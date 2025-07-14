#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de permisos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile, CustomRole, UserRole, Permission, Module

def test_admin_permissions():
    """Probar permisos de administrador"""
    print("🔍 Probando permisos de administrador...")
    
    # Buscar un tenant
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("❌ No se encontró ningún tenant activo")
        return
    
    print(f"🏢 Usando tenant: {tenant.name}")
    
    # Buscar un usuario administrador
    admin_user = UserProfile.objects.filter(
        tenant=tenant,
        role='admin',
        is_active=True
    ).first()
    
    if not admin_user:
        print("❌ No se encontró ningún usuario administrador")
        return
    
    print(f"👤 Usuario administrador: {admin_user.user.username}")
    
    # Probar permisos básicos
    permissions_to_test = [
        'manage_roles',
        'edit_users', 
        'view_users',
        'vehicle_entry',
        'vehicle_exit',
        'cash_management',
        'view_reports',
        'view_dashboard'
    ]
    
    print("\n📋 Verificando permisos:")
    for permission in permissions_to_test:
        has_perm = admin_user.has_permission(permission)
        status = "✅" if has_perm else "❌"
        print(f"  {status} {permission}: {has_perm}")
    
    # Verificar roles personalizados
    print("\n🎭 Verificando roles personalizados:")
    user_roles = UserRole.objects.filter(user_profile=admin_user)
    for user_role in user_roles:
        print(f"  📌 Rol: {user_role.role.name} (Principal: {user_role.is_primary})")
    
    # Verificar módulos disponibles
    print("\n📦 Verificando módulos disponibles:")
    modules = admin_user.get_modules()
    for module in modules:
        print(f"  📁 Módulo: {module.name}")
    
    print("\n✅ Prueba completada")

def test_role_creation():
    """Probar creación de roles"""
    print("\n🔧 Probando creación de roles...")
    
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("❌ No se encontró ningún tenant activo")
        return
    
    # Verificar que existen roles por defecto
    default_roles = CustomRole.objects.filter(tenant=tenant, is_system=True)
    print(f"📋 Roles del sistema encontrados: {default_roles.count()}")
    
    for role in default_roles:
        permissions_count = role.rolepermission_set.count()
        print(f"  🎭 {role.name}: {permissions_count} permisos")
    
    print("✅ Verificación de roles completada")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema de permisos...")
    
    try:
        test_admin_permissions()
        test_role_creation()
        print("\n🎉 Todas las pruebas completadas exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc() 