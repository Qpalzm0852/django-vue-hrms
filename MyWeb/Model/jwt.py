"""Login endpoint based on signed token, no external JWT dependency required."""

from django.core import signing
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from . import log_utils
from . import models as md


TOKEN_SALT = 'myweb-auth'
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24


def _build_success_response(token, user):
    return {
        'data': {
            'token': token,
            'user_id': user.user_id,
            'user_name': user.name,
            'role': user.role,
        },
        'msg': 'success',
        'status': 200,
    }


def _build_error_response(detail, status_code=400):
    return {
        'msg': 'error',
        'status': status_code,
        'detail': detail,
    }


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def obtain_jwt_token(request):
    """Compatible login endpoint, keeps original response shape."""
    user_id = (request.data.get('user_id') or '').strip()
    password = request.data.get('password') or ''

    if not user_id or not password:
        detail = {
            'non_field_errors': ['必须提供 user_id 和 password'],
        }
        return Response(_build_error_response(detail, 400), status=200)

    try:
        user = md.User.objects.get(user_id=user_id)
    except md.User.DoesNotExist:
        detail = {
            'non_field_errors': ['Unable to log in with provided credentials.'],
        }
        return Response(_build_error_response(detail, 400), status=200)

    if not user.check_password(password):
        detail = {
            'non_field_errors': ['Unable to log in with provided credentials.'],
        }
        return Response(_build_error_response(detail, 400), status=200)

    if not user.is_active:
        detail = {
            'non_field_errors': ['User account is disabled.'],
        }
        return Response(_build_error_response(detail, 400), status=200)

    token = signing.dumps({'user_id': user.user_id}, salt=TOKEN_SALT)

    try:
        log_utils.log_login(request, user.user_id, user.name)
    except Exception as exc:
        print(f'记录登录日志失败: {exc}')

    return Response(_build_success_response(token, user), status=200)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_jwt_token(request):
    """Return the same token if valid and not expired."""
    token = (request.data.get('token') or '').strip()
    if not token:
        return Response(_build_error_response({'token': ['token 不能为空']}, 400), status=200)

    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
        user_id = payload.get('user_id')
        user = md.User.objects.get(user_id=user_id, is_active=True)
    except Exception:
        return Response(_build_error_response({'token': ['token 无效或已过期']}, 400), status=200)

    return Response(_build_success_response(token, user), status=200)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_jwt_token(request):
    """Verify token validity."""
    token = (request.data.get('token') or '').strip()
    if not token:
        return Response(_build_error_response({'token': ['token 不能为空']}, 400), status=200)

    try:
        signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE_SECONDS)
    except Exception:
        return Response(_build_error_response({'token': ['token 无效或已过期']}, 400), status=200)

    return Response({'msg': 'success', 'status': 200}, status=200)
