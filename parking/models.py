from django.db import models
import uuid
import math
from django.utils import timezone
from datetime import timedelta
from io import BytesIO
from django.core.files import File
import barcode  # Asegúrate de que esta sea la librería correcta (python-barcode)
from barcode.writer import ImageWriter
import base64
from io import BytesIO
from barcode import Code128
from .managers import TenantManager, UserProfileManager
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# Modelo Tenant (Empresa) para multitenant
class Tenant(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre de la empresa")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Identificador único")
    nit = models.CharField(max_length=20, verbose_name="NIT")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generar slug automáticamente si no se proporciona
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# VehicleCategory se mantiene igual pero con relación a Tenant
class VehicleCategory(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    name = models.CharField(max_length=50, verbose_name="Nombre")
    first_hour_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Tarifa primera hora")
    additional_hour_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Tarifa hora adicional")
    is_monthly = models.BooleanField(default=False, verbose_name="Es mensual")
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Tarifa mensual")

    objects = TenantManager()

    class Meta:
        verbose_name = "Categoría de Vehículo"
        verbose_name_plural = "Categorías de Vehículos"
        unique_together = ['tenant', 'name']  # Una categoría por nombre por empresa

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"


# ParkingLot se mantiene igual pero con relación a Tenant
class ParkingLot(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    empresa = models.CharField(max_length=255, verbose_name="Nombre de la empresa")
    nit = models.CharField(max_length=20, verbose_name="NIT")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")

    objects = TenantManager()

    class Meta:
        verbose_name = "Parqueadero"
        verbose_name_plural = "Parqueaderos"

    def __str__(self):
        return f"{self.tenant.name} - {self.empresa}"


# ParkingTicket con mejoras y relación a Tenant
class ParkingTicket(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False)
    category = models.ForeignKey('VehicleCategory', on_delete=models.CASCADE, verbose_name="Categoría")
    placa = models.CharField(max_length=20, verbose_name="Placa")
    color = models.CharField(max_length=50, verbose_name="Color")
    marca = models.CharField(max_length=50, verbose_name="Marca")
    cascos = models.IntegerField(null=True, blank=True, verbose_name="Cascos")
    entry_time = models.DateTimeField(auto_now_add=True, verbose_name="Hora de entrada")
    exit_time = models.DateTimeField(null=True, blank=True, verbose_name="Hora de salida")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto pagado")
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto recibido")  # Nuevo
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Vuelto")  # Nuevo
    forma_pago = models.CharField(max_length=20, blank=True, null=True, verbose_name="Forma de pago")  # Nuevo campo
    barcode = models.ImageField(upload_to='barcodes/', blank=True, verbose_name="Código de barras")
    monthly_expiry = models.DateTimeField(null=True, blank=True, verbose_name="Vencimiento mensual")

    objects = TenantManager()

    class Meta:
        verbose_name = "Ticket de Parqueadero"
        verbose_name_plural = "Tickets de Parqueadero"
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'placa'],
                condition=models.Q(exit_time__isnull=True),
                name='unique_active_plate_per_tenant'
            )
        ]
        ordering = ['-entry_time']

    def __str__(self):
        return f"{self.tenant.name} - {self.placa} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"
    
    def get_barcode_base64(self):
        buffer = BytesIO()
        code = Code128(self.placa, writer=ImageWriter())
        code.write(buffer)
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f'data:image/png;base64,{base64_data}'

    def save(self, *args, **kwargs):
        # Generar el código de barras con la placa si no existe
        if not self.barcode:
            code = barcode.Code128(self.placa, writer=ImageWriter())  # Usar la placa en lugar de ticket_id
            buffer = BytesIO()
            code.write(buffer)
            self.barcode.save(
                f'barcode_{self.placa}.png',  # Nombrar el archivo con la placa
                File(buffer),
                save=False
            )
        # Asegurarse de que entry_time tenga un valor antes de calcular monthly_expiry
        if not self.entry_time:
            self.entry_time = timezone.now()
        # Si es categoría mensual y no tiene fecha de vencimiento, asignar un mes desde la entrada
        if self.category.is_monthly and not self.monthly_expiry:
            self.monthly_expiry = self.entry_time + timedelta(days=30)
        super().save(*args, **kwargs)

    def calculate_fee(self):
        if self.exit_time:
            if self.category.is_monthly and self.monthly_expiry and self.exit_time <= self.monthly_expiry:
                return float(self.category.monthly_rate)
            duration = self.exit_time - self.entry_time
            hours = duration.total_seconds() / 3600

            total = float(self.category.first_hour_rate)
            if hours > 1:
                additional_hours = math.ceil(hours - 1)
                total += additional_hours * float(self.category.additional_hour_rate)

            # Redondear SIEMPRE hacia arriba a la centena más cercana
            total = math.ceil(total / 100) * 100
            return float(total)
        return self.calculate_current_fee()

    def calculate_current_fee(self):
        if not self.exit_time:
            if self.category.is_monthly and self.monthly_expiry and timezone.now() <= self.monthly_expiry:
                return float(self.category.monthly_rate)
            duration = timezone.now() - self.entry_time
            hours = duration.total_seconds() / 3600

            total = float(self.category.first_hour_rate)
            if hours > 1:
                additional_hours = math.ceil(hours - 1)
                total += additional_hours * float(self.category.additional_hour_rate)

            # Redondear SIEMPRE hacia arriba a la centena más cercana
            total = math.ceil(total / 100) * 100
            return float(total)
        return 0

    def get_duration(self):
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            return math.ceil(duration.total_seconds() / 3600)
        return self.get_current_duration()['hours']

    def get_current_duration(self):
        if not self.exit_time:
            duration = timezone.now() - self.entry_time
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            return {'hours': int(hours), 'minutes': int(minutes)}
        return {'hours': 0, 'minutes': 0}

    def get_status(self):
        if not self.exit_time:
            duration = self.get_current_duration()
            current_fee = self.calculate_current_fee()
            monthly_status = None
            if self.category.is_monthly:
                monthly_status = 'Vigente' if timezone.now() <= self.monthly_expiry else 'Vencido'
            return {
                'duration': duration,
                'current_fee': current_fee,
                'is_active': True,
                'monthly_status': monthly_status
            }
        return {
            'duration': {'hours': 0, 'minutes': 0},
            'current_fee': self.amount_paid or 0,
            'is_active': False,
            'monthly_status': None
        }


