# MyWeb/Model/log_utils.py
"""
鎿嶄綔鏃ュ織璁板綍宸ュ叿妯″潡
鎻愪緵渚挎嵎鐨勬棩蹇楄褰曞嚱鏁?
"""
from . import models as md


def log_operation(request, action_type, module, resource_type=None, resource_id=None, description=None):
    """
    璁板綍鎿嶄綔鏃ュ織
    
    Args:
        request: Django request瀵硅薄
        action_type: 鎿嶄綔绫诲瀷 (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT, EXPORT)
        module: 妯″潡鍚嶇О锛屽锛氬憳宸ョ鐞嗐€佽€冨嫟绠＄悊
        resource_type: 璧勬簮绫诲瀷锛屽锛欵mployeeProfile銆丄ttendanceRecord
        resource_id: 璧勬簮ID
        description: 鎿嶄綔鎻忚堪锛屽鏋滀负None鍒欒嚜鍔ㄧ敓鎴?
    """
    try:
        user = getattr(request, 'user', None)
        user_code = user.user_id if user and hasattr(user, 'user_id') else None
        user_name = user.name if user and hasattr(user, 'name') else None
        
        # 濡傛灉娌℃湁鎻愪緵鎻忚堪锛岃嚜鍔ㄧ敓鎴?
        if not description:
            action_name = dict(md.ACTION_TYPE_CHOICES).get(action_type, action_type)
            if resource_type and resource_id:
                description = f"{action_name} {resource_type} (ID: {resource_id})"
            else:
                description = f"{action_name} {module}"
        
        # 鑾峰彇IP鍦板潃
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # 鑾峰彇鐢ㄦ埛浠ｇ悊
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        if user_agent:
            user_agent = user_agent[:255]  # 闄愬埗闀垮害
        
        # 鍒涘缓鏃ュ織璁板綍
        md.OperationLog.objects.create(
            user=user if user and user.is_authenticated else None,
            user_code=user_code,
            user_name=user_name,
            action_type=action_type,
            module=module,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # 鏃ュ織璁板綍澶辫触涓嶅簲褰卞搷涓讳笟鍔℃祦绋?
        print(f"璁板綍鎿嶄綔鏃ュ織澶辫触: {str(e)}")


def log_create(request, module, resource_type, resource_id, description=None):
    """璁板綍鍒涘缓鎿嶄綔"""
    log_operation(request, 'CREATE', module, resource_type, resource_id, description)


def log_update(request, module, resource_type, resource_id, description=None):
    """璁板綍鏇存柊鎿嶄綔"""
    log_operation(request, 'UPDATE', module, resource_type, resource_id, description)


def log_delete(request, module, resource_type, resource_id, description=None):
    """璁板綍鍒犻櫎鎿嶄綔"""
    log_operation(request, 'DELETE', module, resource_type, resource_id, description)


def log_login(request, user_id, user_name):
    """璁板綍鐧诲綍鎿嶄綔"""
    try:
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        if user_agent:
            user_agent = user_agent[:255]
        
        md.OperationLog.objects.create(
            user_code=user_id,
            user_name=user_name,
            action_type='LOGIN',
            module='绯荤粺鐧诲綍',
            description=f'鐢ㄦ埛 {user_name}({user_id}) 鐧诲綍绯荤粺',
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"璁板綍鐧诲綍鏃ュ織澶辫触: {str(e)}")


def log_approve(request, module, resource_type, resource_id, description=None):
    """璁板綍瀹℃壒鎿嶄綔"""
    log_operation(request, 'APPROVE', module, resource_type, resource_id, description)


def log_reject(request, module, resource_type, resource_id, description=None):
    """璁板綍鎷掔粷鎿嶄綔"""
    log_operation(request, 'REJECT', module, resource_type, resource_id, description)


def log_export(request, module, description=None):
    """璁板綍瀵煎嚭鎿嶄綔"""
    log_operation(request, 'EXPORT', module, description=description or f'瀵煎嚭{module}鏁版嵁')

