from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from parking import views
from parking.views import (
    ParkingLotUpdateView, custom_logout, CategoryListView, CategoryCreateView, CategoryEditView,
    VehicleEntryView, vehicle_exit, print_ticket, print_exit_ticket, ReportView,
    company_profile, cash_register,
    superadmin_dashboard, tenant_list, tenant_create, tenant_edit, tenant_detail,
    tenant_toggle_status, tenant_login, tenant_selection, exit_tenant_mode,
    tenant_users_list, tenant_user_create, tenant_user_edit, tenant_user_password,
    tenant_user_toggle_status, tenant_user_delete, CustomLoginView, apertura_turno, registrar_movimiento, cierre_turno, historial_cuadre_caja,
    # Nuevas vistas de roles y permisos
    roles_list, role_create, role_edit, role_permissions, role_delete, role_toggle_status,
    user_roles, user_permissions, permissions_overview, access_log
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('entry/', VehicleEntryView.as_view(), name='vehicle-entry'),
    path('exit/', vehicle_exit, name='vehicle-exit'),
    path('print-ticket/', print_ticket, name='print-ticket'),
    path('print-exit-ticket/', print_exit_ticket, name='print-exit-ticket'),
    path('reprint-ticket/<int:ticket_id>/', print_ticket, name='reprint-ticket'),
    path('parking-lot/<int:pk>/update/', ParkingLotUpdateView.as_view(), name='parking-lot-update'),
    path('mi-empresa/', company_profile, name='company_profile'),
    path('logout/', custom_logout, name='logout'),
    path('categorias/', CategoryListView.as_view(), name='category-list'),
    path('categorias/new/', CategoryCreateView.as_view(), name='category-create'),
    path('categorias/<int:pk>/editar/', CategoryEditView.as_view(), name='category-edit'),
    path('categorias/<int:pk>/eliminar/', views.CategoryDeleteView.as_view(), name='category-delete'),
    path('reports/', ReportView.as_view(), name='reports'),
    path('cash-register/', cash_register, name='cash_register'),  # Nueva URL para Cuadre de Caja
    path('validate-plate/<str:plate>/', views.validate_plate, name='validate-plate'),
    path('tenant-inactive/', views.tenant_inactive, name='tenant-inactive'),
    
    # URLs para Superadministrador
    path('superadmin/', superadmin_dashboard, name='superadmin-dashboard'),
    path('superadmin/tenants/', tenant_list, name='superadmin-tenant-list'),
    path('superadmin/tenants/create/', tenant_create, name='superadmin-tenant-create'),
    path('superadmin/tenants/<int:pk>/', tenant_detail, name='superadmin-tenant-detail'),
    path('superadmin/tenants/<int:pk>/edit/', tenant_edit, name='superadmin-tenant-edit'),
    path('superadmin/tenants/<int:pk>/toggle-status/', tenant_toggle_status, name='superadmin-tenant-toggle-status'),
    path('superadmin/tenants/<int:pk>/login/', tenant_login, name='superadmin-tenant-login'),
    path('superadmin/exit-tenant-mode/', exit_tenant_mode, name='exit-tenant-mode'),
    path('select-tenant/', tenant_selection, name='tenant-selection'),
    
    # Vistas de gestión de usuarios de empresa
    path('usuarios/', tenant_users_list, name='tenant-users-list'),
    path('usuarios/crear/', tenant_user_create, name='tenant-user-create'),
    path('usuarios/<int:pk>/editar/', tenant_user_edit, name='tenant-user-edit'),
    path('usuarios/<int:pk>/password/', tenant_user_password, name='tenant-user-password'),
    path('usuarios/<int:pk>/toggle-status/', tenant_user_toggle_status, name='tenant-user-toggle-status'),
    path('usuarios/<int:pk>/eliminar/', tenant_user_delete, name='tenant-user-delete'),
    
    # URLs para gestión de roles y permisos
    path('roles/', roles_list, name='roles-list'),
    path('roles/crear/', role_create, name='role-create'),
    path('roles/<int:pk>/editar/', role_edit, name='role-edit'),
    path('roles/<int:pk>/permisos/', role_permissions, name='role-permissions'),
    path('roles/<int:pk>/eliminar/', role_delete, name='role-delete'),
    path('roles/<int:pk>/toggle-status/', role_toggle_status, name='role-toggle-status'),
    
    # URLs para asignación de roles y permisos a usuarios
    path('usuarios/<int:pk>/roles/', user_roles, name='user-roles'),
    path('usuarios/<int:pk>/permisos/', user_permissions, name='user-permissions'),
    
    # URLs para vista general y bitácora
    path('permisos/overview/', permissions_overview, name='permissions-overview'),
    path('permisos/bitacora/', access_log, name='access-log'),
    
    # URLs de autenticación de Django (mantener para password reset)
    path('accounts/login/', CustomLoginView.as_view(), name='accounts-login'),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('caja/apertura/', apertura_turno, name='apertura_turno'),
    path('caja/movimiento/', registrar_movimiento, name='registrar_movimiento'),
    path('caja/cierre/', cierre_turno, name='cierre_turno'),
    path('caja/historial/', historial_cuadre_caja, name='historial_cuadre_caja'),
]