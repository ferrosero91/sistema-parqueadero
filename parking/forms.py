from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import VehicleCategory, ParkingTicket, Tenant, UserProfile, ParkingLot, CajaTurno, CajaMovimiento, CustomRole, RolePermission, UserRole, Module, Permission, UserPermission


class TenantLoginForm(AuthenticationForm):
    """
    Formulario de login personalizado que usa email y contraseña
    """
    username = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese su correo electrónico'
        })
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese su contraseña'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')  # El campo se llama username pero contiene el email
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                # Buscar el usuario por email
                user_profile = UserProfile.objects.select_related('user', 'tenant').get(
                    user__email=email,
                    is_active=True,
                    tenant__is_active=True
                )
                user = user_profile.user
                tenant = user_profile.tenant
                
                # Verificar la contraseña
                if not user.check_password(password):
                    raise self.get_invalid_login_error()
                
                # Confirmar que el usuario está activo
                self.confirm_login_allowed(user)
                
                # Agregar el tenant y user al cleaned_data
                self.cleaned_data['tenant'] = tenant
                self.cleaned_data['user'] = user
                
                return self.cleaned_data
                
            except UserProfile.DoesNotExist:
                raise self.get_invalid_login_error()
            except UserProfile.MultipleObjectsReturned:
                raise forms.ValidationError("Error: Múltiples usuarios encontrados con este correo")

        return self.cleaned_data


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
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'placeholder': 'Ej: Motos, Carros, Camiones'
            }),
            'first_hour_rate': forms.NumberInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'additional_hour_rate': forms.NumberInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'is_monthly': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'monthly_rate': forms.NumberInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant

    def clean(self):
        cleaned_data = super().clean()
        is_monthly = cleaned_data.get('is_monthly')
        monthly_rate = cleaned_data.get('monthly_rate')

        # Validar que si es mensual, se especifique una tarifa
        if is_monthly and not monthly_rate:
            raise forms.ValidationError("Debe especificar una tarifa mensual para categorías mensuales")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'instance') and hasattr(self.instance, 'tenant'):
            instance.tenant = self.instance.tenant
        if commit:
            instance.save()
        return instance


