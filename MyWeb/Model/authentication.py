"""Custom authentication backends for the project."""

from django.core import signing
from rest_framework import authentication, exceptions

from . import models as md


class SignedTokenAuthentication(authentication.BaseAuthentication):
    """Authenticate using a signed token from Authorization header."""

    max_age_seconds = 60 * 60 * 24
    allowed_prefixes = {'jwt', 'bearer'}

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth:
            return None

        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('认证头格式错误')

        prefix = auth[0].decode('utf-8', errors='ignore').lower()
        if prefix not in self.allowed_prefixes:
            return None

        token = auth[1].decode('utf-8', errors='ignore')
        if not token:
            raise exceptions.AuthenticationFailed('Token 为空')

        try:
            payload = signing.loads(token, salt='myweb-auth', max_age=self.max_age_seconds)
        except signing.SignatureExpired:
            raise exceptions.AuthenticationFailed('Token 已过期')
        except signing.BadSignature:
            raise exceptions.AuthenticationFailed('Token 无效')

        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('Token 缺少用户信息')

        try:
            user = md.User.objects.get(user_id=user_id, is_active=True)
        except md.User.DoesNotExist:
            raise exceptions.AuthenticationFailed('用户不存在或已禁用')

        return (user, token)
