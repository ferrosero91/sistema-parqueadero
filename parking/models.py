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


# VehicleCategory se mantiene igual
class VehicleCategory(models.Model):
    name = models.CharField(max_length=50)
    first_hour_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    additional_hour_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    is_monthly = models.BooleanField(default=False)
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Vehicle Categories"

# ParkingLot se mantiene igual
class ParkingLot(models.Model):
    empresa = models.CharField(max_length=255)
    nit = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)

    def __str__(self):
        return self.empresa

# ParkingTicket con mejoras
class ParkingTicket(models.Model):
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False)
    category = models.ForeignKey('VehicleCategory', on_delete=models.CASCADE)
    placa = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    cascos = models.IntegerField(null=True, blank=True)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    barcode = models.ImageField(upload_to='barcodes/', blank=True)
    monthly_expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['placa'],
                condition=models.Q(exit_time__isnull=True),
                name='unique_active_plate'
            )
        ]

    def __str__(self):
        return f"{self.placa} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"
    
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

    """
    def generate_barcode_image(self):
        buffer = BytesIO()
        code = Code128(self.placa, writer=ImageWriter())
        code.write(buffer)
        buffer.seek(0)
        return ContentFile(buffer.read(), name=f'barcode_{self.placa}.png')
    """
    

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

            return round(total, 2)
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

            return round(total, 2)
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

# Al final del archivo, añade el modelo Caja si no está


class Caja(models.Model):
    fecha = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=50, choices=[('Ingreso', 'Ingreso'), ('Egreso', 'Egreso')])
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descripcion = models.TextField(blank=True)
    dinero_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    dinero_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cuadre_realizado = models.BooleanField(default=False)

    class Meta:
        unique_together = ('fecha', 'tipo')  # Asegura que la combinación de fecha y tipo sea única

    def __str__(self):
        return f"{self.fecha} - {self.tipo} - ${self.monto}"