class ParkingTicketForm(forms.ModelForm):
    class Meta:
        model = ParkingTicket
        fields = ['category', 'placa', 'color', 'marca', 'cascos']
        labels = {
            'category': 'Categoría',
            'placa': 'Placa',
            'color': 'Color (opcional)',
            'marca': 'Marca (opcional)',
            'cascos': 'Número de cascos (opcional)',
        }
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Seleccione una categoría'
            }),
            'placa': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm uppercase',
                'placeholder': 'Ingrese la placa del vehículo'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el color del vehículo (opcional)'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese la marca del vehículo (opcional)'
            }),
            'cascos': forms.NumberInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el número de cascos (opcional)',
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            # Filtrar categorías por tenant
            self.fields['category'].queryset = VehicleCategory.objects.filter(tenant=tenant)
            self.instance.tenant = tenant
        
        # Hacer los campos opcionales
        self.fields['color'].required = False
        self.fields['marca'].required = False
        self.fields['cascos'].required = False

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        cascos = cleaned_data.get('cascos')

        # Validar cascos para motos solo si se proporciona un valor
        if category and category.name.upper().find('MOTOS') != -1:
            if cascos is not None and cascos < 0:
                raise forms.ValidationError("El número de cascos no puede ser negativo")

        return cleaned_data


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'nit', 'telefono', 'direccion', 'email']
        labels = {
            'name': 'Nombre de la empresa',
            'slug': 'Identificador único',
            'nit': 'NIT',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'email': 'Email',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el nombre de la empresa'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ej: parqueadero-la-23'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el NIT'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el teléfono'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese la dirección'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el email'
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            # Convertir a minúsculas y reemplazar espacios con guiones
            slug = slug.lower().replace(' ', '-')
            # Remover caracteres especiales excepto guiones
            import re
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            # Asegurar que no empiece o termine con guión
            slug = slug.strip('-')
        return slug


class TenantUserForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre de usuario'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el apellido'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el email'
        })
    )
    
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese la contraseña'
        })
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Confirme la contraseña'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['role']
        labels = {
            'role': 'Rol',
        }
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-select block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant

    def clean_username(self):
        username = self.cleaned_data.get('username')
        tenant = self.instance.tenant
        if username and tenant:
            # Permitir el mismo username en diferentes empresas
            if UserProfile.objects.filter(user__username=username, tenant=tenant).exists():
                raise forms.ValidationError("Este nombre de usuario ya existe en esta empresa.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email sea único globalmente (no solo por tenant)
            if UserProfile.objects.filter(user__email=email).exists():
                raise forms.ValidationError("Este email ya está registrado en el sistema.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        from django.contrib.auth.models import User
        # Crear el usuario de Django solo si no existe en este tenant
        user = None
        try:
            user_profile = UserProfile.objects.get(user__username=self.cleaned_data['username'], tenant=self.instance.tenant)
            user = user_profile.user
        except UserProfile.DoesNotExist:
            if not User.objects.filter(username=self.cleaned_data['username']).exists():
                user = User.objects.create_user(
                    username=self.cleaned_data['username'],
                    email=self.cleaned_data['email'],
                    password=self.cleaned_data['password1'],
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name']
                )
                instance.user = user
                instance.role = self.cleaned_data['role']
                instance.tenant = self.instance.tenant
                instance.is_active = True
                if commit:
                    instance.save()
                return instance
        # Si el usuario existe en otro tenant, no lo crea y no falla
        return instance


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
        widgets = {
            'empresa': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el nombre de la empresa'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el NIT'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el teléfono'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese la dirección'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant


class TenantUserEditForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="Usuario",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre de usuario'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el apellido'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el email'
        })
    )

    class Meta:
        model = UserProfile
        fields = ['role']
        labels = {
            'role': 'Rol',
        }
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-select block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and self.instance and self.instance.user:
            # Verificar que el usuario no exista ya en esta empresa (excluyendo el usuario actual)
            if UserProfile.objects.filter(
                user__username=username,
                tenant=self.instance.tenant
            ).exclude(user=self.instance.user).exists():
                raise forms.ValidationError("Este nombre de usuario ya existe en esta empresa")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and self.instance and self.instance.user:
            # Verificar que el email sea único globalmente (excluyendo el usuario actual)
            if UserProfile.objects.filter(user__email=email).exclude(user=self.instance.user).exists():
                raise forms.ValidationError("Este email ya está registrado en el sistema.")
        return email

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Actualizar el usuario de Django
        if self.instance and self.instance.user:
            user = self.instance.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        
        if commit:
            instance.save()
        
        return instance


class TenantUserPasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese la nueva contraseña'
        })
    )
    
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Confirme la nueva contraseña'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")

        return cleaned_data


