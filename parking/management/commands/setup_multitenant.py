from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile, VehicleCategory, ParkingLot


class Command(BaseCommand):
    help = 'Configura el sistema multitenant inicial con tenants y usuarios de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Crear un superusuario para administrar el sistema',
        )

    def handle(self, *args, **options):
        self.stdout.write('Configurando sistema multitenant...')

        # Crear tenant de ejemplo
        tenant, created = Tenant.objects.get_or_create(
            slug='parqueadero-ejemplo',
            defaults={
                'name': 'Parqueadero Ejemplo',
                'nit': '900123456-7',
                'telefono': '3001234567',
                'direccion': 'Calle 123 #45-67, Bogotá',
                'email': 'admin@parqueaderoejemplo.com',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Tenant creado: {tenant.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Tenant ya existe: {tenant.name}')
            )

        # Crear perfil de parqueadero
        parking_lot, created = ParkingLot.objects.get_or_create(
            tenant=tenant,
            defaults={
                'empresa': tenant.name,
                'nit': tenant.nit,
                'telefono': tenant.telefono,
                'direccion': tenant.direccion,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Perfil de parqueadero creado para: {tenant.name}')
            )

        # Crear categorías de vehículos por defecto
        categories_data = [
            {
                'name': 'Carros',
                'first_hour_rate': 2000.00,
                'additional_hour_rate': 1500.00,
                'is_monthly': False,
            },
            {
                'name': 'Motos',
                'first_hour_rate': 1000.00,
                'additional_hour_rate': 800.00,
                'is_monthly': False,
            },
            {
                'name': 'Mensual Carros',
                'first_hour_rate': 0.00,
                'additional_hour_rate': 0.00,
                'is_monthly': True,
                'monthly_rate': 150000.00,
            },
            {
                'name': 'Mensual Motos',
                'first_hour_rate': 0.00,
                'additional_hour_rate': 0.00,
                'is_monthly': True,
                'monthly_rate': 80000.00,
            },
        ]

        for cat_data in categories_data:
            category, created = VehicleCategory.objects.get_or_create(
                tenant=tenant,
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Categoría creada: {category.name}')
                )

        # Crear superusuario si se solicita
        if options['create_superuser']:
            username = 'admin'
            email = 'admin@parqueaderoejemplo.com'
            password = 'admin123'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Superusuario creado: {username} / {password}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Superusuario ya existe: {username}')
                )

            # Crear perfil de usuario para el superusuario
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'tenant': tenant,
                    'role': 'admin',
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Perfil de usuario creado para: {user.username}')
                )

        # Crear usuario operador de ejemplo
        operator_username = 'operador'
        operator_password = 'operador123'

        operator_user, created = User.objects.get_or_create(
            username=operator_username,
            defaults={
                'email': 'operador@parqueaderoejemplo.com',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if created:
            operator_user.set_password(operator_password)
            operator_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Usuario operador creado: {operator_username} / {operator_password}')
            )

        # Crear perfil de operador
        operator_profile, created = UserProfile.objects.get_or_create(
            user=operator_user,
            defaults={
                'tenant': tenant,
                'role': 'operator',
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Perfil de operador creado para: {operator_user.username}')
            )

        self.stdout.write(
            self.style.SUCCESS('Configuración multitenant completada exitosamente!')
        )
        self.stdout.write('')
        self.stdout.write('Credenciales de acceso:')
        self.stdout.write(f'  - Superusuario: admin / admin123')
        self.stdout.write(f'  - Operador: operador / operador123')
        self.stdout.write('')
        self.stdout.write('Recuerda cambiar las contraseñas en producción!') 