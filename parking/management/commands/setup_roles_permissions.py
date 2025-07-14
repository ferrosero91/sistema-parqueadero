from django.core.management.base import BaseCommand
from django.db import transaction
from parking.models import Module, Permission, CustomRole, RolePermission, Tenant


class Command(BaseCommand):
    help = 'Inicializar el sistema de roles y permisos con módulos y permisos por defecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='ID del tenant específico para inicializar (opcional)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la recreación de módulos y permisos existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Inicializando sistema de roles y permisos...'))
        
        with transaction.atomic():
            # 1. Crear módulos por defecto
            self.create_modules(options['force'])
            
            # 2. Crear permisos por defecto
            self.create_permissions(options['force'])
            
            # 3. Crear roles por defecto para cada tenant
            self.create_default_roles(options['tenant_id'])
        
        self.stdout.write(self.style.SUCCESS('✅ Sistema de roles y permisos inicializado correctamente'))

    def create_modules(self, force=False):
        """Crear módulos por defecto"""
        self.stdout.write('📦 Creando módulos...')
        
        default_modules = Module.get_default_modules()
        
        for module_data in default_modules:
            module, created = Module.objects.get_or_create(
                code=module_data['code'],
                defaults=module_data
            )
            
            if created:
                self.stdout.write(f'  ✅ Creado: {module.name}')
            elif force:
                # Actualizar módulo existente
                for key, value in module_data.items():
                    setattr(module, key, value)
                module.save()
                self.stdout.write(f'  🔄 Actualizado: {module.name}')
            else:
                self.stdout.write(f'  ℹ️  Ya existe: {module.name}')

    def create_permissions(self, force=False):
        """Crear permisos por defecto"""
        self.stdout.write('🔐 Creando permisos...')
        
        default_permissions = Permission.get_default_permissions()
        
        for perm_data in default_permissions:
            try:
                module = Module.objects.get(code=perm_data['module_code'])
                
                permission, created = Permission.objects.get_or_create(
                    module=module,
                    code=perm_data['code'],
                    defaults={
                        'name': perm_data['name'],
                        'description': perm_data.get('description', ''),
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'  ✅ Creado: {permission.name}')
                elif force:
                    # Actualizar permiso existente
                    permission.name = perm_data['name']
                    permission.description = perm_data.get('description', '')
                    permission.save()
                    self.stdout.write(f'  🔄 Actualizado: {permission.name}')
                else:
                    self.stdout.write(f'  ℹ️  Ya existe: {permission.name}')
                    
            except Module.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Módulo no encontrado: {perm_data["module_code"]}')
                )

    def create_default_roles(self, tenant_id=None):
        """Crear roles por defecto para cada tenant"""
        self.stdout.write('👥 Creando roles por defecto...')
        
        if tenant_id:
            tenants = Tenant.objects.filter(id=tenant_id)
        else:
            tenants = Tenant.objects.filter(is_active=True)
        
        for tenant in tenants:
            self.stdout.write(f'  🏢 Procesando empresa: {tenant.name}')
            
            # Crear roles por defecto para este tenant
            CustomRole.create_default_roles(tenant)
            
            # Mostrar roles creados
            roles = CustomRole.objects.filter(tenant=tenant)
            for role in roles:
                permissions_count = RolePermission.objects.filter(role=role).count()
                self.stdout.write(f'    ✅ Rol: {role.name} ({permissions_count} permisos)') 