class TenantCreateForm(forms.ModelForm):
    """
    Formulario para crear empresas con usuario administrador
    """
    admin_username = forms.CharField(
        max_length=150,
        label="Usuario Administrador",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre de usuario del administrador'
        }),
        help_text="Este será el usuario para acceder al sistema"
    )
    
    admin_email = forms.EmailField(
        label="Email del Administrador",
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'admin@empresa.com'
        }),
        help_text="Email del usuario administrador"
    )
    
    admin_password = forms.CharField(
        label="Contraseña del Administrador",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese la contraseña del administrador'
        }),
        help_text="Contraseña para el usuario administrador"
    )
    
    admin_confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Confirme la contraseña del administrador'
        }),
        help_text="Confirme la contraseña del administrador"
    )

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'nit', 'telefono', 'direccion', 'email', 'is_active']
        labels = {
            'name': 'Nombre de la empresa',
            'slug': 'Identificador único',
            'nit': 'NIT',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'email': 'Email',
            'is_active': 'Empresa activa',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el nombre de la empresa'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ej: parqueadero-la-23'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el NIT'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el teléfono'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-textarea block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese la dirección',
                'rows': '3'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el email'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            # Verificar que el slug sea único
            if Tenant.objects.filter(slug=slug).exists():
                raise forms.ValidationError("Este identificador ya está en uso. Por favor elige otro.")
        return slug

    def clean_admin_username(self):
        username = self.cleaned_data.get('admin_username')
        slug = self.cleaned_data.get('slug')
        if username and slug:
            try:
                tenant = Tenant.objects.get(slug=slug)
            except Tenant.DoesNotExist:
                tenant = None
            if tenant and UserProfile.objects.filter(user__username=username, tenant=tenant).exists():
                raise forms.ValidationError("Este nombre de usuario ya existe en esta empresa.")
        return username

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if email:
            # Verificar que el email sea único globalmente
            if UserProfile.objects.filter(user__email=email).exists():
                raise forms.ValidationError("Este email ya está registrado en el sistema.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        confirm_password = cleaned_data.get('admin_confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        tenant = super().save(commit=False)
        if commit:
            tenant.save()
            # Crear usuario administrador solo si no existe en este tenant
            admin_username = self.cleaned_data.get('admin_username')
            admin_email = self.cleaned_data.get('admin_email')
            admin_password = self.cleaned_data.get('admin_password')
            if admin_username and admin_email:
                from django.contrib.auth.models import User
                user = None
                try:
                    user_profile = UserProfile.objects.get(user__username=admin_username, tenant=tenant)
                    user = user_profile.user
                except UserProfile.DoesNotExist:
                    if not User.objects.filter(username=admin_username).exists():
                        user = User.objects.create_user(
                            username=admin_username,
                            email=admin_email,
                            password=admin_password or 'changeme123'
                        )
                        UserProfile.objects.create(
                            user=user,
                            tenant=tenant,
                            role='admin',
                            is_active=True
                        )
                # Si el usuario existe en otro tenant, no lo crea y no falla
        return tenant


class TenantEditForm(forms.ModelForm):
    """
    Formulario para editar empresas con opción de cambiar contraseña del administrador
    """
    admin_username = forms.CharField(
        max_length=150,
        label="Usuario Administrador",
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Ingrese el nombre de usuario del administrador'
        }),
        help_text="Este será el usuario para acceder al sistema",
        required=False
    )
    
    admin_email = forms.EmailField(
        label="Email del Administrador",
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'admin@empresa.com'
        }),
        help_text="Email del usuario administrador",
        required=False
    )
    
    admin_password = forms.CharField(
        label="Nueva Contraseña del Administrador",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Dejar en blanco para no cambiar'
        }),
        help_text="Dejar en blanco para mantener la contraseña actual",
        required=False
    )
    
    admin_confirm_password = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
            'placeholder': 'Confirmar la nueva contraseña'
        }),
        help_text="Confirmar la nueva contraseña",
        required=False
    )

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'nit', 'telefono', 'direccion', 'email', 'is_active']
        labels = {
            'name': 'Nombre de la empresa',
            'slug': 'Identificador único',
            'nit': 'NIT',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'email': 'Email',
            'is_active': 'Empresa activa',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el nombre de la empresa'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ej: parqueadero-la-23'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el NIT'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el teléfono'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese la dirección',
                'rows': '3'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input block w-full pl-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-md shadow-sm',
                'placeholder': 'Ingrese el email'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Buscar el usuario administrador existente
            try:
                admin_profile = UserProfile.objects.filter(
                    tenant=self.instance,
                    role='admin'
                ).first()
                if admin_profile:
                    self.fields['admin_username'].initial = admin_profile.user.username
                    self.fields['admin_email'].initial = admin_profile.user.email
            except:
                pass

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if slug:
            # Verificar que el slug sea único (excluyendo la instancia actual)
            existing = Tenant.objects.filter(slug=slug)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("Este identificador ya está en uso")
        return slug

    def clean_admin_username(self):
        username = self.cleaned_data.get('admin_username')
        if username:
            # Verificar que el username sea único
            existing = User.objects.filter(username=username)
            if self.instance and self.instance.pk:
                # Excluir el usuario administrador actual de esta empresa
                try:
                    admin_profile = UserProfile.objects.filter(
                        tenant=self.instance,
                        role='admin'
                    ).first()
                    if admin_profile:
                        existing = existing.exclude(pk=admin_profile.user.pk)
                except:
                    pass
            if existing.exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username

    def clean_admin_email(self):
        email = self.cleaned_data.get('admin_email')
        if email:
            # Verificar que el email sea único
            existing = User.objects.filter(email=email)
            if self.instance and self.instance.pk:
                # Excluir el usuario administrador actual de esta empresa
                try:
                    admin_profile = UserProfile.objects.filter(
                        tenant=self.instance,
                        role='admin'
                    ).first()
                    if admin_profile:
                        existing = existing.exclude(pk=admin_profile.user.pk)
                except:
                    pass
            if existing.exists():
                raise forms.ValidationError("Este email ya está en uso")
        return email

    def clean(self):
        cleaned_data = super().clean()
        admin_password = cleaned_data.get('admin_password')
        admin_confirm_password = cleaned_data.get('admin_confirm_password')

        # Validar que las contraseñas coincidan si se proporcionan
        if admin_password and admin_confirm_password:
            if admin_password != admin_confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden")
        elif admin_password and not admin_confirm_password:
            raise forms.ValidationError("Debe confirmar la nueva contraseña")
        elif admin_confirm_password and not admin_password:
            raise forms.ValidationError("Debe ingresar la nueva contraseña")

        return cleaned_data

    def save(self, commit=True):
        tenant = super().save(commit=False)
        
        if commit:
            tenant.save()
            
            # Actualizar o crear usuario administrador si se proporcionan datos
            admin_username = self.cleaned_data.get('admin_username')
            admin_email = self.cleaned_data.get('admin_email')
            admin_password = self.cleaned_data.get('admin_password')
            
            if admin_username and admin_email:
                try:
                    # Buscar usuario administrador existente
                    admin_profile = UserProfile.objects.filter(
                        tenant=tenant,
                        role='admin'
                    ).first()
                    
                    if admin_profile:
                        # Actualizar usuario existente
                        user = admin_profile.user
                        user.username = admin_username
                        user.email = admin_email
                        if admin_password:
                            user.set_password(admin_password)
                        user.save()
                        
                        admin_profile.save()
                    else:
                        # Crear nuevo usuario administrador
                        user = User.objects.create_user(
                            username=admin_username,
                            email=admin_email,
                            password=admin_password or 'changeme123'
                        )
                        
                        UserProfile.objects.create(
                            user=user,
                            tenant=tenant,
                            role='admin',
                            is_active=True
                        )
                        
                except Exception as e:
                    # Si hay error, no fallar la actualización de la empresa
                    pass
        
        return tenant


class CajaTurnoAperturaForm(forms.ModelForm):
    class Meta:
        model = CajaTurno
        fields = ['monto_inicial', 'observaciones']
        labels = {
            'monto_inicial': 'Fondo fijo inicial',
            'observaciones': 'Observaciones (opcional)',
        }
        widgets = {
            'monto_inicial': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
        }

class CajaMovimientoForm(forms.ModelForm):
    class Meta:
        model = CajaMovimiento
        fields = ['tipo', 'categoria', 'monto', 'descripcion', 'forma_pago', 'tipo_vehiculo']
        labels = {
            'tipo': 'Tipo de movimiento',
            'categoria': 'Categoría',
            'monto': 'Monto',
            'descripcion': 'Descripción (opcional)',
            'forma_pago': 'Forma de pago',
            'tipo_vehiculo': 'Tipo de vehículo (solo para parqueo)',
        }
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
            'descripcion': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
            'forma_pago': forms.Select(attrs={'class': 'form-select'}),
            'tipo_vehiculo': forms.TextInput(attrs={'class': 'form-input'}),
        }

