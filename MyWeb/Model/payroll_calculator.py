"""
薪资自动核算工具模块
根据考勤、加班、请假等数据自动计算员工薪资
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum
from . import models as md


class PayrollCalculator:
    """薪资计算器"""
    
    # 社保和公积金比例（可以根据实际情况调整）
    SOCIAL_SECURITY_RATE = Decimal('0.10')  # 社保比例 10%
    HOUSING_FUND_RATE = Decimal('0.12')  # 公积金比例 12%
    
    # 个税起征点
    TAX_THRESHOLD = Decimal('5000')  # 5000元
    
    # 个税税率表（适用于月度）
    TAX_RATES = [
        (Decimal('0'), Decimal('3000'), Decimal('0.03')),
        (Decimal('3000'), Decimal('12000'), Decimal('0.10')),
        (Decimal('12000'), Decimal('25000'), Decimal('0.20')),
        (Decimal('25000'), Decimal('35000'), Decimal('0.25')),
        (Decimal('35000'), Decimal('55000'), Decimal('0.30')),
        (Decimal('55000'), Decimal('80000'), Decimal('0.35')),
        (Decimal('80000'), Decimal('999999999'), Decimal('0.45')),
    ]
    
    # 标准工作日（小时）
    STANDARD_WORK_HOURS_PER_DAY = Decimal('8')
    
    def __init__(self, employee, period):
        """
        初始化薪资计算器
        :param employee: User对象
        :param period: 薪资周期，格式：YYYY-MM
        """
        self.employee = employee
        self.period = period
        self.year, self.month = map(int, period.split('-'))
        
        # 计算周期开始和结束日期
        self.period_start = datetime(self.year, self.month, 1).date()
        if self.month == 12:
            self.period_end = datetime(self.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            self.period_end = datetime(self.year, self.month + 1, 1).date() - timedelta(days=1)
    
    def calculate(self):
        """
        计算薪资
        :return: dict 包含所有薪资明细
        """
        try:
            profile = self.employee.profile
        except md.EmployeeProfile.DoesNotExist:
            raise ValueError(f"员工 {self.employee.user_id} 没有员工档案")
        except AttributeError as e:
            raise ValueError(f"员工 {self.employee.user_id} 没有员工档案: {str(e)}")
        
        # 基本工资（使用 getattr 避免字段不存在时的错误）
        try:
            base_salary_value = getattr(profile, 'base_salary', None)
            if base_salary_value is None:
                base_salary_value = Decimal('0')
            base_pay = Decimal(str(base_salary_value)) if base_salary_value else Decimal('0')
        except (AttributeError, TypeError, ValueError) as e:
            # 如果 base_salary 字段不存在，使用默认值 0
            base_pay = Decimal('0')
        
        # 获取考勤数据
        attendance_data = self._get_attendance_data()
        
        # 获取请假数据
        leave_data = self._get_leave_data()
        
        # 获取加班数据
        overtime_data = self._get_overtime_data()
        
        # 计算应出勤天数
        work_days = self._calculate_work_days()
        
        # 计算实际出勤天数（有打卡记录的）
        actual_work_days = attendance_data['work_days']
        
        # 计算基本工资（根据出勤率）
        if work_days > 0:
            attendance_rate = Decimal(str(actual_work_days)) / Decimal(str(work_days))
            base_pay = base_pay * attendance_rate
        else:
            base_pay = Decimal('0')
        
        # 计算请假扣除（事假、病假等）
        leave_deduction = self._calculate_leave_deduction(base_pay, work_days, leave_data)
        
        # 津贴（可以根据考勤情况调整）
        allowance = Decimal('0')
        
        # 加班费（根据已审批的加班申请计算，加到奖金中）
        overtime_pay = self._calculate_overtime_pay(base_pay, overtime_data)
        
        # 奖金（包含加班费，可以后续扩展，根据绩效等计算）
        bonus = overtime_pay
        
        # 其他扣除（迟到、早退等）
        other_deduction = self._calculate_other_deduction(base_pay, attendance_data)
        
        # 应发工资 = 基本工资 + 津贴 + 奖金 - 请假扣除 - 其他扣除
        gross_pay = base_pay + allowance + bonus
        
        # 获取员工的基本工资（用于计算社保和公积金）
        try:
            base_salary_for_social = getattr(profile, 'base_salary', None)
            if base_salary_for_social is None:
                base_salary_for_social = Decimal('0')
            else:
                base_salary_for_social = Decimal(str(base_salary_for_social))
        except (AttributeError, TypeError, ValueError):
            base_salary_for_social = Decimal('0')
        
        # 计算社保（基于基本工资）
        social_security = base_salary_for_social * self.SOCIAL_SECURITY_RATE
        
        # 计算公积金（基于基本工资）
        housing_fund = base_salary_for_social * self.HOUSING_FUND_RATE
        
        # 计算个税（基于应发工资 - 社保 - 公积金 - 起征点）
        taxable_income = gross_pay - social_security - housing_fund - self.TAX_THRESHOLD
        tax = self._calculate_tax(taxable_income) if taxable_income > 0 else Decimal('0')
        
        # 总扣除 = 请假扣除 + 其他扣除 + 社保 + 公积金 + 个税
        total_deduction = leave_deduction + other_deduction + social_security + housing_fund + tax
        
        # 实发工资 = 应发工资 - 总扣除
        net_pay = gross_pay - total_deduction
        
        return {
            'base_pay': round(base_pay, 2),
            'allowance': round(allowance, 2),
            'bonus': round(bonus, 2),  # bonus包含加班费
            'deduction': round(leave_deduction + other_deduction, 2),
            'tax': round(tax, 2),
            'social_security': round(social_security, 2),
            'housing_fund': round(housing_fund, 2),
            'net_pay': round(max(net_pay, Decimal('0')), 2),  # 确保不为负数
            'work_days': work_days,
            'actual_work_days': actual_work_days,
            'overtime_hours': overtime_data['total_hours'],
            'overtime_pay': round(overtime_pay, 2),  # 详细的加班费（用于展示）
            'leave_hours': leave_data['total_hours'],
        }
    
    def _calculate_work_days(self):
        """计算应出勤天数（排除周末）"""
        work_days = 0
        current_date = self.period_start
        while current_date <= self.period_end:
            # 周一到周五为工作日
            if current_date.weekday() < 5:
                work_days += 1
            current_date += timedelta(days=1)
        return work_days
    
    def _get_attendance_data(self):
        """获取考勤数据"""
        records = md.AttendanceRecord.objects.filter(
            employee=self.employee,
            work_date__gte=self.period_start,
            work_date__lte=self.period_end
        )
        
        work_days = records.count()
        total_work_hours = records.aggregate(
            total=Sum('work_hours')
        )['total'] or Decimal('0')
        
        # 统计异常情况
        abnormal_count = records.exclude(abnormal__isnull=True).exclude(abnormal='').count()
        
        return {
            'work_days': work_days,
            'total_work_hours': total_work_hours,
            'abnormal_count': abnormal_count,
            'records': list(records)
        }
    
    def _get_leave_data(self):
        """获取请假数据（仅已审批通过的）"""
        leave_requests = md.LeaveRequest.objects.filter(
            employee=self.employee,
            status='APPROVED',
            start_time__date__lte=self.period_end,
            end_time__date__gte=self.period_start
        )
        
        total_hours = leave_requests.aggregate(
            total=Sum('hours')
        )['total'] or Decimal('0')
        
        # 按请假类型统计
        leave_by_type = {}
        for leave in leave_requests:
            leave_type = leave.type
            if leave_type not in leave_by_type:
                leave_by_type[leave_type] = Decimal('0')
            leave_by_type[leave_type] += leave.hours or Decimal('0')
        
        return {
            'total_hours': total_hours,
            'leave_by_type': leave_by_type,
            'requests': list(leave_requests)
        }
    
    def _get_overtime_data(self):
        """获取加班数据（仅已审批通过的）"""
        overtime_requests = md.OvertimeRequest.objects.filter(
            employee=self.employee,
            status='APPROVED',
            start_time__date__lte=self.period_end,
            end_time__date__gte=self.period_start
        )
        
        total_hours = overtime_requests.aggregate(
            total=Sum('hours')
        )['total'] or Decimal('0')
        
        return {
            'total_hours': total_hours,
            'requests': list(overtime_requests)
        }
    
    def _calculate_leave_deduction(self, base_pay, work_days, leave_data):
        """计算请假扣除"""
        if work_days == 0:
            return Decimal('0')
        
        # 按天计算基本工资
        daily_pay = base_pay / Decimal(str(work_days))
        
        # 事假和病假扣除（可以根据公司政策调整）
        deduction = Decimal('0')
        leave_by_type = leave_data['leave_by_type']
        
        # 事假：全额扣除
        sick_leave_hours = leave_by_type.get('事假', Decimal('0'))
        if sick_leave_hours > 0:
            deduction += (sick_leave_hours / self.STANDARD_WORK_HOURS_PER_DAY) * daily_pay
        
        # 病假：部分扣除（50%）
        personal_leave_hours = leave_by_type.get('病假', Decimal('0'))
        if personal_leave_hours > 0:
            deduction += (personal_leave_hours / self.STANDARD_WORK_HOURS_PER_DAY) * daily_pay * Decimal('0.5')
        
        # 其他类型请假可以根据实际情况调整
        
        return deduction
    
    def _calculate_overtime_pay(self, base_pay, overtime_data):
        """计算加班费"""
        if not base_pay or base_pay == 0:
            return Decimal('0')
        
        total_hours = overtime_data['total_hours']
        if total_hours == 0:
            return Decimal('0')
        
        # 按小时计算基本工资（按每月22天，每天8小时计算）
        hourly_pay = base_pay / (Decimal('22') * self.STANDARD_WORK_HOURS_PER_DAY)
        
        # 平时加班：1.5倍
        # 周末加班：2倍
        # 节假日：3倍
        # 这里简化为统一按1.5倍计算，可以根据实际情况调整
        overtime_rate = Decimal('1.5')
        
        overtime_pay = total_hours * hourly_pay * overtime_rate
        
        return overtime_pay
    
    def _calculate_other_deduction(self, base_pay, attendance_data):
        """计算其他扣除（迟到、早退等）"""
        abnormal_count = attendance_data['abnormal_count']
        if abnormal_count == 0:
            return Decimal('0')
        
        # 每个异常扣除一定金额（可以根据实际情况调整）
        deduction_per_abnormal = Decimal('50')  # 每次异常扣除50元
        
        return Decimal(str(abnormal_count)) * deduction_per_abnormal
    
    def _calculate_tax(self, taxable_income):
        """计算个人所得税"""
        if taxable_income <= 0:
            return Decimal('0')
        
        tax = Decimal('0')
        remaining = taxable_income
        
        for min_income, max_income, rate in self.TAX_RATES:
            if remaining > 0:
                bracket_income = min(remaining, max_income - min_income)
                tax += bracket_income * rate
                remaining -= bracket_income
        
        return tax