# --- MODELOS MEJORADOS PARA CUADRE DE CAJA ---

class CajaTurno(models.Model):
    def diferencia_efectivo(self):
        """
        Devuelve la diferencia entre el efectivo contado y el esperado en efectivo.
        """
        if self.monto_real_contado is not None:
            return self.monto_real_contado - self.total_esperado_efectivo()
        return None
    ESTADO_CHOICES = [
        ("abierto", "Abierto"),
        ("cerrado", "Cerrado"),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    usuario_apertura = models.ForeignKey(User, on_delete=models.PROTECT, related_name="turnos_abiertos", verbose_name="Usuario apertura")
    usuario_cierre = models.ForeignKey(User, on_delete=models.PROTECT, related_name="turnos_cerrados", null=True, blank=True, verbose_name="Usuario cierre")
    fecha_apertura = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora de apertura")
    fecha_cierre = models.DateTimeField(null=True, blank=True, verbose_name="Fecha y hora de cierre")
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Fondo fijo inicial")
    monto_real_contado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto real contado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    firma_cierre = models.CharField(max_length=255, blank=True, null=True, verbose_name="Firma/confirmación de cierre")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default="abierto", verbose_name="Estado del turno")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Turno de Caja"
        verbose_name_plural = "Turnos de Caja"
        ordering = ["-fecha_apertura"]

    def __str__(self):
        return f"{self.tenant.name} - {self.usuario_apertura.username} - {self.fecha_apertura.strftime('%Y-%m-%d %H:%M')}"

    def total_ingresos(self):
        return self.movimientos.filter(tipo="Ingreso").aggregate(models.Sum("monto"))["monto__sum"] or 0

    def total_egresos(self):
        return self.movimientos.filter(tipo="Egreso").aggregate(models.Sum("monto"))["monto__sum"] or 0

    def total_esperado(self):
        return self.monto_inicial + self.total_ingresos() - self.total_egresos()

    def total_esperado_efectivo(self):
        ingresos_efectivo = self.movimientos.filter(tipo="Ingreso", forma_pago="efectivo").aggregate(models.Sum("monto"))["monto__sum"] or 0
        egresos_efectivo = self.movimientos.filter(tipo="Egreso", forma_pago="efectivo").aggregate(models.Sum("monto"))["monto__sum"] or 0
        return self.monto_inicial + ingresos_efectivo - egresos_efectivo

    def diferencia(self):
        if self.monto_real_contado is not None:
            return self.monto_real_contado - self.total_esperado()
        return None

    def exportar_pdf(self):
        # Aquí iría la lógica para exportar el cuadre a PDF (puede usarse ReportLab, xhtml2pdf, etc.)
        pass

    def alerta_diferencia(self, umbral=10000):
        # Retorna True si la diferencia supera el umbral (por ejemplo, $10.000)
        diff = self.diferencia()
        if diff is not None:
            return abs(diff) >= umbral
        return False

    def desglose_ingresos_por_forma_pago(self):
        from django.db.models import Sum
        formas = [c[0] for c in CajaMovimiento.FORMA_PAGO_CHOICES]
        resultado = {}
        for forma in formas:
            total = self.movimientos.filter(tipo="Ingreso", forma_pago=forma).aggregate(Sum("monto"))["monto__sum"] or 0
            resultado[forma] = total
        return resultado

