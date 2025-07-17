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