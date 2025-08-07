from django import forms
from .models import Currency, TaxType, TenantConfiguration, VehicleCategory


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['name', 'code', 'symbol', 'decimal_places', 'is_active', 'is_default']
        labels = {
            'name': 'Nombre de la moneda',
            'code': 'Código (ISO)',
            'symbol': 'Símbolo',
            'decimal_places': 'Decimales',
            'is_active': 'Activa',
            'is_default': 'Moneda por defecto',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: Peso Colombiano'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: COP',
                'maxlength': '10'
            }),
            'symbol': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: $',
                'maxlength': '5'
            }),
            'decimal_places': forms.NumberInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'min': '0',
                'max': '4'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'instance') and hasattr(self.instance, 'tenant'):
            instance.tenant = self.instance.tenant
        if commit:
            instance.save()
        return instance


class TaxTypeForm(forms.ModelForm):
    class Meta:
        model = TaxType
        fields = ['name', 'code', 'rate', 'description', 'is_active', 'is_default']
        labels = {
            'name': 'Nombre del impuesto',
            'code': 'Código',
            'rate': 'Porcentaje (%)',
            'description': 'Descripción',
            'is_active': 'Activo',
            'is_default': 'Impuesto por defecto',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: IVA Colombia'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: IVA',
                'maxlength': '10'
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '19.00'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'rows': '3',
                'placeholder': 'Descripción del impuesto'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
        return code

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'instance') and hasattr(self.instance, 'tenant'):
            instance.tenant = self.instance.tenant
        if commit:
            instance.save()
        return instance


class TenantConfigurationForm(forms.ModelForm):
    class Meta:
        model = TenantConfiguration
        fields = [
            'default_currency', 'default_tax_type', 'apply_tax_by_default',
            'include_tax_in_ticket', 'show_tax_breakdown',
            'thousand_separator', 'decimal_separator',
            'company_logo', 'receipt_footer_text', 'timezone'
        ]
        labels = {
            'default_currency': 'Moneda por defecto',
            'default_tax_type': 'Impuesto por defecto',
            'apply_tax_by_default': 'Aplicar impuesto por defecto',
            'include_tax_in_ticket': 'Incluir impuesto en ticket',
            'show_tax_breakdown': 'Mostrar desglose de impuesto',
            'thousand_separator': 'Separador de miles',
            'decimal_separator': 'Separador decimal',
            'company_logo': 'Logo de la empresa',
            'receipt_footer_text': 'Texto pie de página',
            'timezone': 'Zona horaria',
        }
        widgets = {
            'default_currency': forms.Select(attrs={
                'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
            }),
            'default_tax_type': forms.Select(attrs={
                'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
            }),
            'apply_tax_by_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'include_tax_in_ticket': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'show_tax_breakdown': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'thousand_separator': forms.Select(choices=[
                ('.', 'Punto (.)'),
                (',', 'Coma (,)'),
                (' ', 'Espacio ( )'),
            ], attrs={
                'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
            }),
            'decimal_separator': forms.Select(choices=[
                (',', 'Coma (,)'),
                ('.', 'Punto (.)'),
            ], attrs={
                'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
            }),
            'company_logo': forms.FileInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'accept': 'image/*'
            }),
            'receipt_footer_text': forms.Textarea(attrs={
                'class': 'form-textarea block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'rows': '3',
                'placeholder': 'Texto que aparecerá en el pie de página de los recibos'
            }),
            'timezone': forms.Select(choices=[
                ('America/Bogota', 'Colombia (UTC-5)'),
                ('America/Lima', 'Perú (UTC-5)'),
                ('America/Mexico_City', 'México (UTC-6)'),
                ('America/Argentina/Buenos_Aires', 'Argentina (UTC-3)'),
                ('Europe/Madrid', 'España (UTC+1)'),
                ('America/New_York', 'Estados Unidos Este (UTC-5)'),
                ('America/Los_Angeles', 'Estados Unidos Oeste (UTC-8)'),
            ], attrs={
                'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant
            # Filtrar opciones por tenant
            self.fields['default_currency'].queryset = Currency.objects.filter(tenant=tenant, is_active=True)
            self.fields['default_tax_type'].queryset = TaxType.objects.filter(tenant=tenant, is_active=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'instance') and hasattr(self.instance, 'tenant'):
            instance.tenant = self.instance.tenant
        if commit:
            instance.save()
        return instance


class QuickSetupForm(forms.Form):
    """Formulario para configuración rápida inicial"""
    
    # Configuración de moneda
    currency_choice = forms.ChoiceField(
        label="Seleccionar moneda",
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
        })
    )
    
    # Configuración de impuesto
    tax_choice = forms.ChoiceField(
        label="Seleccionar impuesto",
        choices=[],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200'
        })
    )
    
    apply_tax = forms.BooleanField(
        label="Aplicar impuesto por defecto",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Opciones de moneda
        currency_choices = [('', 'Seleccionar moneda')] + [
            (f"{curr['code']}", f"{curr['name']} ({curr['symbol']})")
            for curr in Currency.get_default_currencies()
        ]
        self.fields['currency_choice'].choices = currency_choices
        
        # Opciones de impuesto
        tax_choices = [('', 'Sin impuesto')] + [
            (f"{tax['code']}_{tax['rate']}", f"{tax['name']} ({tax['rate']}%)")
            for tax in TaxType.get_default_tax_types()
        ]
        self.fields['tax_choice'].choices = tax_choices



