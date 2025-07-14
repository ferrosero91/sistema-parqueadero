from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
import logging


def tenant_required(view_func):
    """
    Decorador para asegurar que el usuario tenga un tenant asignado.
    Los superusuarios pueden acceder sin tenant.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Los superusuarios pueden acceder sin tenant
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not hasattr(request, 'tenant') or not request.tenant:
            messages.error(request, 'No tienes acceso a ninguna empresa. Contacta al administrador.')
            return redirect('logout')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def permission_required(permission):
    """
    Decorador para verificar permisos específicos del usuario.
    Permite acceso total a usuarios con role='admin' (cualquier variante) o con el rol personalizado 'Administrador' (cualquier variante) activo en su tenant.
    Muestra mensajes claros y logs para depuración.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            logger = logging.getLogger("permisos")
            if not request.user.is_authenticated:
                messages.error(request, 'No has iniciado sesión.')
                logger.warning("Usuario no autenticado")
                return redirect('login')

            try:
                if not hasattr(request.user, 'profile'):
                    messages.error(request, 'No se encontró el perfil de usuario. Contacta al administrador.')
                    logger.error(f"No se encontró perfil para el usuario {request.user}")
                    return redirect('dashboard')
                profile = request.user.profile
                logger.info(f"Validando permisos para usuario: {request.user.username}")

                # 1. Acceso total si el campo role es admin (cualquier variante)
                role_field = getattr(profile, 'role', '').strip().lower()
                if role_field in ['admin', 'administrador']:
                    logger.info(f"Acceso total por role='{role_field}'")
                    return view_func(request, *args, **kwargs)

                # 2. Acceso total si tiene el rol personalizado 'Administrador' (cualquier variante) activo
                user_roles = getattr(profile, 'userrole_set', None)
                if user_roles:
                    for user_role in user_roles.all():
                        role_name = user_role.role.name.strip().lower()
                        if role_name in ['admin', 'administrador'] and user_role.role.is_active:
                            logger.info(f"Acceso total por CustomRole='{role_name}' activo")
                            return view_func(request, *args, **kwargs)

                # 3. Validar permiso específico
                if hasattr(profile, 'has_permission') and profile.has_permission(permission):
                    logger.info(f"Permiso específico concedido: {permission}")
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, f'No tienes permisos para realizar esta acción: {permission}')
                    logger.warning(f"Permiso denegado: {permission} para usuario {request.user.username}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error de permisos: {str(e)}')
                logger.error(f"Error en permission_required: {e}")
                return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorador para verificar que el usuario sea administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            user_profile = request.user.profile
            if user_profile.role != 'admin':
                messages.error(request, 'Solo los administradores pueden acceder a esta función.')
                return redirect('dashboard')
        except:
            messages.error(request, 'Perfil de usuario no encontrado.')
            return redirect('logout')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def operator_required(view_func):
    """
    Decorador para verificar que el usuario sea operador, cajero o administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            user_profile = request.user.profile
            if user_profile.role not in ['admin', 'operator', 'cajero']:
                messages.error(request, 'No tienes permisos para realizar esta acción.')
                return redirect('dashboard')
        except:
            messages.error(request, 'Perfil de usuario no encontrado.')
            return redirect('logout')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def cajero_required(view_func):
    """
    Decorador para verificar que el usuario sea cajero o administrador.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            user_profile = request.user.profile
            if user_profile.role not in ['admin', 'cajero']:
                messages.error(request, 'No tienes permisos para realizar esta acción.')
                return redirect('dashboard')
        except:
            messages.error(request, 'Perfil de usuario no encontrado.')
            return redirect('logout')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view 