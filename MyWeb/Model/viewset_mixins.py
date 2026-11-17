# MyWeb/Model/viewset_mixins.py
"""
ViewSet混入类
提供通用的ViewSet功能增强
"""
from rest_framework.response import Response
from rest_framework import status
from Model.utils import require_roles, error_response


class ApprovalMixin:
    """
    审批功能混入类
    为ViewSet提供统一的审批和拒绝方法
    """
    approval_allowed_roles = ['ADMIN', 'HR', 'MANAGER']

    def check_approval_permission(self, request):
        """
        检查审批权限

        Returns:
            tuple: (has_permission, error_response)
                   如果无权限，返回(False, Response对象)
                   如果有权限，返回(True, None)
        """
        has_permission, error_msg = require_roles(request.user, self.approval_allowed_roles)
        if not has_permission:
            return False, error_response(
                error_message=error_msg,
                status_code=status.HTTP_403_FORBIDDEN
            )
        return True, None

    def check_approval_scope(self, request, instance):
        """
        检查审批数据范围（经理仅可审批本部门员工）
        """
        user_role = getattr(request.user, 'role', None)
        if user_role != 'MANAGER':
            return True, None

        try:
            manager_department = request.user.profile.department
        except Exception:
            return False, error_response(
                error_message='当前账号未绑定部门，无法执行审批',
                status_code=status.HTTP_403_FORBIDDEN
            )

        employee = getattr(instance, 'employee', None)
        if employee is None:
            return False, error_response(
                error_message='审批对象缺少员工信息，无法执行审批',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        employee_department = getattr(getattr(employee, 'profile', None), 'department', None)
        if employee_department != manager_department:
            return False, error_response(
                error_message='无权审批非本部门员工申请',
                status_code=status.HTTP_403_FORBIDDEN
            )

        return True, None

    def approve_request(self, request, instance, status_field='status',
                       approver_field='approver', log_func=None, log_module=None, log_resource_type=None):
        """
        通用的审批通过方法

        Args:
            request: request对象
            instance: 要审批的实例对象
            status_field: 状态字段名，默认为'status'
            approver_field: 审批人字段名，默认为'approver'
            log_func: 日志记录函数，如 log_utils.log_approve
            log_module: 日志模块名称
            log_resource_type: 日志资源类型
        """
        # 检查权限
        has_permission, error_response_obj = self.check_approval_permission(request)
        if not has_permission:
            return error_response_obj

        has_scope, scope_error_response = self.check_approval_scope(request, instance)
        if not has_scope:
            return scope_error_response

        # 设置状态和审批人
        setattr(instance, status_field, 'APPROVED')
        if request.user and hasattr(instance, approver_field):
            setattr(instance, approver_field, request.user)
        instance.save()

        # 记录日志
        if log_func and log_module and log_resource_type:
            resource_id = getattr(instance, 'id', None) or getattr(instance, 'pk', None)
            log_func(
                request,
                log_module,
                log_resource_type,
                resource_id,
                f"审批通过 (ID: {resource_id})"
            )

        return Response({'status': 'approved'})

    def reject_request(self, request, instance, status_field='status',
                      approver_field='approver', log_func=None, log_module=None, log_resource_type=None):
        """
        通用的拒绝方法

        Args:
            request: request对象
            instance: 要拒绝的实例对象
            status_field: 状态字段名，默认为'status'
            approver_field: 审批人字段名，默认为'approver'
            log_func: 日志记录函数，如 log_utils.log_reject
            log_module: 日志模块名称
            log_resource_type: 日志资源类型
        """
        # 检查权限
        has_permission, error_response_obj = self.check_approval_permission(request)
        if not has_permission:
            return error_response_obj

        has_scope, scope_error_response = self.check_approval_scope(request, instance)
        if not has_scope:
            return scope_error_response

        # 设置状态和审批人
        setattr(instance, status_field, 'REJECTED')
        if request.user and hasattr(instance, approver_field):
            setattr(instance, approver_field, request.user)
        instance.save()

        # 记录日志
        if log_func and log_module and log_resource_type:
            resource_id = getattr(instance, 'id', None) or getattr(instance, 'pk', None)
            log_func(
                request,
                log_module,
                log_resource_type,
                resource_id,
                f"拒绝 (ID: {resource_id})"
            )

        return Response({'status': 'rejected'})
