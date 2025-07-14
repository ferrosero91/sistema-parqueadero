#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile, VehicleCategory

print("=== DIAGNÓSTICO Y CORRECCIÓN DEL SISTEMA ===\n")

# 1. Verificar tenants
print("1. Verificando empresas (tenants)...")
tenants = Tenant.objects.all()
print(f"   Empresas encontradas: {tenants.count()}")
for tenant in tenants:
    print(f"   - {tenant.name} (ID: {tenant.id}, Activo: {tenant.is_active})")

# 2. Verificar usuarios
print("\n2. Verificando usuarios...")
users = User.objects.all()
print(f"   Usuarios encontrados: {users.count()}")
for user in users:
    try:
        profile = user.profile
        tenant_name = profile.tenant.name if profile.tenant else "Sin empresa"
        print(f"   - {user.username} (Superuser: {user.is_superuser}, Tenant: {tenant_name}, Rol: {profile.role})")
    except:
        print(f"   - {user.username} (Superuser: {user.is_superuser}, Sin perfil)")

# 3. Verificar categorías
print("\n3. Verificando categorías...")
categories = VehicleCategory.objects.all()
print(f"   Categorías encontradas: {categories.count()}")
for category in categories:
    tenant_name = category.tenant.name if category.tenant else "Sin empresa"
    print(f"   - {category.name} (Tenant: {tenant_name})")

# 4. Crear categorías por defecto si no existen
print("\n4. Creando categorías por defecto...")
for tenant in tenants:
    if tenant.is_active:
        default_categories = [
            {'name': 'CARROS', 'first_hour_rate': 2000, 'additional_hour_rate': 1000, 'is_monthly': False},
            {'name': 'MOTOS', 'first_hour_rate': 1000, 'additional_hour_rate': 500, 'is_monthly': False},
            {'name': 'CAMIONES', 'first_hour_rate': 3000, 'additional_hour_rate': 1500, 'is_monthly': False},
            {'name': 'CAMIONETAS', 'first_hour_rate': 2500, 'additional_hour_rate': 1200, 'is_monthly': False},
        ]
        
        for cat_data in default_categories:
            category, created = VehicleCategory.objects.get_or_create(
                name=cat_data['name'],
                tenant=tenant,
                defaults={
                    'first_hour_rate': cat_data['first_hour_rate'],
                    'additional_hour_rate': cat_data['additional_hour_rate'],
                    'is_monthly': cat_data['is_monthly']
                }
            )
            if created:
                print(f"   ✅ Categoría '{cat_data['name']}' creada para {tenant.name}")
            else:
                print(f"   ℹ️  Categoría '{cat_data['name']}' ya existe para {tenant.name}")

# 5. Verificar que todos los usuarios tengan perfil
print("\n5. Verificando perfiles de usuario...")
for user in users:
    try:
        profile = user.profile
        if not profile.tenant and not user.is_superuser:
            print(f"   ⚠️  Usuario {user.username} no tiene tenant asignado")
    except UserProfile.DoesNotExist:
        if not user.is_superuser:
            print(f"   ❌ Usuario {user.username} no tiene perfil")
        else:
            print(f"   ℹ️  Superusuario {user.username} no tiene perfil (normal)")

print("\n=== DIAGNÓSTICO COMPLETADO ===")
print("\nPara acceder al sistema:")
print("1. Superadmin: admin / admin123")
print("2. Empresas: Usar el botón 'Acceder' desde el panel de superadmin")
print("3. O acceder directamente con los usuarios de cada empresa") 