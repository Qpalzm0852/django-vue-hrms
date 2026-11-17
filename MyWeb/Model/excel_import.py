"""
Excel数据导入工具模块
支持批量导入员工信息、考勤记录等数据
"""
import pandas as pd
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from . import models as md
from . import log_utils


class ExcelImportError(Exception):
    """Excel导入异常"""
    pass


class EmployeeExcelImporter:
    """员工信息Excel导入器"""
    
    REQUIRED_COLUMNS = ['工号', '姓名', '部门', '密码']  # 必填列
    OPTIONAL_COLUMNS = ['岗位', '入职日期', '状态', '基本工资', '手机', '邮箱', '身份证号', '学历', '合同到期日', '角色']  # 可选列
    
    def __init__(self, file_path, request=None):
        """
        初始化导入器
        :param file_path: Excel文件路径
        :param request: HTTP请求对象（用于记录日志）
        """
        self.file_path = file_path
        self.request = request
        self.errors = []
        self.success_count = 0
        self.fail_count = 0
    
    def validate_file(self, df):
        """验证文件格式"""
        # 检查必填列
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            raise ExcelImportError(f"缺少必填列: {', '.join(missing_columns)}")
        
        if len(df) == 0:
            raise ExcelImportError("Excel文件中没有数据")
        
        return True
    
    def import_data(self):
        """
        导入数据
        :return: dict 导入结果
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(self.file_path)
            
            # 验证文件格式
            self.validate_file(df)
            
            # 开始事务
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        self._import_single_record(row, index + 2)  # index+2是因为Excel行号从1开始，且有表头
                        self.success_count += 1
                    except Exception as e:
                        self.fail_count += 1
                        self.errors.append({
                            'row': index + 2,
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'success_count': self.success_count,
                'fail_count': self.fail_count,
                'errors': self.errors,
                'total': len(df)
            }
        except Exception as e:
            raise ExcelImportError(f"导入失败: {str(e)}")
    
    def _import_single_record(self, row, row_num):
        """导入单条记录"""
        user_id = str(row['工号']).strip()
        name = str(row['姓名']).strip()
        department_name = str(row['部门']).strip()
        password = str(row['密码']).strip() if pd.notna(row['密码']) else ''
        
        # 验证必填字段
        if not user_id or user_id == 'nan':
            raise ValueError(f"第{row_num}行: 工号不能为空")
        if not name or name == 'nan':
            raise ValueError(f"第{row_num}行: 姓名不能为空")
        if not department_name or department_name == 'nan':
            raise ValueError(f"第{row_num}行: 部门不能为空")
        
        # 获取或创建部门
        try:
            department = md.Department.objects.get(name=department_name)
        except md.Department.DoesNotExist:
            raise ValueError(f"第{row_num}行: 部门 '{department_name}' 不存在")
        
        # 获取岗位（如果提供）
        position = None
        if '岗位' in row and pd.notna(row['岗位']):
            position_name = str(row['岗位']).strip()
            try:
                position = md.JobPosition.objects.filter(name=position_name, department=department).first()
            except md.JobPosition.DoesNotExist:
                pass  # 岗位不存在，设置为None
        
        # 获取角色（默认为STAFF）
        role = 'STAFF'
        if '角色' in row and pd.notna(row['角色']):
            role_value = str(row['角色']).strip().upper()
            if role_value in ['ADMIN', 'HR', 'MANAGER', 'STAFF']:
                role = role_value
        
        # 创建或更新用户
        user, user_created = md.User.objects.get_or_create(
            user_id=user_id,
            defaults={
                'name': name,
                'role': role,
            }
        )
        if not user_created:
            # 如果用户已存在，更新信息
            user.name = name
            user.role = role
            user.save()
        
        # 设置密码
        if password and password != 'nan':
            user.set_password(password)
            user.save(update_fields=['password'])
        elif user_created:
            user.set_unusable_password()
            user.save(update_fields=['password'])
        
        # 解析日期字段
        hire_date = None
        if '入职日期' in row and pd.notna(row['入职日期']):
            try:
                if isinstance(row['入职日期'], str):
                    hire_date = datetime.strptime(row['入职日期'], '%Y-%m-%d').date()
                else:
                    hire_date = row['入职日期'].date() if hasattr(row['入职日期'], 'date') else row['入职日期']
            except (ValueError, AttributeError):
                pass
        
        contract_end = None
        if '合同到期日' in row and pd.notna(row['合同到期日']):
            try:
                if isinstance(row['合同到期日'], str):
                    contract_end = datetime.strptime(row['合同到期日'], '%Y-%m-%d').date()
                else:
                    contract_end = row['合同到期日'].date() if hasattr(row['合同到期日'], 'date') else row['合同到期日']
            except (ValueError, AttributeError):
                pass
        
        # 解析状态
        status = 'ONBOARD'
        if '状态' in row and pd.notna(row['状态']):
            status_value = str(row['状态']).strip()
            status_map = {'在职': 'ONBOARD', '试用': 'PROBATION', '离职': 'LEAVE', '停薪留职': 'SUSPEND'}
            status = status_map.get(status_value, 'ONBOARD')
        
        # 解析基本工资
        base_salary = Decimal('0')
        if '基本工资' in row and pd.notna(row['基本工资']):
            try:
                base_salary = Decimal(str(row['基本工资']))
            except (ValueError, TypeError):
                pass
        
        # 创建或更新员工档案
        profile, profile_created = md.EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'department': department,
                'position': position,
                'hire_date': hire_date,
                'status': status,
                'base_salary': base_salary,
                'phone': str(row['手机']).strip() if '手机' in row and pd.notna(row['手机']) else None,
                'email': str(row['邮箱']).strip() if '邮箱' in row and pd.notna(row['邮箱']) else None,
                'id_no': str(row['身份证号']).strip() if '身份证号' in row and pd.notna(row['身份证号']) else None,
                'education': str(row['学历']).strip() if '学历' in row and pd.notna(row['学历']) else None,
                'contract_end': contract_end,
            }
        )
        
        if not profile_created:
            # 如果档案已存在，更新信息
            profile.department = department
            profile.position = position
            if hire_date:
                profile.hire_date = hire_date
            profile.status = status
            profile.base_salary = base_salary
            if '手机' in row and pd.notna(row['手机']):
                profile.phone = str(row['手机']).strip()
            if '邮箱' in row and pd.notna(row['邮箱']):
                profile.email = str(row['邮箱']).strip()
            if '身份证号' in row and pd.notna(row['身份证号']):
                profile.id_no = str(row['身份证号']).strip()
            if '学历' in row and pd.notna(row['学历']):
                profile.education = str(row['学历']).strip()
            if contract_end:
                profile.contract_end = contract_end
            profile.save()
        
        # 记录操作日志
        if self.request and profile_created:
            log_utils.log_create(
                self.request,
                "员工管理",
                "EmployeeProfile",
                user_id,
                f"通过Excel导入创建员工档案: {name}({user_id})"
            )
        elif self.request:
            log_utils.log_update(
                self.request,
                "员工管理",
                "EmployeeProfile",
                user_id,
                f"通过Excel导入更新员工档案: {name}({user_id})"
            )


class AttendanceExcelImporter:
    """考勤记录Excel导入器"""
    
    REQUIRED_COLUMNS = ['工号', '日期']
    OPTIONAL_COLUMNS = ['上班打卡', '下班打卡', '工时', '加班时长', '异常说明']
    
    def __init__(self, file_path, request=None):
        self.file_path = file_path
        self.request = request
        self.errors = []
        self.success_count = 0
        self.fail_count = 0
    
    def validate_file(self, df):
        """验证文件格式"""
        missing_columns = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            raise ExcelImportError(f"缺少必填列: {', '.join(missing_columns)}")
        
        if len(df) == 0:
            raise ExcelImportError("Excel文件中没有数据")
        
        return True
    
    def import_data(self):
        """导入数据"""
        try:
            df = pd.read_excel(self.file_path)
            self.validate_file(df)
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        self._import_single_record(row, index + 2)
                        self.success_count += 1
                    except Exception as e:
                        self.fail_count += 1
                        self.errors.append({
                            'row': index + 2,
                            'error': str(e)
                        })
            
            return {
                'success': True,
                'success_count': self.success_count,
                'fail_count': self.fail_count,
                'errors': self.errors,
                'total': len(df)
            }
        except Exception as e:
            raise ExcelImportError(f"导入失败: {str(e)}")
    
    def _import_single_record(self, row, row_num):
        """导入单条记录"""
        user_id = str(row['工号']).strip()
        work_date_str = str(row['日期']).strip()
        
        # 验证必填字段
        if not user_id or user_id == 'nan':
            raise ValueError(f"第{row_num}行: 工号不能为空")
        if not work_date_str or work_date_str == 'nan':
            raise ValueError(f"第{row_num}行: 日期不能为空")
        
        # 获取员工
        try:
            employee = md.User.objects.get(user_id=user_id)
        except md.User.DoesNotExist:
            raise ValueError(f"第{row_num}行: 员工 '{user_id}' 不存在")
        
        # 解析日期
        try:
            if isinstance(row['日期'], str):
                work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
            else:
                work_date = row['日期'].date() if hasattr(row['日期'], 'date') else row['日期']
        except (ValueError, AttributeError):
            raise ValueError(f"第{row_num}行: 日期格式错误，应为 YYYY-MM-DD")
        
        # 解析时间字段
        check_in = None
        if '上班打卡' in row and pd.notna(row['上班打卡']):
            try:
                if isinstance(row['上班打卡'], str):
                    check_in = datetime.strptime(row['上班打卡'], '%Y-%m-%d %H:%M:%S')
                else:
                    check_in = row['上班打卡'] if isinstance(row['上班打卡'], datetime) else datetime.combine(work_date, row['上班打卡'].time())
            except (ValueError, AttributeError, TypeError):
                pass
        
        check_out = None
        if '下班打卡' in row and pd.notna(row['下班打卡']):
            try:
                if isinstance(row['下班打卡'], str):
                    check_out = datetime.strptime(row['下班打卡'], '%Y-%m-%d %H:%M:%S')
                else:
                    check_out = row['下班打卡'] if isinstance(row['下班打卡'], datetime) else datetime.combine(work_date, row['下班打卡'].time())
            except (ValueError, AttributeError, TypeError):
                pass
        
        # 解析工时和加班时长
        work_hours = None
        if '工时' in row and pd.notna(row['工时']):
            try:
                work_hours = Decimal(str(row['工时']))
            except (ValueError, TypeError):
                pass
        
        overtime_hours = None
        if '加班时长' in row and pd.notna(row['加班时长']):
            try:
                overtime_hours = Decimal(str(row['加班时长']))
            except (ValueError, TypeError):
                pass
        
        # 异常说明
        abnormal = None
        if '异常说明' in row and pd.notna(row['异常说明']):
            abnormal = str(row['异常说明']).strip()
        
        # 创建或更新考勤记录
        record, created = md.AttendanceRecord.objects.update_or_create(
            employee=employee,
            work_date=work_date,
            defaults={
                'check_in': check_in,
                'check_out': check_out,
                'work_hours': work_hours,
                'overtime_hours': overtime_hours,
                'abnormal': abnormal,
            }
        )
        
        # 记录操作日志
        if self.request and created:
            log_utils.log_create(
                self.request,
                "考勤管理",
                "AttendanceRecord",
                str(record.id),
                f"通过Excel导入创建考勤记录: {employee.name}({user_id}) - {work_date}"
            )
        elif self.request:
            log_utils.log_update(
                self.request,
                "考勤管理",
                "AttendanceRecord",
                str(record.id),
                f"通过Excel导入更新考勤记录: {employee.name}({user_id}) - {work_date}"
            )

