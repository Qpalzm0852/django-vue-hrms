from rest_framework_jwt.serializers import JSONWebTokenSerializer
from django.contrib.auth import authenticate
try:
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class CustomJSONWebTokenSerializer(JSONWebTokenSerializer):
    """
    自定义JWT序列化器，使用user_id而不是username
    """
    username_field = 'user_id'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_id'] = serializers.CharField()
        if 'username' in self.fields:
            del self.fields['username']
    
    def validate(self, attrs):
        user_id = attrs.get(self.username_field)
        password = attrs.get('password')

        if user_id and password:
            # 直接使用 UserManager 查找用户
            from Model.models import User
            try:
                user = User.objects.get(user_id=user_id)
                # 验证密码
                if user.check_password(password):
                    if not user.is_active:
                        msg = _('User account is disabled.')
                        raise serializers.ValidationError(msg)
                    return {
                        'token': self._get_token(user),
                        'user': user
                    }
                else:
                    msg = _('Unable to log in with provided credentials.')
                    raise serializers.ValidationError(msg)
            except User.DoesNotExist:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)
    
    def _get_token(self, user):
        from rest_framework_jwt.settings import api_settings
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return token