class CajaMovimiento(models.Model):
    TIPO_CHOICES = [
        ("Ingreso", "Ingreso"),
        ("Egreso", "Egreso"),
    ]
    CATEGORIA_CHOICES = [
        ("parqueo", "Parqueo"),
        ("venta", "Venta de productos"),
        ("penalidad", "Penalidad"),
        ("compra", "Compra menor"),
        ("anticipo", "Anticipo"),
        ("devolucion", "Devolución"),
        ("otro", "Otro"),
    ]
    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("datafono", "Datáfono"),
        ("transferencia", "Transferencia"),
        ("otro", "Otro"),
    ]
    caja_turno = models.ForeignKey(CajaTurno, on_delete=models.CASCADE, related_name="movimientos", verbose_name="Turno de caja")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo de movimiento")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, verbose_name="Categoría")
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Monto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, verbose_name="Forma de pago")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Usuario")
    tipo_vehiculo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tipo de vehículo")

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.caja_turno} - {self.tipo} - {self.categoria} - ${self.monto}"

# --- FIN MODELOS MEJORADOS ---

# Modelo Caja anterior (deprecado, mantener por compatibilidad temporal)
# class Caja(models.Model):
#     ...
#     # Modelo anterior, ahora reemplazado por CajaTurno y CajaMovimiento
# ... existing code ...


# Modelo de Usuario personalizado con relación a Tenant
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa", null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrador'),
            ('cajero', 'Cajero'),
            ('operator', 'Operador'),
            ('viewer', 'Visualizador'),
        ],
        default='cajero',
        verbose_name="Rol"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    objects = UserProfileManager()

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="unique_user_per_tenant")
        ]

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "Sin empresa"
        return f"{self.user.username} - {tenant_name}"

    def has_permission(self, permission):
        """Verificar si el usuario tiene un permiso específico"""
        if self.role == 'admin':
            return True
        elif self.role == 'operator':
            # Los operadores pueden hacer todo excepto administrar usuarios
            return permission not in ['user_management']
        elif self.role == 'cajero':
            # Los cajeros pueden gestionar entradas/salidas y caja
            return permission in ['vehicle_entry', 'vehicle_exit', 'cash_management', 'view_reports', 'view_dashboard']
        elif self.role == 'viewer':
            # Los visualizadores solo pueden ver reportes
            return permission in ['view_reports', 'view_dashboard']
        return False

# --- SISTEMA DE ROLES Y PERMISOS PERSONALIZADOS ---

class Module(models.Model):
    """Modelo para definir los módulos del sistema"""
    name = models.CharField(max_length=100, verbose_name="Nombre del módulo")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código del módulo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icono")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.IntegerField(default=0, verbose_name="Orden")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_default_modules(cls):
        """Obtener los módulos por defecto del sistema"""
        default_modules = [
            {'name': 'Dashboard', 'code': 'dashboard', 'description': 'Panel principal del sistema', 'icon': 'fas fa-tachometer-alt', 'order': 1},
            {'name': 'Gestión de Vehículos', 'code': 'vehicle_management', 'description': 'Registro de entradas y salidas de vehículos', 'icon': 'fas fa-car', 'order': 2},
            {'name': 'Categorías de Vehículos', 'code': 'vehicle_categories', 'description': 'Administración de categorías y tarifas', 'icon': 'fas fa-tags', 'order': 3},
            {'name': 'Reportes', 'code': 'reports', 'description': 'Generación y visualización de reportes', 'icon': 'fas fa-chart-bar', 'order': 4},
            {'name': 'Cuadre de Caja', 'code': 'cash_management', 'description': 'Gestión de caja y movimientos', 'icon': 'fas fa-cash-register', 'order': 5},
            {'name': 'Historial de Movimientos', 'code': 'movement_history', 'description': 'Historial de transacciones', 'icon': 'fas fa-history', 'order': 6},
            {'name': 'Gestión de Usuarios', 'code': 'user_management', 'description': 'Administración de usuarios y roles', 'icon': 'fas fa-users', 'order': 7},
            {'name': 'Configuración', 'code': 'settings', 'description': 'Configuración general del sistema', 'icon': 'fas fa-cog', 'order': 8},
            {'name': 'Exportación de Datos', 'code': 'data_export', 'description': 'Exportación de reportes y datos', 'icon': 'fas fa-download', 'order': 9},
        ]
        return default_modules


