#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from django.db import migrations, models
from django.conf import settings

def create_multitenant_migrations():
    """Crear migraciones para el sistema multitenant"""
    
    # Crear migración para Tenant
    tenant_migration = migrations.Migration(
        '0002_create_tenant_model',
        'parking',
        [
            migrations.CreateModel(
                name='Tenant',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('name', models.CharField(max_length=255, verbose_name='Nombre de la empresa')),
                    ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Identificador único')),
                    ('nit', models.CharField(max_length=20, verbose_name='NIT')),
                    ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                    ('direccion', models.CharField(max_length=200, verbose_name='Dirección')),
                    ('email', models.EmailField(blank=True, null=True, verbose_name='Email')),
                    ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                ],
                options={
                    'verbose_name': 'Empresa',
                    'verbose_name_plural': 'Empresas',
                    'ordering': ['name'],
                },
            ),
        ],
    )
    
    # Crear migración para UserProfile
    userprofile_migration = migrations.Migration(
        '0003_create_userprofile_model',
        'parking',
        [
            migrations.CreateModel(
                name='UserProfile',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('role', models.CharField(choices=[('admin', 'Administrador'), ('operator', 'Operador'), ('viewer', 'Visualizador')], default='operator', max_length=20, verbose_name='Rol')),
                    ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                    ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
                    ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa')),
                ],
                options={
                    'verbose_name': 'Perfil de Usuario',
                    'verbose_name_plural': 'Perfiles de Usuario',
                },
            ),
        ],
    )
    
    # Crear migración para agregar tenant a VehicleCategory
    category_tenant_migration = migrations.Migration(
        '0004_add_tenant_to_vehiclecategory',
        'parking',
        [
            migrations.AddField(
                model_name='vehiclecategory',
                name='tenant',
                field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa'),
                preserve_default=False,
            ),
            migrations.AlterUniqueTogether(
                name='vehiclecategory',
                unique_together={('tenant', 'name')},
            ),
        ],
    )
    
    # Crear migración para agregar tenant a ParkingLot
    parkinglot_tenant_migration = migrations.Migration(
        '0005_add_tenant_to_parkinglot',
        'parking',
        [
            migrations.AddField(
                model_name='parkinglot',
                name='tenant',
                field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa'),
                preserve_default=False,
            ),
        ],
    )
    
    # Crear migración para agregar tenant a ParkingTicket
    parkingticket_tenant_migration = migrations.Migration(
        '0006_add_tenant_to_parkingticket',
        'parking',
        [
            migrations.AddField(
                model_name='parkingticket',
                name='tenant',
                field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa'),
                preserve_default=False,
            ),
            migrations.AlterUniqueConstraint(
                model_name='parkingticket',
                constraint=models.UniqueConstraint(condition=models.Q(('exit_time__isnull', True)), fields=('tenant', 'placa'), name='unique_active_plate_per_tenant'),
            ),
        ],
    )
    
    # Crear migración para agregar tenant a Caja
    caja_tenant_migration = migrations.Migration(
        '0007_add_tenant_to_caja',
        'parking',
        [
            migrations.AddField(
                model_name='caja',
                name='tenant',
                field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa'),
                preserve_default=False,
            ),
            migrations.AlterUniqueTogether(
                name='caja',
                unique_together={('tenant', 'fecha', 'tipo')},
            ),
        ],
    )
    
    return [
        tenant_migration,
        userprofile_migration,
        category_tenant_migration,
        parkinglot_tenant_migration,
        parkingticket_tenant_migration,
        caja_tenant_migration,
    ]

