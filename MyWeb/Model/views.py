from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta, datetime, date
from . import models as md
from . import serializers
from . import log_utils
from Model.log_mixin import LoggingMixin
from Model.utils import (
    validate_period_format, validate_required_params,
    success_response, error_response, exception_response, require_roles
)
from Model.viewset_mixins import ApprovalMixin


def _get_user_role(user):
    return (getattr(user, 'role', '') or '').upper()


def _get_user_department(user):
    try:
        return user.profile.department
    except Exception:
        return None


def _scope_by_employee_role(queryset, user, employee_field='employee'):
    role = _get_user_role(user)
    if role in {'ADMIN', 'HR'}:
        return queryset
    if role == 'MANAGER':
        department = _get_user_department(user)
        if not department:
            return queryset.none()
        return queryset.filter(**{f'{employee_field}__profile__department': department})
    return queryset.filter(**{employee_field: user})


class IsAdminOrHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return _get_user_role(request.user) in {'ADMIN', 'HR'}


class IsAdminHRManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return _get_user_role(request.user) in {'ADMIN', 'HR', 'MANAGER'}


# ============ 企业人力资源管理系统视图 ============


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    部门管理视图集
    """
    queryset = md.Department.objects.all().order_by('id')
    serializer_class = serializers.DepartmentSerializer
    permission_classes = [IsAdminOrHR]


class JobPositionViewSet(viewsets.ModelViewSet):
    """
    岗位管理视图集
    """
    queryset = md.JobPosition.objects.select_related('department').all().order_by('id')
    serializer_class = serializers.JobPositionSerializer
    permission_classes = [IsAdminOrHR]


class EmployeeProfileViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    员工档案管理视图集
    """
    serializer_class = serializers.EmployeeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "员工管理"
    resource_type = "EmployeeProfile"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrHR()]

    def get_queryset(self):
        queryset = md.EmployeeProfile.objects.select_related(
            'user', 'department', 'position'
        ).all().order_by('user_id')

        role = _get_user_role(self.request.user)
        if role == 'MANAGER':
            department = _get_user_department(self.request.user)
            queryset = queryset.filter(department=department) if department else queryset.none()
        elif role not in {'ADMIN', 'HR'}:
            queryset = queryset.filter(user=self.request.user)

        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter(user__user_id__icontains=employee_id)

        return queryset
class AttendanceRecordViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    考勤记录视图集
    """
    serializer_class = serializers.AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "考勤管理"
    resource_type = "AttendanceRecord"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminHRManager()]

    def get_queryset(self):
        queryset = md.AttendanceRecord.objects.select_related('employee').all().order_by('-work_date')
        queryset = _scope_by_employee_role(queryset, self.request.user, employee_field='employee')

        # 查询参数过滤
        employee_id = self.request.query_params.get('employee_id', None)
        work_date = self.request.query_params.get('work_date', None)

        if employee_id:
            queryset = queryset.filter(employee__user_id__icontains=employee_id)
        if work_date:
            queryset = queryset.filter(work_date=work_date)

        return queryset

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        获取考勤统计信息
        查询参数：
        - employee_id: 员工工号（必填）
        - period: 统计周期，格式：YYYY-MM（必填）
        """
        from .attendance_statistics import AttendanceStatistics

        # 验证必需参数
        is_valid, error_msg, _ = validate_required_params(
            request.query_params,
            ['employee_id', 'period'],
            {'employee_id': '员工工号', 'period': '统计周期'}
        )
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        employee_id = request.query_params.get('employee_id')
        period = request.query_params.get('period')

        # 验证周期格式
        is_valid, error_msg, (year, month) = validate_period_format(period)
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        # 获取员工对象
        try:
            employee = md.User.objects.get(user_id=employee_id)
        except md.User.DoesNotExist:
            return error_response(f'员工 {employee_id} 不存在', status.HTTP_404_NOT_FOUND)

        # 获取统计数据
        try:
            stats = AttendanceStatistics(employee, period)
            statistics_data = stats.get_statistics()
            return success_response(data=statistics_data)
        except Exception as e:
            return exception_response(e, '获取考勤统计时发生错误', status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='auto-detect-abnormal')
    def auto_detect_abnormal(self, request):
        """
        自动识别并更新异常考勤
        请求参数：
        {
            "employee_id": "emp001",
            "period": "2024-01"
        }
        """
        from .attendance_statistics import AttendanceStatistics

        # 验证必需参数
        is_valid, error_msg, _ = validate_required_params(
            request.data,
            ['employee_id', 'period'],
            {'employee_id': '员工工号', 'period': '统计周期'}
        )
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        employee_id = request.data.get('employee_id')
        period = request.data.get('period')

        # 验证周期格式
        is_valid, error_msg, (year, month) = validate_period_format(period)
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        # 获取员工对象
        try:
            employee = md.User.objects.get(user_id=employee_id)
        except md.User.DoesNotExist:
            return error_response(f'员工 {employee_id} 不存在', status.HTTP_404_NOT_FOUND)

        # 自动识别异常考勤
        try:
            stats = AttendanceStatistics(employee, period)
            updated_count = stats.auto_update_abnormal()
            return success_response(
                data={'updated_count': updated_count},
                message=f'成功更新 {updated_count} 条异常考勤记录'
            )
        except Exception as e:
            return exception_response(e, '自动识别异常考勤时发生错误', status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='department-statistics')
    def department_statistics(self, request):
        """
        获取部门考勤统计
        查询参数：
        - department_id: 部门ID（必填）
        - period: 统计周期，格式：YYYY-MM（必填）
        """
        from .attendance_statistics import get_department_statistics

        # 验证必需参数
        is_valid, error_msg, _ = validate_required_params(
            request.query_params,
            ['department_id', 'period'],
            {'department_id': '部门ID', 'period': '统计周期'}
        )
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        department_id = request.query_params.get('department_id')
        period = request.query_params.get('period')

        # 验证周期格式
        is_valid, error_msg, (year, month) = validate_period_format(period)
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        # 获取部门对象
        try:
            department = md.Department.objects.get(id=department_id)
        except md.Department.DoesNotExist:
            return error_response(f'部门 {department_id} 不存在', status.HTTP_404_NOT_FOUND)

        # 获取部门统计数据
        try:
            statistics_data = get_department_statistics(department, period)
            return success_response(data=statistics_data)
        except Exception as e:
            return exception_response(e, '获取部门考勤统计时发生错误', status.HTTP_500_INTERNAL_SERVER_ERROR)