class Permission(models.Model):
    """Modelo para definir permisos específicos dentro de los módulos"""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, verbose_name="Módulo")
    name = models.CharField(max_length=100, verbose_name="Nombre del permiso")
    code = models.CharField(max_length=50, verbose_name="Código del permiso")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        unique_together = ['module', 'code']
        ordering = ['module__order', 'name']

    def __str__(self):
        return f"{self.module.name} - {self.name}"

    @classmethod
    def get_default_permissions(cls):
        """Obtener los permisos por defecto del sistema"""
        default_permissions = [
            # Dashboard
            {'module_code': 'dashboard', 'name': 'Ver Dashboard', 'code': 'view_dashboard'},
            
            # Gestión de Vehículos
            {'module_code': 'vehicle_management', 'name': 'Registrar Entrada', 'code': 'vehicle_entry'},
            {'module_code': 'vehicle_management', 'name': 'Registrar Salida', 'code': 'vehicle_exit'},
            {'module_code': 'vehicle_management', 'name': 'Imprimir Tickets', 'code': 'print_tickets'},
            
            # Categorías de Vehículos
            {'module_code': 'vehicle_categories', 'name': 'Ver Categorías', 'code': 'view_categories'},
            {'module_code': 'vehicle_categories', 'name': 'Crear Categorías', 'code': 'create_categories'},
            {'module_code': 'vehicle_categories', 'name': 'Editar Categorías', 'code': 'edit_categories'},
            {'module_code': 'vehicle_categories', 'name': 'Eliminar Categorías', 'code': 'delete_categories'},
            
            # Reportes
            {'module_code': 'reports', 'name': 'Ver Reportes', 'code': 'view_reports'},
            {'module_code': 'reports', 'name': 'Exportar Reportes', 'code': 'export_reports'},
            
            # Cuadre de Caja
            {'module_code': 'cash_management', 'name': 'Abrir Turno', 'code': 'open_shift'},
            {'module_code': 'cash_management', 'name': 'Cerrar Turno', 'code': 'close_shift'},
            {'module_code': 'cash_management', 'name': 'Registrar Movimientos', 'code': 'register_movements'},
            {'module_code': 'cash_management', 'name': 'Ver Historial', 'code': 'view_cash_history'},
            
            # Historial de Movimientos
            {'module_code': 'movement_history', 'name': 'Ver Historial', 'code': 'view_movement_history'},
            {'module_code': 'movement_history', 'name': 'Exportar Historial', 'code': 'export_movement_history'},
            
            # Gestión de Usuarios
            {'module_code': 'user_management', 'name': 'Ver Usuarios', 'code': 'view_users'},
            {'module_code': 'user_management', 'name': 'Crear Usuarios', 'code': 'create_users'},
            {'module_code': 'user_management', 'name': 'Editar Usuarios', 'code': 'edit_users'},
            {'module_code': 'user_management', 'name': 'Eliminar Usuarios', 'code': 'delete_users'},
            {'module_code': 'user_management', 'name': 'Gestionar Roles', 'code': 'manage_roles'},
            
            # Configuración
            {'module_code': 'settings', 'name': 'Ver Configuración', 'code': 'view_settings'},
            {'module_code': 'settings', 'name': 'Editar Configuración', 'code': 'edit_settings'},
            
            # Exportación de Datos
            {'module_code': 'data_export', 'name': 'Exportar Datos', 'code': 'export_data'},
        ]
        return default_permissions


class CustomRole(models.Model):
    """Modelo para roles personalizados"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    name = models.CharField(max_length=100, verbose_name="Nombre del rol")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_system = models.BooleanField(default=False, verbose_name="Rol del sistema")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Rol Personalizado"
        verbose_name_plural = "Roles Personalizados"
        unique_together = ['tenant', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    @classmethod
    def create_default_roles(cls, tenant):
        """Crear roles por defecto para un tenant"""
        default_roles = [
            {
                'name': 'Administrador',
                'description': 'Acceso completo a todas las funcionalidades del sistema',
                'is_system': True,
                'permissions': ['*']  # Todos los permisos
            },
            {
                'name': 'Cajero',
                'description': 'Gestión de entradas/salidas y caja',
                'is_system': True,
                'permissions': [
                    'view_dashboard', 'vehicle_entry', 'vehicle_exit', 'print_tickets',
                    'view_categories', 'view_reports', 'export_reports',
                    'open_shift', 'close_shift', 'register_movements', 'view_cash_history',
                    'view_movement_history', 'export_movement_history'
                ]
            },
            {
                'name': 'Operador',
                'description': 'Operaciones básicas del sistema',
                'is_system': True,
                'permissions': [
                    'view_dashboard', 'vehicle_entry', 'vehicle_exit', 'print_tickets',
                    'view_categories', 'view_reports', 'view_movement_history'
                ]
            },
            {
                'name': 'Visualizador',
                'description': 'Solo visualización de reportes y dashboard',
                'is_system': True,
                'permissions': [
                    'view_dashboard', 'view_reports', 'view_movement_history'
                ]
            }
        ]
        
        for role_data in default_roles:
            role, created = cls.objects.get_or_create(
                tenant=tenant,
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system': role_data['is_system'],
                    'is_active': True
                }
            )
            
            if created:
                # Asignar permisos al rol
                if role_data['permissions'] == ['*']:
                    # Todos los permisos
                    permissions = Permission.objects.filter(is_active=True)
                else:
                    # Permisos específicos
                    permissions = Permission.objects.filter(
                        code__in=role_data['permissions'],
                        is_active=True
                    )
                
                for permission in permissions:
                    RolePermission.objects.create(role=role, permission=permission)


class RolePermission(models.Model):
    """Modelo para relacionar roles con permisos"""
    role = models.ForeignKey(CustomRole, on_delete=models.CASCADE, verbose_name="Rol")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="Permiso")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Permiso de Rol"
        verbose_name_plural = "Permisos de Roles"
        unique_together = ['role', 'permission']
        ordering = ['role__name', 'permission__module__order', 'permission__name']

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserRole(models.Model):
    """Modelo para relacionar usuarios con roles"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Perfil de Usuario")
    role = models.ForeignKey(CustomRole, on_delete=models.CASCADE, verbose_name="Rol")
    is_primary = models.BooleanField(default=False, verbose_name="Rol principal")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Rol de Usuario"
        verbose_name_plural = "Roles de Usuario"
        unique_together = ['user_profile', 'role']
        ordering = ['-is_primary', 'role__name']

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.role.name}"


