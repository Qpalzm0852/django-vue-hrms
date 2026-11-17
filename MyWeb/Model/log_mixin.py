# MyWeb/Model/log_mixin.py
"""
日志记录混入类
为ViewSet提供自动日志记录功能
"""
from . import log_utils


class LoggingMixin:
    """日志记录混入类，在ViewSet中使用"""
    
    # 模块名称映射，子类可以覆盖
    module_name = "未命名模块"
    resource_type = None
    
    def get_module_name(self):
        """获取模块名称"""
        return self.module_name
    
    def get_resource_type(self):
        """获取资源类型"""
        if self.resource_type:
            return self.resource_type
        # 自动从queryset推断
        if hasattr(self, 'queryset') and self.queryset:
            model_name = self.queryset.model.__name__
            return model_name
        return None
    
    def perform_create(self, serializer):
        """创建操作后记录日志"""
        instance = serializer.save()
        module = self.get_module_name()
        resource_type = self.get_resource_type()
        description = f"创建{module}记录"
        
        if hasattr(instance, 'user_id'):
            resource_id = instance.user_id
        elif hasattr(instance, 'id'):
            resource_id = instance.id
        elif hasattr(instance, 'pk'):
            resource_id = instance.pk
        else:
            resource_id = None
        
        log_utils.log_create(
            self.request,
            module,
            resource_type,
            resource_id,
            description
        )
        return instance
    
    def perform_update(self, serializer):
        """更新操作后记录日志"""
        instance = serializer.save()
        module = self.get_module_name()
        resource_type = self.get_resource_type()
        description = f"更新{module}记录"
        
        if hasattr(instance, 'user_id'):
            resource_id = instance.user_id
        elif hasattr(instance, 'id'):
            resource_id = instance.id
        elif hasattr(instance, 'pk'):
            resource_id = instance.pk
        else:
            resource_id = None
        
        log_utils.log_update(
            self.request,
            module,
            resource_type,
            resource_id,
            description
        )
        return instance
    
    def perform_destroy(self, instance):
        """删除操作前记录日志"""
        module = self.get_module_name()
        resource_type = self.get_resource_type()
        description = f"删除{module}记录"
        
        if hasattr(instance, 'user_id'):
            resource_id = instance.user_id
        elif hasattr(instance, 'id'):
            resource_id = instance.id
        elif hasattr(instance, 'pk'):
            resource_id = instance.pk
        else:
            resource_id = None
        
        log_utils.log_delete(
            self.request,
            module,
            resource_type,
            resource_id,
            description
        )
        return super().perform_destroy(instance)