def create_roles_permissions_migrations():
    """Crear migraciones para el sistema de roles y permisos"""
    
    # Migración para crear módulos
    modules_migration = migrations.Migration(
        '0011_create_modules',
        'parking',
        [
            migrations.CreateModel(
                name='Module',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('name', models.CharField(max_length=100, verbose_name='Nombre del módulo')),
                    ('code', models.CharField(max_length=50, unique=True, verbose_name='Código del módulo')),
                    ('description', models.TextField(blank=True, verbose_name='Descripción')),
                    ('icon', models.CharField(blank=True, max_length=50, verbose_name='Icono')),
                    ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                    ('order', models.IntegerField(default=0, verbose_name='Orden')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                ],
                options={
                    'verbose_name': 'Módulo',
                    'verbose_name_plural': 'Módulos',
                    'ordering': ['order', 'name'],
                },
            ),
        ],
    )
    
    # Migración para crear permisos
    permissions_migration = migrations.Migration(
        '0012_create_permissions',
        'parking',
        [
            migrations.CreateModel(
                name='Permission',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('name', models.CharField(max_length=100, verbose_name='Nombre del permiso')),
                    ('code', models.CharField(max_length=50, verbose_name='Código del permiso')),
                    ('description', models.TextField(blank=True, verbose_name='Descripción')),
                    ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                    ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.module', verbose_name='Módulo')),
                ],
                options={
                    'verbose_name': 'Permiso',
                    'verbose_name_plural': 'Permisos',
                    'unique_together': {('module', 'code')},
                    'ordering': ['module__order', 'name'],
                },
            ),
        ],
    )
    
    # Migración para crear roles personalizados
    custom_roles_migration = migrations.Migration(
        '0013_create_custom_roles',
        'parking',
        [
            migrations.CreateModel(
                name='CustomRole',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('name', models.CharField(max_length=100, verbose_name='Nombre del rol')),
                    ('description', models.TextField(blank=True, verbose_name='Descripción')),
                    ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                    ('is_system', models.BooleanField(default=False, verbose_name='Rol del sistema')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                    ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa')),
                ],
                options={
                    'verbose_name': 'Rol Personalizado',
                    'verbose_name_plural': 'Roles Personalizados',
                    'unique_together': {('tenant', 'name')},
                    'ordering': ['name'],
                },
            ),
        ],
    )
    
    # Migración para crear permisos de roles
    role_permissions_migration = migrations.Migration(
        '0014_create_role_permissions',
        'parking',
        [
            migrations.CreateModel(
                name='RolePermission',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.permission', verbose_name='Permiso')),
                    ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.customrole', verbose_name='Rol')),
                ],
                options={
                    'verbose_name': 'Permiso de Rol',
                    'verbose_name_plural': 'Permisos de Roles',
                    'unique_together': {('role', 'permission')},
                    'ordering': ['role__name', 'permission__module__order', 'permission__name'],
                },
            ),
        ],
    )
    
    # Migración para crear roles de usuario
    user_roles_migration = migrations.Migration(
        '0015_create_user_roles',
        'parking',
        [
            migrations.CreateModel(
                name='UserRole',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('is_primary', models.BooleanField(default=False, verbose_name='Rol principal')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                    ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.customrole', verbose_name='Rol')),
                    ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.userprofile', verbose_name='Perfil de Usuario')),
                ],
                options={
                    'verbose_name': 'Rol de Usuario',
                    'verbose_name_plural': 'Roles de Usuario',
                    'unique_together': {('user_profile', 'role')},
                    'ordering': ['-is_primary', 'role__name'],
                },
            ),
        ],
    )
    
    # Migración para crear permisos de usuario
    user_permissions_migration = migrations.Migration(
        '0016_create_user_permissions',
        'parking',
        [
            migrations.CreateModel(
                name='UserPermission',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('is_granted', models.BooleanField(default=True, verbose_name='Permitido')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
                    ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.permission', verbose_name='Permiso')),
                    ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.userprofile', verbose_name='Perfil de Usuario')),
                ],
                options={
                    'verbose_name': 'Permiso de Usuario',
                    'verbose_name_plural': 'Permisos de Usuario',
                    'unique_together': {('user_profile', 'permission')},
                    'ordering': ['permission__module__order', 'permission__name'],
                },
            ),
        ],
    )
    
    # Migración para crear bitácora de acceso
    access_log_migration = migrations.Migration(
        '0017_create_access_log',
        'parking',
        [
            migrations.CreateModel(
                name='AccessLog',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('action', models.CharField(choices=[('login', 'Inicio de sesión'), ('logout', 'Cierre de sesión'), ('permission_change', 'Cambio de permisos'), ('role_assignment', 'Asignación de rol'), ('user_creation', 'Creación de usuario'), ('user_edit', 'Edición de usuario'), ('user_deletion', 'Eliminación de usuario')], max_length=50, verbose_name='Acción')),
                    ('details', models.TextField(blank=True, verbose_name='Detalles')),
                    ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Dirección IP')),
                    ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                    ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                    ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parking.tenant', verbose_name='Empresa')),
                    ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user', verbose_name='Usuario')),
                ],
                options={
                    'verbose_name': 'Bitácora de Acceso',
                    'verbose_name_plural': 'Bitácoras de Acceso',
                    'ordering': ['-created_at'],
                },
            ),
        ],
    )
    
    return [
        modules_migration,
        permissions_migration,
        custom_roles_migration,
        role_permissions_migration,
        user_roles_migration,
        user_permissions_migration,
        access_log_migration,
    ]

if __name__ == '__main__':
    # Crear el directorio de migraciones si no existe
    migrations_dir = 'parking/migrations'
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    # Crear archivo __init__.py si no existe
    init_file = os.path.join(migrations_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
    
    # Crear las migraciones
    migrations_list = create_multitenant_migrations()
    
    for i, migration in enumerate(migrations_list):
        migration_file = os.path.join(migrations_dir, f'{migration.name}.py')
        
        with open(migration_file, 'w') as f:
            f.write(f'''# Generated by custom script
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('parking', '{migrations_list[i-1].name if i > 0 else "0001_initial"}'),
    ]

    operations = [
        {migration.operations[0]},
    ]
''')
        
        print(f'Migración creada: {migration_file}')
    
    print('Migraciones creadas exitosamente!') 