class UserPermission(models.Model):
    """Modelo para permisos específicos de usuario (sobre-escritura de roles)"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Perfil de Usuario")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="Permiso")
    is_granted = models.BooleanField(default=True, verbose_name="Permitido")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Permiso de Usuario"
        verbose_name_plural = "Permisos de Usuario"
        unique_together = ['user_profile', 'permission']
        ordering = ['permission__module__order', 'permission__name']

    def __str__(self):
        status = "Permitido" if self.is_granted else "Denegado"
        return f"{self.user_profile.user.username} - {self.permission.name} ({status})"


class AccessLog(models.Model):
    """Modelo para bitácora de acceso y cambios de permisos"""
    ACTION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('permission_change', 'Cambio de permisos'),
        ('role_assignment', 'Asignación de rol'),
        ('user_creation', 'Creación de usuario'),
        ('user_edit', 'Edición de usuario'),
        ('user_deletion', 'Eliminación de usuario'),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Usuario")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="Acción")
    details = models.TextField(blank=True, verbose_name="Detalles")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Bitácora de Acceso"
        verbose_name_plural = "Bitácoras de Acceso"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at}"


# Extender el modelo UserProfile existente
def userprofile_has_permission(self, permission_code):
    """Verificar si el usuario tiene un permiso específico"""
    try:
        # Verificar permisos específicos del usuario (sobre-escritura)
        user_permission = UserPermission.objects.get(
            user_profile=self,
            permission__code=permission_code
        )
        return user_permission.is_granted
    except UserPermission.DoesNotExist:
        # Verificar permisos a través de roles
        user_roles = UserRole.objects.filter(
            user_profile=self,
            role__is_active=True
        ).prefetch_related('role__rolepermission_set__permission')
        
        for user_role in user_roles:
            role_permissions = user_role.role.rolepermission_set.filter(
                permission__code=permission_code,
                permission__is_active=True
            )
            if role_permissions.exists():
                return True
        
        return False


def userprofile_get_permissions(self):
    """Obtener todos los permisos del usuario"""
    permissions = set()
    
    # Obtener permisos de roles
    user_roles = UserRole.objects.filter(
        user_profile=self,
        role__is_active=True
    ).prefetch_related('role__rolepermission_set__permission')
    
    for user_role in user_roles:
        role_permissions = user_role.role.rolepermission_set.filter(
            permission__is_active=True
        ).select_related('permission')
        
        for role_permission in role_permissions:
            permissions.add(role_permission.permission.code)
    
    # Aplicar sobre-escrituras de permisos específicos
    user_permissions = UserPermission.objects.filter(
        user_profile=self
    ).select_related('permission')
    
    for user_permission in user_permissions:
        if user_permission.is_granted:
            permissions.add(user_permission.permission.code)
        else:
            permissions.discard(user_permission.permission.code)
    
    return list(permissions)


def userprofile_get_modules(self):
    """Obtener módulos a los que tiene acceso el usuario"""
    permissions = self.get_permissions()
    modules = Module.objects.filter(
        permission__code__in=permissions,
        is_active=True
    ).distinct().order_by('order')
    
    return modules


def userprofile_get_roles(self):
    """Obtener roles del usuario"""
    return UserRole.objects.filter(
        user_profile=self,
        role__is_active=True
    ).select_related('role')


def userprofile_get_primary_role(self):
    """Obtener el rol principal del usuario"""
    try:
        return UserRole.objects.get(
            user_profile=self,
            is_primary=True,
            role__is_active=True
        ).role
    except UserRole.DoesNotExist:
        return None


# Agregar métodos al modelo UserProfile existente
UserProfile.has_permission = userprofile_has_permission
UserProfile.get_permissions = userprofile_get_permissions
UserProfile.get_modules = userprofile_get_modules
UserProfile.get_roles = userprofile_get_roles
UserProfile.get_primary_role = userprofile_get_primary_role

# =============================================================================
# MODELOS DE CONFIGURACIÓN DEL SISTEMA
# =============================================================================

class Currency(models.Model):
    """Modelo para configurar monedas por tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    name = models.CharField(max_length=50, verbose_name="Nombre de la moneda")
    code = models.CharField(max_length=10, verbose_name="Código de la moneda")  # USD, COP, PEN, etc.
    symbol = models.CharField(max_length=5, verbose_name="Símbolo")  # $, S/, etc.
    decimal_places = models.IntegerField(default=2, verbose_name="Decimales")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_default = models.BooleanField(default=False, verbose_name="Moneda por defecto")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    objects = TenantManager()

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        unique_together = ['tenant', 'code']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    def save(self, *args, **kwargs):
        # Si se marca como default, desmarcar las demás del mismo tenant
        if self.is_default:
            Currency.objects.filter(tenant=self.tenant, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_currencies(cls):
        """Obtener monedas por defecto del sistema"""
        return [
            {'name': 'Peso Colombiano', 'code': 'COP', 'symbol': '$', 'decimal_places': 0},
            {'name': 'Dólar Americano', 'code': 'USD', 'symbol': '$', 'decimal_places': 2},
            {'name': 'Sol Peruano', 'code': 'PEN', 'symbol': 'S/', 'decimal_places': 2},
            {'name': 'Euro', 'code': 'EUR', 'symbol': '€', 'decimal_places': 2},
            {'name': 'Peso Mexicano', 'code': 'MXN', 'symbol': '$', 'decimal_places': 2},
            {'name': 'Peso Argentino', 'code': 'ARS', 'symbol': '$', 'decimal_places': 2},
        ]

    def format_amount(self, amount, use_tenant_separators=True):
        """Formatear un monto según la configuración de la moneda y tenant"""
        try:
            if use_tenant_separators:
                # Intentar usar los separadores configurados del tenant
                config = self.tenant.tenantconfiguration
                thousand_sep = config.thousand_separator
                decimal_sep = config.decimal_separator
                
                # Formatear el número
                if self.decimal_places == 0:
                    # Sin decimales
                    formatted_number = f"{amount:,.0f}".replace(',', thousand_sep)
                else:
                    # Con decimales
                    formatted_number = f"{amount:,.{self.decimal_places}f}"
                    # Reemplazar separadores
                    formatted_number = formatted_number.replace(',', '|TEMP|')  # Temporal
                    formatted_number = formatted_number.replace('.', decimal_sep)
                    formatted_number = formatted_number.replace('|TEMP|', thousand_sep)
                
                return f"{self.symbol}{formatted_number}"
            else:
                # Formato estándar
                if self.decimal_places == 0:
                    return f"{self.symbol}{amount:,.0f}"
                else:
                    return f"{self.symbol}{amount:,.{self.decimal_places}f}"
        except:
            # Fallback al formato estándar
            if self.decimal_places == 0:
                return f"{self.symbol}{amount:,.0f}"
            else:
                return f"{self.symbol}{amount:,.{self.decimal_places}f}"


class TaxType(models.Model):
    """Modelo para configurar tipos de impuestos por tenant"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    name = models.CharField(max_length=50, verbose_name="Nombre del impuesto")
    code = models.CharField(max_length=10, verbose_name="Código del impuesto")  # IVA, IGV, VAT, etc.
    rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Porcentaje")  # 19.00 para 19%
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_default = models.BooleanField(default=False, verbose_name="Impuesto por defecto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    objects = TenantManager()

    class Meta:
        verbose_name = "Tipo de Impuesto"
        verbose_name_plural = "Tipos de Impuestos"
        unique_together = ['tenant', 'code']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def save(self, *args, **kwargs):
        # Si se marca como default, desmarcar los demás del mismo tenant
        if self.is_default:
            TaxType.objects.filter(tenant=self.tenant, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_tax_types(cls):
        """Obtener tipos de impuestos por defecto del sistema"""
        return [
            {'name': 'IVA Colombia', 'code': 'IVA', 'rate': 19.00, 'description': 'Impuesto al Valor Agregado - Colombia'},
            {'name': 'IGV Perú', 'code': 'IGV', 'rate': 18.00, 'description': 'Impuesto General a las Ventas - Perú'},
            {'name': 'IVA México', 'code': 'IVA', 'rate': 16.00, 'description': 'Impuesto al Valor Agregado - México'},
            {'name': 'IVA Argentina', 'code': 'IVA', 'rate': 21.00, 'description': 'Impuesto al Valor Agregado - Argentina'},
            {'name': 'VAT España', 'code': 'VAT', 'rate': 21.00, 'description': 'Value Added Tax - España'},
        ]

    def calculate_tax(self, base_amount):
        """Calcular el impuesto sobre un monto base"""
        return base_amount * (self.rate / 100)

    def calculate_total_with_tax(self, base_amount):
        """Calcular el total incluyendo impuesto"""
        return base_amount + self.calculate_tax(base_amount)

    def calculate_base_from_total(self, total_amount):
        """
        Calcular el monto base desde el total (método colombiano)
        Si el total es 5000 y el impuesto es 19%:
        Base = 5000 / 1.19 = 4201.68
        """
        tax_factor = 1 + (float(self.rate) / 100)
        return total_amount / tax_factor

    def calculate_tax_from_total(self, total_amount):
        """
        Calcular el impuesto desde el total
        Si el total es 5000 y el impuesto es 19%:
        Impuesto = 5000 - (5000 / 1.19) = 798.32
        """
        base_amount = self.calculate_base_from_total(total_amount)
        return total_amount - base_amount

    def get_tax_breakdown_from_total(self, total_amount):
        """Obtener desglose completo desde el total"""
        base_amount = self.calculate_base_from_total(total_amount)
        tax_amount = self.calculate_tax_from_total(total_amount)
        
        return {
            'base_amount': round(base_amount, 2),
            'tax_name': self.name,
            'tax_code': self.code,
            'tax_rate': float(self.rate),
            'tax_amount': round(tax_amount, 2),
            'total_amount': total_amount,
            'tax_factor': 1 + (float(self.rate) / 100)
        }


class TenantConfiguration(models.Model):
    """Modelo para configuraciones generales del tenant"""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Configuración de moneda
    default_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Moneda por defecto")
    
    # Configuración de impuestos
    default_tax_type = models.ForeignKey(TaxType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Impuesto por defecto")
    apply_tax_by_default = models.BooleanField(default=False, verbose_name="Aplicar impuesto por defecto")
    
    # Configuración de tickets
    include_tax_in_ticket = models.BooleanField(default=False, verbose_name="Incluir impuesto en ticket")
    show_tax_breakdown = models.BooleanField(default=True, verbose_name="Mostrar desglose de impuesto")
    
    # Configuración de formato de números
    thousand_separator = models.CharField(max_length=1, default='.', verbose_name="Separador de miles")
    decimal_separator = models.CharField(max_length=1, default=',', verbose_name="Separador decimal")
    
    # Configuración de la empresa
    company_logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo de la empresa")
    receipt_footer_text = models.TextField(blank=True, verbose_name="Texto pie de página en recibos")
    
    # Configuración de zona horaria
    timezone = models.CharField(max_length=50, default='America/Bogota', verbose_name="Zona horaria")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresa"

    def __str__(self):
        return f"Configuración - {self.tenant.name}"

    def get_currency_symbol(self):
        """Obtener el símbolo de la moneda por defecto"""
        if self.default_currency:
            return self.default_currency.symbol
        return '$'  # Símbolo por defecto

    def format_amount(self, amount):
        """Formatear un monto según la configuración"""
        if self.default_currency:
            return self.default_currency.format_amount(amount)
        return f"${amount:,.2f}"

    def calculate_with_tax(self, base_amount):
        """Calcular monto con impuesto si está configurado"""
        if self.apply_tax_by_default and self.default_tax_type:
            return self.default_tax_type.calculate_total_with_tax(base_amount)
        return base_amount

    def get_tax_info(self, base_amount):
        """Obtener información detallada del impuesto"""
        if self.apply_tax_by_default and self.default_tax_type:
            tax_amount = self.default_tax_type.calculate_tax(base_amount)
            total_amount = base_amount + tax_amount
            return {
                'base_amount': base_amount,
                'tax_name': self.default_tax_type.name,
                'tax_rate': self.default_tax_type.rate,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'has_tax': True
            }
        return {
            'base_amount': base_amount,
            'tax_name': None,
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': base_amount,
            'has_tax': False
        }

    def calculate_tax_breakdown_from_total(self, total_amount):
        """
        Calcular desglose de impuesto desde el total (método colombiano)
        Si el total es 5000 y el impuesto es 19%, entonces:
        - Subtotal = 5000 / 1.19 = 4201.68
        - Impuesto = 5000 - 4201.68 = 798.32
        """
        if self.apply_tax_by_default and self.default_tax_type:
            tax_rate = float(self.default_tax_type.rate)
            tax_factor = 1 + (tax_rate / 100)  # 1.19 para 19%
            
            subtotal = total_amount / tax_factor
            tax_amount = total_amount - subtotal
            
            return {
                'subtotal': round(subtotal, 2),
                'tax_name': self.default_tax_type.name,
                'tax_rate': tax_rate,
                'tax_amount': round(tax_amount, 2),
                'total_amount': total_amount,
                'has_tax': True,
                'tax_factor': tax_factor
            }
        return {
            'subtotal': total_amount,
            'tax_name': None,
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': total_amount,
            'has_tax': False,
            'tax_factor': 1
        }


# =============================================================================
# EXTENSIONES A MODELOS EXISTENTES
# =============================================================================

# Agregar métodos helper al modelo VehicleCategory para manejar impuestos
def vehiclecategory_calculate_rate_with_tax(self, rate_type='first_hour'):
    """Calcular tarifa con impuesto si está configurado"""
    try:
        config = self.tenant.tenantconfiguration
        if rate_type == 'first_hour':
            base_rate = self.first_hour_rate
        elif rate_type == 'additional_hour':
            base_rate = self.additional_hour_rate
        elif rate_type == 'monthly':
            base_rate = self.monthly_rate or 0
        else:
            base_rate = self.first_hour_rate
        
        return config.calculate_with_tax(base_rate)
    except:
        # Si no hay configuración, devolver la tarifa base
        if rate_type == 'first_hour':
            return self.first_hour_rate
        elif rate_type == 'additional_hour':
            return self.additional_hour_rate
        elif rate_type == 'monthly':
            return self.monthly_rate or 0
        else:
            return self.first_hour_rate

def vehiclecategory_get_formatted_rate(self, rate_type='first_hour'):
    """Obtener tarifa formateada con moneda"""
    try:
        config = self.tenant.tenantconfiguration
        rate = self.calculate_rate_with_tax(rate_type)
        return config.format_amount(rate)
    except:
        # Formato por defecto
        if rate_type == 'first_hour':
            return f"${self.first_hour_rate:,.0f}"
        elif rate_type == 'additional_hour':
            return f"${self.additional_hour_rate:,.0f}"
        elif rate_type == 'monthly':
            return f"${self.monthly_rate or 0:,.0f}"
        else:
            return f"${self.first_hour_rate:,.0f}"

# Agregar métodos a VehicleCategory
VehicleCategory.calculate_rate_with_tax = vehiclecategory_calculate_rate_with_tax
VehicleCategory.get_formatted_rate = vehiclecategory_get_formatted_rate


# Agregar métodos helper al modelo ParkingTicket para manejar impuestos
def parkingticket_calculate_fee_with_tax(self):
    """Calcular tarifa con impuesto"""
    base_fee = self.calculate_fee()
    try:
        config = self.tenant.tenantconfiguration
        return config.calculate_with_tax(base_fee)
    except:
        return base_fee

def parkingticket_get_fee_breakdown(self):
    """Obtener desglose detallado de la tarifa"""
    total_fee = self.calculate_fee()  # Este es el total que debe pagar
    try:
        config = self.tenant.tenantconfiguration
        if config.apply_tax_by_default and config.default_tax_type:
            # Usar el método colombiano: dividir el total entre el factor de impuesto
            return config.calculate_tax_breakdown_from_total(total_fee)
        else:
            return {
                'subtotal': total_fee,
                'tax_name': None,
                'tax_rate': 0,
                'tax_amount': 0,
                'total_amount': total_fee,
                'has_tax': False,
                'tax_factor': 1
            }
    except:
        return {
            'subtotal': total_fee,
            'tax_name': None,
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': total_fee,
            'has_tax': False,
            'tax_factor': 1
        }

def parkingticket_get_formatted_fee(self):
    """Obtener tarifa formateada con moneda"""
    fee = self.calculate_fee()  # Total a pagar
    try:
        config = self.tenant.tenantconfiguration
        if config.default_currency:
            return config.default_currency.format_amount(fee)
        else:
            return f"${fee:,.0f}"
    except:
        return f"${fee:,.0f}"

def parkingticket_get_formatted_breakdown(self):
    """Obtener desglose formateado de la tarifa"""
    breakdown = self.get_fee_breakdown()
    try:
        config = self.tenant.tenantconfiguration
        currency = config.default_currency
        
        if currency:
            result = {
                'subtotal_formatted': currency.format_amount(breakdown['subtotal']),
                'tax_amount_formatted': currency.format_amount(breakdown['tax_amount']),
                'total_formatted': currency.format_amount(breakdown['total_amount']),
                'currency_symbol': currency.symbol,
                **breakdown  # Incluir todos los datos originales
            }
        else:
            result = {
                'subtotal_formatted': f"${breakdown['subtotal']:,.0f}",
                'tax_amount_formatted': f"${breakdown['tax_amount']:,.0f}",
                'total_formatted': f"${breakdown['total_amount']:,.0f}",
                'currency_symbol': '$',
                **breakdown
            }
        
        return result
    except:
        return {
            'subtotal_formatted': f"${breakdown['subtotal']:,.0f}",
            'tax_amount_formatted': f"${breakdown['tax_amount']:,.0f}",
            'total_formatted': f"${breakdown['total_amount']:,.0f}",
            'currency_symbol': '$',
            **breakdown
        }

# Agregar métodos a ParkingTicket
ParkingTicket.calculate_fee_with_tax = parkingticket_calculate_fee_with_tax
ParkingTicket.get_fee_breakdown = parkingticket_get_fee_breakdown
ParkingTicket.get_formatted_fee = parkingticket_get_formatted_fee
ParkingTicket.get_formatted_breakdown = parkingticket_get_formatted_breakdown

