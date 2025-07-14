from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Tenant
from threading import local

# Thread local para almacenar el tenant actual
_thread_locals = local()


class TenantMiddleware:
    """
    Middleware para manejar el tenant (empresa) en todas las vistas.
    Filtra automáticamente los datos por el tenant del usuario autenticado.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar la solicitud antes de que llegue a la vista
        request.tenant = None
        
        if request.user.is_authenticated:
            # Si es superusuario, verificar tenant temporal en sesión
            if request.user.is_superuser:
                temp_tenant_id = request.session.get('temp_tenant_id')
                if temp_tenant_id:
                    try:
                        tenant = Tenant.objects.get(id=temp_tenant_id, is_active=True)
                        request.tenant = tenant
                        _thread_locals.tenant = tenant
                    except Tenant.DoesNotExist:
                        # Limpiar tenant temporal si no existe o está inactivo
                        request.session.pop('temp_tenant_id', None)
                        request.session.pop('temp_tenant_name', None)
                        # Si el tenant existe pero está inactivo, mostrar mensaje
                        try:
                            inactive_tenant = Tenant.objects.get(id=temp_tenant_id)
                            if not inactive_tenant.is_active:
                                messages.error(request, f'La empresa "{inactive_tenant.name}" está inactiva. No puedes acceder al sistema.')
                                return redirect('logout')
                        except Tenant.DoesNotExist:
                            pass
            else:
                # Obtener el tenant del usuario a través del perfil
                try:
                    user_profile = request.user.profile
                    request.tenant = user_profile.tenant
                    
                    # Verificar si el tenant está activo
                    if request.tenant and not request.tenant.is_active:
                        # Evitar redirección infinita si ya estamos en tenant-inactive
                        if request.path != '/tenant-inactive/':
                            messages.error(request, f'La empresa "{request.tenant.name}" está inactiva. Contacta al administrador del sistema.')
                            return redirect('tenant-inactive')
                    
                    # Almacenar el tenant en thread locals para los managers
                    _thread_locals.tenant = user_profile.tenant
                except:
                    # Si el usuario no tiene perfil, buscar el primer tenant activo
                    tenant = Tenant.objects.filter(is_active=True).first()
                    if tenant:
                        request.tenant = tenant
                        _thread_locals.tenant = tenant
                        # Crear perfil de usuario si no existe
                        from .models import UserProfile
                        UserProfile.objects.get_or_create(
                            user=request.user,
                            defaults={'tenant': tenant, 'role': 'operator'}
                        )
        
        response = self.get_response(request)
        
        # Limpiar thread locals después de la respuesta
        if hasattr(_thread_locals, 'tenant'):
            delattr(_thread_locals, 'tenant')
        
        return response


class TenantRequiredMiddleware:
    """
    Middleware para asegurar que el usuario tenga un tenant asignado
    en ciertas vistas que requieren tenant.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que requieren tenant
        tenant_required_urls = [
            '/dashboard/',
            '/entry/',
            '/exit/',
            '/print-ticket/',
            '/print-exit-ticket/',
            '/reports/',
            '/cash-register/',
            '/categorias/',
            '/mi-empresa/',
            '/caja/',
        ]
        
        # Verificar si la URL actual requiere tenant
        requires_tenant = any(request.path.startswith(url) for url in tenant_required_urls)
        
        if requires_tenant and request.user.is_authenticated:
            # Los superusuarios pueden acceder si tienen tenant temporal
            if not request.user.is_superuser:
                if not hasattr(request, 'tenant') or not request.tenant:
                    messages.error(request, 'No tienes acceso a ninguna empresa. Contacta al administrador.')
                    return redirect('logout')
                # Verificar que el tenant esté activo
                elif not request.tenant.is_active:
                    # Evitar redirección infinita si ya estamos en tenant-inactive
                    if request.path != '/tenant-inactive/':
                        messages.error(request, f'Tu empresa "{request.tenant.name}" está inactiva. No puedes acceder al sistema.')
                        return redirect('tenant-inactive')
            else:
                # Para superusuarios, verificar si tienen tenant temporal
                if not hasattr(request, 'tenant') or not request.tenant:
                    messages.error(request, 'No tienes una empresa asignada temporalmente.')
                    return redirect('superadmin-dashboard')
                else:
                    # Verificar si el tenant temporal está activo
                    if not request.tenant.is_active:
                        # Evitar redirección infinita si ya estamos en tenant-inactive
                        if request.path != '/tenant-inactive/':
                            messages.error(request, f'La empresa "{request.tenant.name}" está inactiva.')
                            return redirect('tenant-inactive')
        
        response = self.get_response(request)
        return response 