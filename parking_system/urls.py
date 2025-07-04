from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from parking import views
from parking.views import (
    ParkingLotUpdateView, custom_logout, CategoryListView, CategoryCreateView,
    VehicleEntryView, vehicle_exit, print_ticket, print_exit_ticket, ReportView,
    company_profile, category_edit, cash_register
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.pagina_inicial, name='pagina_inicial'),
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
    path('categorias/<int:pk>/editar/', category_edit, name='category-edit'),
    path('categorias/<int:pk>/eliminar/', views.CategoryDeleteView.as_view(), name='category-delete'),
    path('reports/', ReportView.as_view(), name='reports'),
    path('cash-register/', cash_register, name='cash_register'),  # Nueva URL para Cuadre de Caja
    path('validate-plate/<str:plate>/', views.validate_plate, name='validate-plate'),
    path('accounts/', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)