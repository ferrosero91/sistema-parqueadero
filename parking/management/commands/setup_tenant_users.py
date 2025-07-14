from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile


class Command(BaseCommand):
    help = 'Configura usuarios de ejemplo para las empresas existentes'

    def handle(self, *args, **options):
        # Obtener todas las empresas activas
        tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in tenants:
            self.stdout.write(f'Configurando usuarios para empresa: {tenant.name}')
            
            # Crear usuario administrador si no existe
            admin_username = f'admin_{tenant.slug}'
            if not User.objects.filter(username=admin_username).exists():
                admin_user = User.objects.create_user(
                    username=admin_username,
                    email=f'admin@{tenant.slug}.com',
                    password='admin123456',
                    first_name='Administrador',
                    last_name=tenant.name
                )
                
                UserProfile.objects.create(
                    user=admin_user,
                    tenant=tenant,
                    role='admin',
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario administrador creado: {admin_username}')
                )
            else:
                self.stdout.write(f'⚠ Usuario administrador ya existe: {admin_username}')
            
            # Crear usuario cajero si no existe
            cajero_username = f'cajero_{tenant.slug}'
            if not User.objects.filter(username=cajero_username).exists():
                cajero_user = User.objects.create_user(
                    username=cajero_username,
                    email=f'cajero@{tenant.slug}.com',
                    password='cajero123456',
                    first_name='Cajero',
                    last_name=tenant.name
                )
                
                UserProfile.objects.create(
                    user=cajero_user,
                    tenant=tenant,
                    role='cajero',
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario cajero creado: {cajero_username}')
                )
            else:
                self.stdout.write(f'⚠ Usuario cajero ya existe: {cajero_username}')
            
            # Crear usuario operador si no existe
            operador_username = f'operador_{tenant.slug}'
            if not User.objects.filter(username=operador_username).exists():
                operador_user = User.objects.create_user(
                    username=operador_username,
                    email=f'operador@{tenant.slug}.com',
                    password='operador123456',
                    first_name='Operador',
                    last_name=tenant.name
                )
                
                UserProfile.objects.create(
                    user=operador_user,
                    tenant=tenant,
                    role='operator',
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Usuario operador creado: {operador_username}')
                )
            else:
                self.stdout.write(f'⚠ Usuario operador ya existe: {operador_username}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Configuración de usuarios completada')
        )
        self.stdout.write('\nCredenciales de ejemplo:')
        self.stdout.write('Administrador: admin_[slug_empresa] / admin123456')
        self.stdout.write('Cajero: cajero_[slug_empresa] / cajero123456')
        self.stdout.write('Operador: operador_[slug_empresa] / operador123456') 