class LeaveRequestViewSet(LoggingMixin, ApprovalMixin, viewsets.ModelViewSet):
    """
    请假申请视图集
    """
    serializer_class = serializers.LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "请假审批"
    resource_type = "LeaveRequest"

    def get_queryset(self):
        queryset = md.LeaveRequest.objects.select_related('employee', 'approver').all().order_by('-created_at')
        queryset = _scope_by_employee_role(queryset, self.request.user, employee_field='employee')

        # 查询参数过滤
        employee_id = self.request.query_params.get('employee_id', None)
        status = self.request.query_params.get('status', None)

        if employee_id:
            queryset = queryset.filter(employee__user_id__icontains=employee_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        if _get_user_role(self.request.user) == 'STAFF':
            serializer.save(employee=self.request.user, approver=None, status='PENDING')
        else:
            serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if _get_user_role(self.request.user) == 'STAFF':
            if instance.status != 'PENDING':
                raise PermissionDenied('仅待审批状态可修改')
            serializer.save(employee=self.request.user, approver=None, status='PENDING')
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批请假申请 - 仅ADMIN、HR、MANAGER可以审批"""
        leave_request = self.get_object()
        return self.approve_request(
            request,
            leave_request,
            log_func=log_utils.log_approve,
            log_module="请假审批",
            log_resource_type="LeaveRequest"
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝请假申请 - 仅ADMIN、HR、MANAGER可以审批"""
        leave_request = self.get_object()
        return self.reject_request(
            request,
            leave_request,
            log_func=log_utils.log_reject,
            log_module="请假审批",
            log_resource_type="LeaveRequest"
        )
class PayrollViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    薪酬管理视图集
    """
    serializer_class = serializers.PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "薪酬管理"
    resource_type = "Payroll"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrHR()]

    def get_queryset(self):
        queryset = md.Payroll.objects.select_related('employee').all().order_by('-period', 'employee_id')
        queryset = _scope_by_employee_role(queryset, self.request.user, employee_field='employee')

        # 查询参数过滤
        employee_id = self.request.query_params.get('employee_id', None)
        period = self.request.query_params.get('period', None)

        if employee_id:
            queryset = queryset.filter(employee__user_id__icontains=employee_id)
        if period:
            queryset = queryset.filter(period__icontains=period)

        return queryset

    @action(detail=False, methods=['post'], url_path='calculate')
    def calculate_payroll(self, request):
        """
        自动计算薪资
        请求参数：
        {
            "employee_id": "emp001",
            "period": "2024-01"
        }
        """
        from .payroll_calculator import PayrollCalculator

        # 验证必需参数
        is_valid, error_msg, _ = validate_required_params(
            request.data,
            ['employee_id', 'period'],
            {'employee_id': '员工工号', 'period': '薪资周期'}
        )
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        employee_id = request.data.get('employee_id')
        period = request.data.get('period')

        # 验证周期格式
        is_valid, error_msg, (year, month) = validate_period_format(period)
        if not is_valid:
            return error_response(error_msg, status.HTTP_400_BAD_REQUEST)

        # 获取员工对象
        try:
            employee = md.User.objects.get(user_id=employee_id)
        except md.User.DoesNotExist:
            return error_response(f'员工 {employee_id} 不存在', status.HTTP_404_NOT_FOUND)

        # 计算薪资
        try:
            calculator = PayrollCalculator(employee, period)
            result = calculator.calculate()
            return success_response(data=result)
        except ValueError as e:
            return error_response(str(e), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return exception_response(e, '计算薪资时发生错误', status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='auto-generate')
    def auto_generate_payroll(self, request):
        """
        自动生成薪资记录
        请求参数：
        {
            "employee_id": "emp001",
            "period": "2024-01",
            "bonus": 0,  # 可选，手动添加的奖金
            "other_deduction": 0  # 可选，其他扣除项
        }
        """
        from .payroll_calculator import PayrollCalculator
        from decimal import Decimal

        employee_id = request.data.get('employee_id')
        period = request.data.get('period')
        bonus = Decimal(str(request.data.get('bonus', 0)))
        other_deduction = Decimal(str(request.data.get('other_deduction', 0)))

        if not employee_id or not period:
            return Response(
                {'error': '员工工号和薪资周期不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employee = md.User.objects.get(user_id=employee_id)
        except md.User.DoesNotExist:
            return Response(
                {'error': f'员工 {employee_id} 不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            calculator = PayrollCalculator(employee, period)
            calculated = calculator.calculate()

            # 合并手动输入的奖金和其他扣除
            calculated['bonus'] = calculated.get('bonus', Decimal('0')) + bonus
            calculated['deduction'] = calculated.get('deduction', Decimal('0')) + other_deduction

            # 重新计算实发工资
            income = calculated['base_pay'] + calculated['allowance'] + calculated['bonus']
            deduction_total = calculated['deduction'] + calculated['tax'] + calculated['social_security'] + calculated['housing_fund']
            calculated['net_pay'] = max(income - deduction_total, Decimal('0'))

            # 创建或更新薪资记录（确保所有值都是 Decimal 或 float）
            payroll, created = md.Payroll.objects.update_or_create(
                employee=employee,
                period=period,
                defaults={
                    'base_pay': float(calculated['base_pay']),
                    'allowance': float(calculated['allowance']),
                    'bonus': float(calculated['bonus']),
                    'deduction': float(calculated['deduction']),
                    'tax': float(calculated['tax']),
                    'social_security': float(calculated['social_security']),
                    'housing_fund': float(calculated['housing_fund']),
                    'net_pay': float(calculated['net_pay']),
                    'status': 'DRAFT',
                }
            )

            serializer = self.get_serializer(payroll)
            # 将 Decimal 类型转换为 float，确保可以序列化
            calculation_details = {}
            for k, v in calculated.items():
                if isinstance(v, Decimal):
                    calculation_details[k] = float(v)
                else:
                    calculation_details[k] = v

            return Response({
                'success': True,
                'created': created,
                'data': serializer.data,
                'calculation_details': calculation_details
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"生成薪资记录时发生错误: {error_detail}")  # 打印到控制台，方便调试
            return Response(
                {
                    'error': f'生成薪资记录时发生错误: {str(e)}',
                    'detail': str(error_detail)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class PerformanceRecordViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    绩效记录视图集
    """
    serializer_class = serializers.PerformanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "绩效管理"
    resource_type = "PerformanceRecord"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminHRManager()]

    def get_queryset(self):
        queryset = md.PerformanceRecord.objects.select_related('employee', 'evaluator').all().order_by('-period', 'employee_id')
        queryset = _scope_by_employee_role(queryset, self.request.user, employee_field='employee')

        # 查询参数过滤
        employee_id = self.request.query_params.get('employee_id', None)
        period = self.request.query_params.get('period', None)

        if employee_id:
            queryset = queryset.filter(employee__user_id__icontains=employee_id)
        if period:
            queryset = queryset.filter(period__icontains=period)

        return queryset
class TrainingViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    Training management viewset
    """
    serializer_class = serializers.TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "Training Management"
    resource_type = "Training"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminHRManager()]

    def get_queryset(self):
        queryset = md.Training.objects.all().order_by('-created_at')
        role = _get_user_role(self.request.user)
        if role == 'STAFF':
            department_name = getattr(_get_user_department(self.request.user), 'name', '')
            queryset = queryset.filter(
                Q(participants_scope__isnull=True) |
                Q(participants_scope='') |
                Q(participants_scope__icontains=self.request.user.user_id) |
                Q(participants_scope__icontains=department_name)
            )

        title = self.request.query_params.get('title', None)

        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

class AnnouncementViewSet(LoggingMixin, viewsets.ModelViewSet):
    """
    Announcement management viewset
    """
    serializer_class = serializers.AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "Announcement Management"
    resource_type = "Announcement"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminHRManager()]

    def get_queryset(self):
        queryset = md.Announcement.objects.select_related('publisher').all().order_by('-publish_time')
        title = self.request.query_params.get('title', None)
        level = self.request.query_params.get('level', None)

        if title:
            queryset = queryset.filter(title__icontains=title)
        if level:
            queryset = queryset.filter(level=level)

        return queryset

class OvertimeRequestViewSet(LoggingMixin, ApprovalMixin, viewsets.ModelViewSet):
    """
    加班申请视图集
    """
    serializer_class = serializers.OvertimeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    module_name = "加班管理"
    resource_type = "OvertimeRequest"

    def get_queryset(self):
        queryset = md.OvertimeRequest.objects.select_related('employee', 'approver').all().order_by('-created_at')
        queryset = _scope_by_employee_role(queryset, self.request.user, employee_field='employee')

        # 查询参数过滤
        employee_id = self.request.query_params.get('employee_id', None)
        status = self.request.query_params.get('status', None)

        if employee_id:
            queryset = queryset.filter(employee__user_id__icontains=employee_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        if _get_user_role(self.request.user) == 'STAFF':
            serializer.save(employee=self.request.user, approver=None, status='PENDING')
        else:
            serializer.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if _get_user_role(self.request.user) == 'STAFF':
            if instance.status != 'PENDING':
                raise PermissionDenied('仅待审批状态可修改')
            serializer.save(employee=self.request.user, approver=None, status='PENDING')
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批加班申请 - 仅ADMIN、HR、MANAGER可以审批"""
        overtime_request = self.get_object()
        return self.approve_request(
            request,
            overtime_request,
            log_func=log_utils.log_approve,
            log_module="加班管理",
            log_resource_type="OvertimeRequest"
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝加班申请 - 仅ADMIN、HR、MANAGER可以审批"""
        overtime_request = self.get_object()
        return self.reject_request(
            request,
            overtime_request,
            log_func=log_utils.log_reject,
            log_module="加班管理",
            log_resource_type="OvertimeRequest"
        )
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_employees(request):
    """
    批量导入员工信息
    请求：multipart/form-data
    - file: Excel文件
    """
    from .excel_import import EmployeeExcelImporter, ExcelImportError
    import tempfile
    import os

    has_permission, error_msg = require_roles(request.user, ['ADMIN', 'HR'])
    if not has_permission:
        return error_response(error_msg, status.HTTP_403_FORBIDDEN)

    if 'file' not in request.FILES:
        return Response(
            {'error': '请上传Excel文件'},
            status=status.HTTP_400_BAD_REQUEST
        )

    uploaded_file = request.FILES['file']

    # 检查文件扩展名
    if not uploaded_file.name.endswith(('.xlsx', '.xls')):
        return Response(
            {'error': '文件格式错误，请上传Excel文件（.xlsx或.xls）'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    try:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()

        # 导入数据
        importer = EmployeeExcelImporter(temp_file.name, request)
        result = importer.import_data()

        return Response({
            'success': True,
            'message': f'导入完成：成功 {result["success_count"]} 条，失败 {result["fail_count"]} 条',
            **result
        })
    except ExcelImportError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"导入员工信息时发生错误: {error_detail}")
        return Response(
            {
                'error': f'导入失败: {str(e)}',
                'detail': str(error_detail) if settings.DEBUG else None
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # 删除临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_attendance(request):
    """
    批量导入考勤记录
    请求：multipart/form-data
    - file: Excel文件
    """
    from .excel_import import AttendanceExcelImporter, ExcelImportError
    import tempfile
    import os

    has_permission, error_msg = require_roles(request.user, ['ADMIN', 'HR'])
    if not has_permission:
        return error_response(error_msg, status.HTTP_403_FORBIDDEN)

    if 'file' not in request.FILES:
        return error_response('请上传Excel文件', status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']

    # 检查文件扩展名
    if not uploaded_file.name.endswith(('.xlsx', '.xls')):
        return error_response('文件格式错误，请上传Excel文件（.xlsx或.xls）', status.HTTP_400_BAD_REQUEST)

    # 保存临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    try:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.close()

        # 导入数据
        importer = AttendanceExcelImporter(temp_file.name, request)
        result = importer.import_data()

        return success_response(
            data=result,
            message=f'导入完成：成功 {result["success_count"]} 条，失败 {result["fail_count"]} 条'
        )
    except ExcelImportError as e:
        return error_response(str(e), status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return exception_response(e, '导入考勤记录时发生错误', status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # 删除临时文件
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def overview_statistics(request):
    """
    首页概览统计API
    返回员工总数、待审批事项等关键统计数据
    """
    try:
        has_permission, error_msg = require_roles(request.user, ['ADMIN', 'HR', 'MANAGER'])
        if not has_permission:
            return error_response(error_msg, status.HTTP_403_FORBIDDEN)

        from django.utils import timezone
        from datetime import date
        
        today = timezone.now().date()
        
        # 员工总数
        total_employees = md.EmployeeProfile.objects.count()
        
        # 今日考勤人数
        today_attendance = md.AttendanceRecord.objects.filter(work_date=today).count()
        
        # 待审批请假申请
        pending_leave = md.LeaveRequest.objects.filter(status='PENDING').count()
        
        # 待审批加班申请
        pending_overtime = md.OvertimeRequest.objects.filter(status='PENDING').count()
        
        # 本月新入职员工数
        first_day_of_month = date(today.year, today.month, 1)
        new_employees = md.EmployeeProfile.objects.filter(
            hire_date__gte=first_day_of_month
        ).count()
        
        # 部门总数
        total_departments = md.Department.objects.count()
        
        # 本月考勤异常数
        this_month_start = first_day_of_month
        abnormal_attendance = md.AttendanceRecord.objects.filter(
            work_date__gte=this_month_start,
            work_date__lte=today
        ).exclude(
            Q(abnormal__isnull=True) | Q(abnormal='')
        ).count()
        
        # 待发布招聘需求
        draft_recruitment = md.RecruitmentRequirement.objects.filter(status='DRAFT').count()
        
        return Response({
            'total_employees': total_employees,
            'today_attendance': today_attendance,
            'pending_leave': pending_leave,
            'pending_overtime': pending_overtime,
            'new_employees': new_employees,
            'total_departments': total_departments,
            'abnormal_attendance': abnormal_attendance,
            'draft_recruitment': draft_recruitment,
            'pending_total': pending_leave + pending_overtime,
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"首页统计API错误: {str(e)}")
        print(error_detail)
        return Response({
            'error': f'服务器错误: {str(e)}',
            'detail': error_detail
        }, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employee_overview_statistics(request):
    """
    员工端首页概览统计API
    返回当前员工的个人统计数据
    """
    try:
        from django.utils import timezone
        from datetime import date

        today = timezone.now().date()
        user = request.user

        # 获取员工档案
        try:
            profile = user.profile
        except md.EmployeeProfile.DoesNotExist:
            return Response({'error': '未找到员工信息'}, status=404)

        # 本月第一天
        first_day_of_month = date(today.year, today.month, 1)

        attendance_queryset = md.AttendanceRecord.objects.filter(
            employee=user,
            work_date__gte=first_day_of_month,
            work_date__lte=today
        )

        # 本月考勤天数
        month_attendance_days = attendance_queryset.count()

        # 本月出勤天数（存在任一打卡即视为出勤）
        month_work_days = attendance_queryset.exclude(
            Q(check_in__isnull=True) & Q(check_out__isnull=True)
        ).count()

        # 本月请假次数
        month_leave_count = md.LeaveRequest.objects.filter(
            employee=user,
            start_time__date__gte=first_day_of_month,
            start_time__date__lte=today
        ).count()

        # 本月加班次数
        month_overtime_count = md.OvertimeRequest.objects.filter(
            employee=user,
            start_time__date__gte=first_day_of_month,
            start_time__date__lte=today
        ).count()

        # 待审批请假/加班
        pending_leave = md.LeaveRequest.objects.filter(employee=user, status='PENDING').count()
        pending_overtime = md.OvertimeRequest.objects.filter(employee=user, status='PENDING').count()

        # 本月考勤异常数
        month_abnormal_count = attendance_queryset.exclude(
            Q(abnormal__isnull=True) | Q(abnormal='')
        ).count()

        # 最近一次工资条周期
        latest_payroll = md.Payroll.objects.filter(employee=user).order_by('-period').first()
        latest_payroll_date = latest_payroll.period if latest_payroll else None

        # 本月绩效记录数（按周期字段统计）
        current_period = today.strftime('%Y-%m')
        month_performance_count = md.PerformanceRecord.objects.filter(
            employee=user,
            period=current_period
        ).count()

        # 本月培训次数（无员工关联字段，按可见培训统计）
        month_training_count = md.Training.objects.filter(
            start_time__date__gte=first_day_of_month,
            start_time__date__lte=today
        ).filter(
            Q(participants_scope__isnull=True) |
            Q(participants_scope='') |
            Q(participants_scope__icontains=user.user_id) |
            Q(participants_scope__icontains=getattr(profile.department, 'name', ''))
        ).count()

        return Response({
            'month_attendance_days': month_attendance_days,
            'month_work_days': month_work_days,
            'month_leave_count': month_leave_count,
            'month_overtime_count': month_overtime_count,
            'pending_leave': pending_leave,
            'pending_overtime': pending_overtime,
            'month_abnormal_count': month_abnormal_count,
            'latest_payroll_date': latest_payroll_date,
            'month_performance_count': month_performance_count,
            'month_training_count': month_training_count,
            'pending_total': pending_leave + pending_overtime,
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"员工端统计API错误: {str(e)}")
        print(error_detail)
        return Response({
            'error': f'服务器错误: {str(e)}',
            'detail': error_detail
        }, status=500)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def statistics_dashboard(request):
    """
    统计仪表板数据API
    返回员工部门分布等统计数据
    """
    try:
        has_permission, error_msg = require_roles(request.user, ['ADMIN', 'HR', 'MANAGER'])
        if not has_permission:
            return error_response(error_msg, status.HTTP_403_FORBIDDEN)

        # 员工部门分布统计 - 使用filter排除department为None的情况
        department_stats = md.EmployeeProfile.objects.filter(
            department__isnull=False
        ).values(
            'department__name'
        ).annotate(
            count=Count('user')
        ).order_by('-count')
        
        # 格式化为ECharts所需的数据格式
        department_data = [
            {
                'name': item['department__name'] or '未分配部门',
                'value': item['count']
            }
            for item in department_stats
        ]
        
        # 员工岗位分布统计
        position_stats = md.EmployeeProfile.objects.filter(
            position__isnull=False
        ).values(
            'position__name'
        ).annotate(
            count=Count('user')
        ).order_by('-count')
        
        # 格式化为ECharts所需的数据格式
        position_data = [
            {
                'name': item['position__name'] or '未分配岗位',
                'value': item['count']
            }
            for item in position_stats
        ]
        
        # 考勤趋势统计（支持日期范围筛选）
        today = timezone.now().date()
        # 获取日期范围参数
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # 限制最大范围不超过365天
                if (end_date - start_date).days > 365:
                    end_date = start_date + timedelta(days=365)
            except ValueError:
                # 日期格式错误，使用默认30天
                start_date = today - timedelta(days=30)
                end_date = today
        else:
            # 默认最近30天
            start_date = today - timedelta(days=30)
            end_date = today
        
        attendance_trend = md.AttendanceRecord.objects.filter(
            work_date__gte=start_date,
            work_date__lte=end_date
        ).values(
            'work_date'
        ).annotate(
            count=Count('employee', distinct=True)
        ).order_by('work_date')
        
        # 生成完整的日期序列
        date_list = []
        attendance_count_list = []
        current_date = start_date
        
        # 创建日期到人数的映射
        attendance_dict = {item['work_date'].strftime('%Y-%m-%d'): item['count'] for item in attendance_trend}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_list.append(date_str)
            attendance_count_list.append(attendance_dict.get(date_str, 0))
            current_date += timedelta(days=1)
        
        attendance_trend_data = {
            'dates': date_list,
            'counts': attendance_count_list
        }
        
        # 部门平均薪酬统计（横向条形图）
        # 获取最新一个月的薪酬数据
        latest_period = md.Payroll.objects.values('period').order_by('-period').first()
        if latest_period:
            latest_period_str = latest_period['period']
            salary_stats = md.Payroll.objects.filter(
                period=latest_period_str,
                employee__profile__department__isnull=False
            ).values(
                'employee__profile__department__name'
            ).annotate(
                avg_salary=Avg('net_pay')
            ).order_by('-avg_salary')
            
            salary_data = [
                {
                    'name': item['employee__profile__department__name'] or '未分配部门',
                    'value': float(item['avg_salary']) if item['avg_salary'] else 0
                }
                for item in salary_stats
            ]
        else:
            salary_data = []
        
        # 请假类型统计（堆叠柱状图：按状态堆叠）
        leave_stats = md.LeaveRequest.objects.values(
            'type', 'status'
        ).annotate(
            count=Count('id')
        ).order_by('type', 'status')
        
        # 组织数据格式：{type: {PENDING: count, APPROVED: count, REJECTED: count}}
        leave_type_dict = {}
        status_list = ['PENDING', 'APPROVED', 'REJECTED']
        
        for item in leave_stats:
            leave_type = item['type'] or '其他'
            status = item['status']
            count = item['count']
            
            if leave_type not in leave_type_dict:
                leave_type_dict[leave_type] = {s: 0 for s in status_list}
            leave_type_dict[leave_type][status] = count
        
        # 转换为堆叠柱状图格式
        leave_categories = list(leave_type_dict.keys())
        leave_series_data = []
        # 导入状态选择
        from Model.models import REQ_STATUS, STATUS_CHOICES
        req_status_dict = dict(REQ_STATUS)
        status_choices_dict = dict(STATUS_CHOICES)
        
        for status in status_list:
            leave_series_data.append({
                'name': req_status_dict.get(status, status),
                'type': 'bar',
                'stack': 'leave',
                'data': [leave_type_dict.get(cat, {}).get(status, 0) for cat in leave_categories]
            })
        
        leave_data = {
            'categories': leave_categories,
            'series': leave_series_data
        }
        
        # 员工状态分布（玫瑰图）
        status_stats = md.EmployeeProfile.objects.values(
            'status'
        ).annotate(
            count=Count('user')
        ).order_by('-count')
        
        status_data = [
            {
                'name': status_choices_dict.get(item['status'], item['status']),
                'value': item['count']
            }
            for item in status_stats
        ]
        
        # 绩效趋势分析（最近12个月的平均绩效）
        from decimal import Decimal
        performance_trend_data = []
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30 * i)
            period_str = month_date.strftime('%Y-%m')
            performance_records = md.PerformanceRecord.objects.filter(period=period_str)
            if performance_records.exists():
                avg_score = performance_records.aggregate(avg=Avg('score'))['avg']
                performance_trend_data.append({
                    'period': period_str,
                    'avg_score': float(avg_score) if avg_score else 0
                })
            else:
                performance_trend_data.append({
                    'period': period_str,
                    'avg_score': 0
                })
        
        # 薪酬成本趋势（最近12个月的总薪酬成本）
        salary_trend_data = []
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30 * i)
            period_str = month_date.strftime('%Y-%m')
            payroll_records = md.Payroll.objects.filter(period=period_str, status='CONFIRMED')
            if payroll_records.exists():
                total_cost = payroll_records.aggregate(total=Sum('net_pay'))['total']
                salary_trend_data.append({
                    'period': period_str,
                    'total_cost': float(total_cost) if total_cost else 0
                })
            else:
                salary_trend_data.append({
                    'period': period_str,
                    'total_cost': 0
                })
        
        # 入职离职趋势（最近12个月）
        hire_trend_data = []
        leave_trend_data = []
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30 * i)
            year = month_date.year
            month = month_date.month
            period_start = date(year, month, 1)
            if month == 12:
                period_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(year, month + 1, 1) - timedelta(days=1)
            
            # 入职人数（按hire_date统计）
            hire_count = md.EmployeeProfile.objects.filter(
                hire_date__gte=period_start,
                hire_date__lte=period_end
            ).count()
            
            # 离职人数（简化：统计当前状态为离职且在当月更新过的员工）
            # 注意：这里简化处理，实际应该记录离职日期
            leave_profiles = md.EmployeeProfile.objects.filter(status='LEAVE')
            leave_count = 0
            for profile in leave_profiles:
                if profile.updated_at:
                    profile_date = profile.updated_at.date()
                    if period_start <= profile_date <= period_end:
                        leave_count += 1
            
            period_str = period_start.strftime('%Y-%m')
            hire_trend_data.append({
                'period': period_str,
                'count': hire_count
            })
            leave_trend_data.append({
                'period': period_str,
                'count': leave_count
            })
        
        # 部门绩效对比（各部门平均绩效，取最近一个期间）
        latest_performance_period = md.PerformanceRecord.objects.values('period').order_by('-period').first()
        department_performance_data = []
        if latest_performance_period:
            period_str = latest_performance_period['period']
            dept_performance = md.PerformanceRecord.objects.filter(
                period=period_str,
                employee__profile__department__isnull=False
            ).values(
                'employee__profile__department__name'
            ).annotate(
                avg_score=Avg('score'),
                count=Count('employee', distinct=True)
            ).order_by('-avg_score')
            
            department_performance_data = [
                {
                    'name': item['employee__profile__department__name'] or '未分配部门',
                    'avg_score': float(item['avg_score']) if item['avg_score'] else 0,
                    'count': item['count']
                }
                for item in dept_performance
            ]
        
        return Response({
            'department_distribution': department_data,
            'position_distribution': position_data,
            'attendance_trend': attendance_trend_data,
            'salary_by_department': salary_data,
            'leave_by_type': leave_data,
            'employee_status': status_data,
            'performance_trend': performance_trend_data,
            'salary_trend': salary_trend_data,
            'hire_leave_trend': {
                'hire': hire_trend_data,
                'leave': leave_trend_data
            },
            'department_performance': department_performance_data,
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"统计API错误: {str(e)}")
        print(error_detail)
        return Response({
            'error': f'服务器错误: {str(e)}',
            'detail': error_detail
        }, status=500)


# 招聘管理视图集

class RecruitmentRequirementViewSet(LoggingMixin, viewsets.ModelViewSet):
    """招聘需求管理视图集"""
    # 使用prefetch_related而不是select_related来避免字符集冲突
    queryset = md.RecruitmentRequirement.objects.all().order_by('-created_at')
    serializer_class = serializers.RecruitmentRequirementSerializer
    permission_classes = [IsAdminHRManager]
    module_name = "招聘管理"
    resource_type = "RecruitmentRequirement"
    
    def list(self, request, *args, **kwargs):
        """列表查询，添加错误处理"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"获取招聘需求列表时发生错误: {error_detail}")
            return Response(
                {
                    'error': f'获取招聘需求列表失败: {str(e)}',
                    'detail': str(error_detail) if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """创建招聘需求，添加详细的错误处理"""
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"创建招聘需求时发生错误: {error_detail}")
            # 如果是序列化器验证错误，返回详细错误信息
            if hasattr(e, 'detail'):
                return Response(
                    {'error': '验证失败', 'detail': e.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {
                    'error': f'创建失败: {str(e)}',
                    'detail': str(error_detail) if settings.DEBUG else None
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        """创建时设置发布人"""
        serializer.save(publisher=self.request.user)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布招聘需求"""
        requirement = self.get_object()
        if requirement.status == 'PUBLISHED':
            return Response(
                {'error': '招聘需求已经发布'},
                status=status.HTTP_400_BAD_REQUEST
            )
        requirement.status = 'PUBLISHED'
        requirement.publish_time = timezone.now()
        requirement.publisher = request.user
        requirement.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(requirement.id),
            f"发布招聘需求: {requirement.title}"
        )
        
        return Response({'message': '发布成功'})
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """关闭招聘需求"""
        requirement = self.get_object()
        requirement.status = 'CLOSED'
        requirement.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(requirement.id),
            f"关闭招聘需求: {requirement.title}"
        )
        
        return Response({'message': '关闭成功'})


class ResumeViewSet(LoggingMixin, viewsets.ModelViewSet):
    """简历管理视图集"""
    queryset = md.Resume.objects.select_related(
        'recruitment', 'recruiter'
    ).all().order_by('-created_at')
    serializer_class = serializers.ResumeSerializer
    permission_classes = [IsAdminHRManager]
    module_name = "招聘管理"
    resource_type = "Resume"
    
    def get_queryset(self):
        """根据招聘需求ID筛选"""
        queryset = super().get_queryset()
        recruitment_id = self.request.query_params.get('recruitment_id', None)
        if recruitment_id:
            queryset = queryset.filter(recruitment_id=recruitment_id)
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def perform_create(self, serializer):
        """创建时设置处理人"""
        serializer.save(recruiter=self.request.user)


class InterviewViewSet(LoggingMixin, viewsets.ModelViewSet):
    """面试管理视图集"""
    queryset = md.Interview.objects.select_related(
        'resume', 'created_by'
    ).prefetch_related('interviewers').all().order_by('-scheduled_time')
    serializer_class = serializers.InterviewSerializer
    permission_classes = [IsAdminHRManager]
    module_name = "招聘管理"
    resource_type = "Interview"
    
    def get_queryset(self):
        """根据简历ID筛选"""
        queryset = super().get_queryset()
        resume_id = self.request.query_params.get('resume_id', None)
        if resume_id:
            queryset = queryset.filter(resume_id=resume_id)
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def perform_create(self, serializer):
        """创建时设置创建人"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成面试"""
        interview = self.get_object()
        result = request.data.get('result')
        score = request.data.get('score')
        comment = request.data.get('comment')
        
        interview.status = 'COMPLETED'
        if result:
            interview.result = result
        if score is not None:
            interview.score = score
        if comment:
            interview.comment = comment
        interview.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(interview.id),
            f"完成面试: {interview.resume.name} - 第{interview.round}轮"
        )
        
        return Response({'message': '面试已完成'})


class OfferViewSet(LoggingMixin, viewsets.ModelViewSet):
    """录用管理视图集"""
    queryset = md.Offer.objects.select_related(
        'resume', 'department', 'position', 'created_by'
    ).all().order_by('-created_at')
    serializer_class = serializers.OfferSerializer
    permission_classes = [IsAdminHRManager]
    module_name = "招聘管理"
    resource_type = "Offer"
    
    def get_queryset(self):
        """根据状态筛选"""
        queryset = super().get_queryset()
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def perform_create(self, serializer):
        """创建时设置创建人"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """发送Offer"""
        offer = self.get_object()
        if offer.status != 'PENDING':
            return Response(
                {'error': 'Offer状态不正确，无法发送'},
                status=status.HTTP_400_BAD_REQUEST
            )
        offer.status = 'SENT'
        offer.sent_time = timezone.now()
        offer.save()
        
        # 更新简历状态
        offer.resume.status = 'OFFER'
        offer.resume.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(offer.id),
            f"发送Offer: {offer.resume.name}"
        )
        
        return Response({'message': 'Offer已发送'})
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """接受Offer"""
        offer = self.get_object()
        if offer.status != 'SENT':
            return Response(
                {'error': 'Offer状态不正确，无法接受'},
                status=status.HTTP_400_BAD_REQUEST
            )
        offer.status = 'ACCEPTED'
        offer.accepted_time = timezone.now()
        offer.save()
        
        # 更新简历状态
        offer.resume.status = 'HIRED'
        offer.resume.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(offer.id),
            f"接受Offer: {offer.resume.name}"
        )
        
        return Response({'message': 'Offer已接受'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝Offer"""
        offer = self.get_object()
        if offer.status != 'SENT':
            return Response(
                {'error': 'Offer状态不正确，无法拒绝'},
                status=status.HTTP_400_BAD_REQUEST
            )
        rejected_reason = request.data.get('rejected_reason', '')
        offer.status = 'REJECTED'
        offer.rejected_reason = rejected_reason
        offer.save()
        
        log_utils.log_update(
            request,
            self.module_name,
            self.resource_type,
            str(offer.id),
            f"拒绝Offer: {offer.resume.name}"
        )
        
        return Response({'message': 'Offer已拒绝'})


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    操作日志视图集（只读）
    """
    serializer_class = serializers.OperationLogSerializer
    permission_classes = [IsAdminOrHR]

    def get_queryset(self):
        queryset = md.OperationLog.objects.all().order_by('-created_at')

        # 筛选条件
        user_code = self.request.query_params.get('user_id', None)  # 前端参数名为user_id
        action_type = self.request.query_params.get('action_type', None)
        module = self.request.query_params.get('module', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if user_code:
            queryset = queryset.filter(user_code__icontains=user_code)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if module:
            queryset = queryset.filter(module__icontains=module)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset


