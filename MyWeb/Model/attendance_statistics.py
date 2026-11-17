"""
考勤自动统计工具模块
提供考勤数据的统计、分析和报表生成功能
"""
from decimal import Decimal
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from . import models as md


class AttendanceStatistics:
    """考勤统计工具类"""
    
    # 标准上班时间（可以根据实际情况调整）
    STANDARD_CHECK_IN_TIME = time(9, 0, 0)  # 9:00
    STANDARD_CHECK_OUT_TIME = time(18, 0, 0)  # 18:00
    STANDARD_WORK_HOURS_PER_DAY = Decimal('8')  # 每天标准工作8小时
    
    def __init__(self, employee, period):
        """
        初始化考勤统计器
        :param employee: User对象
        :param period: 统计周期，格式：YYYY-MM
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
    
    def calculate_work_days(self):
        """计算应出勤天数（排除周末）"""
        work_days = 0
        current_date = self.period_start
        while current_date <= self.period_end:
            # 周一到周五为工作日
            if current_date.weekday() < 5:
                work_days += 1
            current_date += timedelta(days=1)
        return work_days
    
    def get_statistics(self):
        """
        获取考勤统计信息
        :return: dict 包含所有统计信息
        """
        # 计算应出勤天数
        work_days = self.calculate_work_days()
        
        # 获取考勤记录
        attendance_records = md.AttendanceRecord.objects.filter(
            employee=self.employee,
            work_date__gte=self.period_start,
            work_date__lte=self.period_end
        ).order_by('work_date')
        
        # 统计实际出勤天数
        actual_work_days = attendance_records.count()
        
        # 统计总工作小时数
        total_work_hours = attendance_records.aggregate(
            total=Sum('work_hours')
        )['total'] or Decimal('0')
        
        # 统计总加班小时数
        total_overtime_hours = attendance_records.aggregate(
            total=Sum('overtime_hours')
        )['total'] or Decimal('0')
        
        # 统计异常情况
        abnormal_records = attendance_records.exclude(
            Q(abnormal__isnull=True) | Q(abnormal='')
        )
        abnormal_count = abnormal_records.count()
        
        # 分析异常类型
        abnormal_analysis = self._analyze_abnormal(abnormal_records)
        
        # 识别迟到、早退
        late_count = 0
        early_leave_count = 0
        absent_count = work_days - actual_work_days  # 缺勤天数 = 应出勤 - 实际出勤
        
        for record in attendance_records:
            if record.check_in:
                check_in_time = record.check_in.time()
                if check_in_time > self.STANDARD_CHECK_IN_TIME:
                    late_count += 1
            
            if record.check_out:
                check_out_time = record.check_out.time()
                if check_out_time < self.STANDARD_CHECK_OUT_TIME:
                    early_leave_count += 1
        
        # 计算平均每日工作小时数
        avg_daily_hours = Decimal('0')
        if actual_work_days > 0:
            avg_daily_hours = total_work_hours / Decimal(str(actual_work_days))
        
        # 计算出勤率
        attendance_rate = Decimal('0')
        if work_days > 0:
            attendance_rate = Decimal(str(actual_work_days)) / Decimal(str(work_days)) * Decimal('100')
        
        return {
            'period': self.period,
            'employee_id': self.employee.user_id,
            'employee_name': self.employee.name,
            'work_days': work_days,  # 应出勤天数
            'actual_work_days': actual_work_days,  # 实际出勤天数
            'absent_days': absent_count,  # 缺勤天数
            'total_work_hours': float(round(total_work_hours, 2)),
            'total_overtime_hours': float(round(total_overtime_hours, 2)),
            'avg_daily_hours': float(round(avg_daily_hours, 2)),
            'attendance_rate': float(round(attendance_rate, 2)),  # 出勤率（百分比）
            'late_count': late_count,  # 迟到次数
            'early_leave_count': early_leave_count,  # 早退次数
            'abnormal_count': abnormal_count,  # 异常次数
            'abnormal_analysis': abnormal_analysis,  # 异常分析详情
            'records': [
                {
                    'work_date': record.work_date.strftime('%Y-%m-%d'),
                    'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else None,
                    'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else None,
                    'work_hours': float(record.work_hours) if record.work_hours else 0,
                    'overtime_hours': float(record.overtime_hours) if record.overtime_hours else 0,
                    'abnormal': record.abnormal,
                }
                for record in attendance_records
            ]
        }
    
    def _analyze_abnormal(self, abnormal_records):
        """
        分析异常记录
        :param abnormal_records: 异常考勤记录的QuerySet
        :return: dict 异常分析结果
        """
        analysis = {
            'total': abnormal_records.count(),
            'by_type': {}
        }
        
        for record in abnormal_records:
            abnormal_type = record.abnormal or '未知'
            if abnormal_type not in analysis['by_type']:
                analysis['by_type'][abnormal_type] = 0
            analysis['by_type'][abnormal_type] += 1
        
        return analysis
    
    def detect_abnormal(self, record):
        """
        自动识别异常考勤（迟到、早退）
        :param record: AttendanceRecord对象
        :return: str 异常类型，如果没有异常返回None
        """
        abnormal_types = []
        
        if record.check_in:
            check_in_time = record.check_in.time()
            if check_in_time > self.STANDARD_CHECK_IN_TIME:
                # 计算迟到分钟数
                late_minutes = (datetime.combine(record.work_date, check_in_time) - 
                               datetime.combine(record.work_date, self.STANDARD_CHECK_IN_TIME)).seconds // 60
                abnormal_types.append(f'迟到{late_minutes}分钟')
        
        if record.check_out:
            check_out_time = record.check_out.time()
            if check_out_time < self.STANDARD_CHECK_OUT_TIME:
                # 计算早退分钟数
                early_minutes = (datetime.combine(record.work_date, self.STANDARD_CHECK_OUT_TIME) - 
                                datetime.combine(record.work_date, check_out_time)).seconds // 60
                abnormal_types.append(f'早退{early_minutes}分钟')
        
        # 检查工作小时数是否不足
        if record.work_hours and record.work_hours < self.STANDARD_WORK_HOURS_PER_DAY:
            shortage = self.STANDARD_WORK_HOURS_PER_DAY - record.work_hours
            abnormal_types.append(f'工时不足{float(shortage):.1f}小时')
        
        if abnormal_types:
            return '; '.join(abnormal_types)
        return None
    
    def auto_update_abnormal(self):
        """
        自动更新考勤记录中的异常字段
        :return: int 更新的记录数
        """
        attendance_records = md.AttendanceRecord.objects.filter(
            employee=self.employee,
            work_date__gte=self.period_start,
            work_date__lte=self.period_end
        )
        
        updated_count = 0
        for record in attendance_records:
            abnormal = self.detect_abnormal(record)
            if record.abnormal != abnormal:
                record.abnormal = abnormal
                record.save(update_fields=['abnormal'])
                updated_count += 1
        
        return updated_count


def get_department_statistics(department, period):
    """
    获取部门的考勤统计
    :param department: Department对象
    :param period: 统计周期，格式：YYYY-MM
    :return: dict 部门统计信息
    """
    year, month = map(int, period.split('-'))
    period_start = datetime(year, month, 1).date()
    if month == 12:
        period_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        period_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # 获取部门所有员工
    employees = md.EmployeeProfile.objects.filter(department=department)
    
    department_stats = {
        'department_id': department.id,
        'department_name': department.name,
        'period': period,
        'total_employees': employees.count(),
        'employee_statistics': []
    }
    
    for emp_profile in employees:
        employee = emp_profile.user
        stats = AttendanceStatistics(employee, period)
        emp_stats = stats.get_statistics()
        department_stats['employee_statistics'].append(emp_stats)
    
    # 计算部门总体统计
    total_work_days = sum(s['work_days'] for s in department_stats['employee_statistics'])
    total_actual_work_days = sum(s['actual_work_days'] for s in department_stats['employee_statistics'])
    total_absent_days = sum(s['absent_days'] for s in department_stats['employee_statistics'])
    total_late_count = sum(s['late_count'] for s in department_stats['employee_statistics'])
    total_early_leave_count = sum(s['early_leave_count'] for s in department_stats['employee_statistics'])
    total_abnormal_count = sum(s['abnormal_count'] for s in department_stats['employee_statistics'])
    
    department_stats['summary'] = {
        'total_work_days': total_work_days,
        'total_actual_work_days': total_actual_work_days,
        'total_absent_days': total_absent_days,
        'total_late_count': total_late_count,
        'total_early_leave_count': total_early_leave_count,
        'total_abnormal_count': total_abnormal_count,
        'avg_attendance_rate': sum(s['attendance_rate'] for s in department_stats['employee_statistics']) / len(department_stats['employee_statistics']) if department_stats['employee_statistics'] else 0
    }
    
    return department_stats