class CajaTurnoCierreForm(forms.ModelForm):
    class Meta:
        model = CajaTurno
        fields = ['monto_real_contado', 'observaciones', 'firma_cierre']
        labels = {
            'monto_real_contado': 'Monto real contado',
            'observaciones': 'Observaciones (opcional)',
            'firma_cierre': 'Firma/confirmación',
        }
        widgets = {
            'monto_real_contado': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-input'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-textarea'}),
            'firma_cierre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre o código de confirmación'}),
        }

# --- FORMULARIOS PARA GESTIÓN DE ROLES Y PERMISOS ---

class CustomRoleForm(forms.ModelForm):
    """Formulario para crear/editar roles personalizados"""
    
    class Meta:
        model = CustomRole
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': 'Nombre del Rol',
            'description': 'Descripción',
            'is_active': 'Activo',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ingrese el nombre del rol'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Descripción del rol'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.instance.tenant = tenant


class RolePermissionForm(forms.Form):
    """Formulario para asignar permisos a roles"""
    
    def __init__(self, *args, **kwargs):
        role = kwargs.pop('role', None)
        super().__init__(*args, **kwargs)
        
        if role:
            # Obtener todos los módulos activos
            modules = Module.objects.filter(is_active=True).order_by('order')
            
            # Obtener permisos actuales del rol
            current_permissions = set(
                RolePermission.objects.filter(role=role)
                .values_list('permission__code', flat=True)
            )
            
            for module in modules:
                permissions = Permission.objects.filter(
                    module=module,
                    is_active=True
                ).order_by('name')
                
                if permissions.exists():
                    # Crear campo de checkbox para cada módulo
                    module_permissions = []
                    for permission in permissions:
                        field_name = f'perm_{permission.code}'
                        self.fields[field_name] = forms.BooleanField(
                            required=False,
                            initial=permission.code in current_permissions,
                            label=permission.name,
                            help_text=permission.description,
                            widget=forms.CheckboxInput(attrs={
                                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                                'data-module': module.code,
                                'data-permission': permission.code
                            })
                        )
                        module_permissions.append(field_name)
                    
                    # Agrupar permisos por módulo
                    self.fields[f'module_{module.code}'] = forms.CharField(
                        widget=forms.HiddenInput(),
                        required=False,
                        initial=','.join(module_permissions)
                    )


