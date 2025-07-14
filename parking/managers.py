from django.db import models
from django.contrib.auth.models import User


class TenantManager(models.Manager):
    """
    Manager personalizado que filtra automáticamente por tenant.
    """
    
    def get_queryset(self):
        """Filtrar automáticamente por tenant si está disponible en el request"""
        from django.db import connection
        from threading import local
        
        # Obtener el tenant del thread local
        _thread_locals = local()
        tenant = getattr(_thread_locals, 'tenant', None)
        
        queryset = super().get_queryset()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset
    
    def for_tenant(self, tenant):
        """Filtrar explícitamente por un tenant específico"""
        return super().get_queryset().filter(tenant=tenant)


class UserProfileManager(models.Manager):
    """
    Manager para perfiles de usuario con filtrado por tenant.
    """
    
    def get_queryset(self):
        from django.db import connection
        from threading import local
        
        _thread_locals = local()
        tenant = getattr(_thread_locals, 'tenant', None)
        
        queryset = super().get_queryset()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        return queryset
    
    def for_tenant(self, tenant):
        return super().get_queryset().filter(tenant=tenant) 