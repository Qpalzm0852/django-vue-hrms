# MyWeb/Model/utils.py
"""
后端通用工具函数模块
提供统一的验证、响应格式化等功能
"""
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.conf import settings
import traceback


def validate_period_format(period):
    """
    验证周期格式（YYYY-MM）
    
    Args:
        period: 周期字符串，格式应为 YYYY-MM
        
    Returns:
        tuple: (is_valid, error_message, (year, month))
               如果验证失败，year和month为None
    """
    if not period:
        return False, '周期不能为空', (None, None)
    
    try:
        year, month = map(int, period.split('-'))
        datetime(year, month, 1)  # 验证日期是否有效
        return True, None, (year, month)
    except (ValueError, TypeError):
        return False, '周期格式错误，应为 YYYY-MM', (None, None)


def validate_required_params(data, required_fields, field_names=None):
    """
    验证必需参数
    
    Args:
        data: 数据字典（request.data 或 request.query_params）
        required_fields: 必需字段列表，如 ['employee_id', 'period']
        field_names: 字段中文名称映射，如 {'employee_id': '员工工号', 'period': '统计周期'}
        
    Returns:
        tuple: (is_valid, error_message, missing_fields)
    """
    if field_names is None:
        field_names = {}
    
    missing_fields = []
    for field in required_fields:
        if not data.get(field):
            field_name = field_names.get(field, field)
            missing_fields.append(field_name)
    
    if missing_fields:
        error_msg = f"{'、'.join(missing_fields)}不能为空"
        return False, error_msg, missing_fields
    
    return True, None, []


def success_response(data=None, message='操作成功', status_code=status.HTTP_200_OK):
    """
    统一成功响应格式
    
    Args:
        data: 响应数据
        message: 成功消息
        status_code: HTTP状态码
        
    Returns:
        Response对象
    """
    response_data = {
        'success': True,
        'message': message,
    }
    if data is not None:
        response_data['data'] = data
    
    return Response(response_data, status=status_code)


def error_response(error_message, status_code=status.HTTP_400_BAD_REQUEST, detail=None):
    """
    统一错误响应格式
    
    Args:
        error_message: 错误消息
        status_code: HTTP状态码
        detail: 详细错误信息（仅DEBUG模式显示）
        
    Returns:
        Response对象
    """
    response_data = {
        'error': error_message,
    }
    
    if detail and settings.DEBUG:
        response_data['detail'] = str(detail)
    
    return Response(response_data, status=status_code)


def exception_response(exception, default_message='操作失败', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
    """
    统一异常响应格式
    
    Args:
        exception: 异常对象
        default_message: 默认错误消息
        status_code: HTTP状态码
        
    Returns:
        Response对象
    """
    error_detail = traceback.format_exc()
    error_message = str(exception) if str(exception) else default_message
    
    print(f"{default_message}: {error_detail}")
    
    return error_response(
        error_message=error_message,
        status_code=status_code,
        detail=error_detail if settings.DEBUG else None
    )


def require_roles(user, allowed_roles):
    """
    检查用户角色权限
    
    Args:
        user: 用户对象
        allowed_roles: 允许的角色列表，如 ['ADMIN', 'HR', 'MANAGER']
        
    Returns:
        tuple: (has_permission, error_message)
    """
    user_role = getattr(user, 'role', None)
    if user_role not in allowed_roles:
        role_names = {
            'ADMIN': '管理员',
            'HR': 'HR',
            'MANAGER': '管理者',
            'STAFF': '员工'
        }
        allowed_role_names = [role_names.get(r, r) for r in allowed_roles]
        error_msg = f'您没有权限执行此操作，只有{"、".join(allowed_role_names)}可以操作'
        return False, error_msg
    
    return True, None