class UserRoleForm(forms.Form):
    """Formulario para asignar roles a usuarios"""
    
    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile:
            # Obtener roles disponibles para el tenant
            available_roles = CustomRole.objects.filter(
                tenant=user_profile.tenant,
                is_active=True
            ).order_by('name')
            
            # Obtener roles actuales del usuario
            current_roles = set(
                UserRole.objects.filter(user_profile=user_profile)
                .values_list('role__id', flat=True)
            )
            
            for role in available_roles:
                field_name = f'role_{role.id}'
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    initial=role.id in current_roles,
                    label=role.name,
                    help_text=role.description,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                        'data-role-id': role.id
                    })
                )
            
            # Campo para rol principal
            self.fields['primary_role'] = forms.ChoiceField(
                choices=[('', 'Sin rol principal')] + [(str(role.id), role.name) for role in available_roles],
                required=False,
                label='Rol Principal',
                help_text='El rol principal determina los permisos básicos del usuario',
                widget=forms.Select(attrs={
                    'class': 'form-select block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                })
            )
            
            # Establecer valor inicial del rol principal
            try:
                primary_role = UserRole.objects.get(
                    user_profile=user_profile,
                    is_primary=True
                )
                self.fields['primary_role'].initial = str(primary_role.role.id)
            except UserRole.DoesNotExist:
                pass


class UserPermissionForm(forms.Form):
    """Formulario para asignar permisos específicos a usuarios"""
    
    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile:
            # Obtener todos los módulos activos
            modules = Module.objects.filter(is_active=True).order_by('order')
            
            # Obtener permisos actuales del usuario (sobre-escrituras)
            current_permissions = {}
            for user_perm in UserPermission.objects.filter(user_profile=user_profile):
                current_permissions[user_perm.permission.code] = user_perm.is_granted
            
            for module in modules:
                permissions = Permission.objects.filter(
                    module=module,
                    is_active=True
                ).order_by('name')
                
                if permissions.exists():
                    for permission in permissions:
                        field_name = f'perm_{permission.code}'
                        
                        # Determinar si el usuario tiene este permiso por roles
                        has_permission_by_role = user_profile.has_permission(permission.code)
                        
                        # Si hay una sobre-escritura específica, usar esa
                        if permission.code in current_permissions:
                            initial_value = current_permissions[permission.code]
                        else:
                            initial_value = has_permission_by_role
                        
                        self.fields[field_name] = forms.BooleanField(
                            required=False,
                            initial=initial_value,
                            label=permission.name,
                            help_text=f"{permission.description} (Módulo: {module.name})",
                            widget=forms.CheckboxInput(attrs={
                                'class': 'form-checkbox h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                                'data-module': module.code,
                                'data-permission': permission.code,
                                'data-has-role-permission': 'true' if has_permission_by_role else 'false'
                            })
                        )


class RoleSearchForm(forms.Form):
    """Formulario para buscar roles"""
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Buscar roles...'
        })
    )
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )


class PermissionSearchForm(forms.Form):
    """Formulario para buscar permisos"""
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Buscar permisos...'
        })
    )
    module = forms.ModelChoiceField(
        queryset=Module.objects.filter(is_active=True),
        required=False,
        empty_label="Todos los módulos",
        widget=forms.Select(attrs={
            'class': 'form-select block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )