#!/usr/bin/env python3
"""
Script para asignar rol de administrador a un usuario
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile, CustomRole, UserRole

def assign_admin_role():
    """Asignar rol de administrador a un usuario"""
    print("🔧 Asignando rol de administrador...")
    
    # Buscar un tenant
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("❌ No se encontró ningún tenant activo")
        return
    
    print(f"🏢 Usando tenant: {tenant.name}")
    
    # Buscar usuarios del tenant
    users = UserProfile.objects.filter(tenant=tenant, is_active=True)
    print(f"👥 Usuarios encontrados: {users.count()}")
    
    for user_profile in users:
        print(f"  👤 {user_profile.user.username} (Rol actual: {user_profile.role})")
    
    # Buscar el rol de administrador
    admin_role = CustomRole.objects.filter(
        tenant=tenant,
        name='Administrador',
        is_active=True
    ).first()
    
    if not admin_role:
        print("❌ No se encontró el rol de administrador")
        return
    
    print(f"🎭 Rol de administrador encontrado: {admin_role.name}")
    
    # Buscar un usuario para asignar como administrador
    target_user = UserProfile.objects.filter(
        tenant=tenant,
        is_active=True
    ).first()
    
    if not target_user:
        print("❌ No se encontró ningún usuario para asignar")
        return
    
    print(f"🎯 Usuario objetivo: {target_user.user.username}")
    
    # Cambiar el rol básico a administrador
    target_user.role = 'admin'
    target_user.save()
    print(f"✅ Rol básico cambiado a: {target_user.role}")
    
    # Asignar el rol personalizado de administrador
    user_role, created = UserRole.objects.get_or_create(
        user_profile=target_user,
        role=admin_role,
        defaults={'is_primary': True}
    )
    
    if created:
        print(f"✅ Rol personalizado asignado: {admin_role.name}")
    else:
        print(f"ℹ️  Rol personalizado ya estaba asignado: {admin_role.name}")
    
    # Verificar permisos
    print("\n📋 Verificando permisos del usuario:")
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
    
    for permission in permissions_to_test:
        has_perm = target_user.has_permission(permission)
        status = "✅" if has_perm else "❌"
        print(f"  {status} {permission}: {has_perm}")
    
    print(f"\n🎉 Usuario {target_user.user.username} ahora es administrador")

if __name__ == "__main__":
    print("🚀 Iniciando asignación de rol de administrador...")
    
    try:
        assign_admin_role()
        print("\n✅ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
        import traceback
        traceback.print_exc() 