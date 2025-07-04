from django import forms
from .models import ParkingTicket, ParkingLot, VehicleCategory


class ParkingTicketForm(forms.ModelForm):
    class Meta:
        model = ParkingTicket
        fields = ['category', 'placa', 'color', 'marca', 'cascos']
        labels = {
            'category': 'Categoría',
            'placa': 'Placa',
            'color': 'Color',
            'marca': 'Marca',
            'cascos': 'Número de cascos',
        }
        widgets = {
            'placa': forms.TextInput(attrs={'class': 'uppercase'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer color, marca y cascos opcionales
        self.fields['color'].required = False
        self.fields['marca'].required = False
        self.fields['cascos'].required = False

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        cascos = cleaned_data.get('cascos')

        # Si es categoría MOTOS, validar cascos
        if category and category.name.upper() == 'MOTOS':
            if cascos is None:
                self.add_error('cascos', 'El número de cascos es obligatorio para motos')
        
        return cleaned_data


class ParkingLotForm(forms.ModelForm):
    class Meta:
        model = ParkingLot
        fields = ['empresa', 'nit', 'telefono', 'direccion']
        labels = {
            'empresa': 'Nombre de la empresa',
            'nit': 'NIT',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = VehicleCategory
        fields = ['name', 'first_hour_rate', 'additional_hour_rate', 'is_monthly', 'monthly_rate']
        labels = {
            'name': 'Nombre',
            'first_hour_rate': 'Tarifa primera hora',
            'additional_hour_rate': 'Tarifa hora adicional',
            'is_monthly': '¿Es mensual?',
            'monthly_rate': 'Tarifa mensual',
        }
        widgets = {
            'first_hour_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'additional_hour_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'monthly_rate': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_monthly = cleaned_data.get('is_monthly')
        monthly_rate = cleaned_data.get('monthly_rate')

        # Validar que si es mensual, se especifique una tarifa mensual
        if is_monthly and (monthly_rate is None or monthly_rate <= 0):
            self.add_error('monthly_rate', 'Debe especificar una tarifa mensual válida para una categoría mensual.')
        
        return cleaned_data