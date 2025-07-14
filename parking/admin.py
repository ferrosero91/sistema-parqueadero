from django.contrib import admin
from .models import Tenant, VehicleCategory, ParkingLot, ParkingTicket, UserProfile, CajaTurno, CajaMovimiento


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'nit', 'telefono', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'nit', 'email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'first_hour_rate', 'additional_hour_rate', 'is_monthly', 'monthly_rate']
    list_filter = ['tenant', 'is_monthly', 'first_hour_rate']
    search_fields = ['name', 'tenant__name']
    list_select_related = ['tenant']
    ordering = ['tenant__name', 'name']


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'tenant', 'nit', 'telefono', 'direccion']
    list_filter = ['tenant']
    search_fields = ['empresa', 'nit', 'tenant__name']
    list_select_related = ['tenant']
    ordering = ['tenant__name']


@admin.register(ParkingTicket)
class ParkingTicketAdmin(admin.ModelAdmin):
    list_display = ['placa', 'tenant', 'category', 'entry_time', 'exit_time', 'amount_paid', 'get_status_display']
    list_filter = ['tenant', 'category', 'entry_time', 'exit_time']
    search_fields = ['placa', 'tenant__name', 'category__name']
    list_select_related = ['tenant', 'category']
    readonly_fields = ['ticket_id', 'entry_time', 'barcode']
    ordering = ['-entry_time']
    
    def get_status_display(self, obj):
        status = obj.get_status()
        if status['is_active']:
            return f"Activo - {status['duration']['hours']}h {status['duration']['minutes']}m"
        else:
            return f"Cerrado - ${status['current_fee']}"
    get_status_display.short_description = 'Estado'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['tenant', 'role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    list_select_related = ['user', 'tenant']
    ordering = ['tenant__name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
