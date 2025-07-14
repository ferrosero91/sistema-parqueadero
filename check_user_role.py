#!/usr/bin/env python
"""
Script para verificar el rol del usuario y diagnosticar problemas de permisos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from parking.models import UserProfile, Tenant, User
from django.contrib.auth.models import User

def check_user_roles():
    """Verificar roles de usuarios en el sistema"""
    print("🔍 Verificando roles de usuarios...")
    print("=" * 50)
    
    # Obtener todos los usuarios con perfiles
    profiles = UserProfile.objects.all().select_related('user', 'tenant')
    
    if not profiles:
        print("❌ No hay perfiles de usuario en el sistema")
        return
    
    print(f"📊 Total de perfiles encontrados: {profiles.count()}")
    print()
    
    for profile in profiles:
        print(f"👤 Usuario: {profile.user.username}")
        print(f"   📧 Email: {profile.user.email}")
        print(f"   🏢 Empresa: {profile.tenant.name if profile.tenant else 'Sin empresa'}")
        print(f"   🎭 Rol: {profile.get_role_display()}")
        print(f"   ✅ Activo: {'Sí' if profile.is_active else 'No'}")
        print(f"   🔑 Superusuario: {'Sí' if profile.user.is_superuser else 'No'}")
        print()
    
    # Verificar permisos para funciones de caja
    print("🔐 Verificando permisos para funciones de caja:")
    print("=" * 50)
    
    for profile in profiles:
        can_access_caja = profile.role in ['admin', 'cajero']
        print(f"👤 {profile.user.username}:")
        print(f"   Rol: {profile.get_role_display()}")
        print(f"   Puede acceder a caja: {'✅ Sí' if can_access_caja else '❌ No'}")
        print()

def create_test_user():
    """Crear un usuario de prueba con rol cajero"""
    print("🔧 Creando usuario de prueba con rol cajero...")
    
    # Buscar el primer tenant activo
    tenant = Tenant.objects.filter(is_active=True).first()
    if not tenant:
        print("❌ No hay empresas activas en el sistema")
        return
    
    # Crear usuario de prueba
    username = "cajero_test"
    email = "cajero@test.com"
    password = "cajero123"
    
    # Verificar si el usuario ya existe
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': 'Cajero',
            'last_name': 'Test',
            'is_active': True
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Usuario creado: {username}")
    else:
        print(f"ℹ️ Usuario ya existe: {username}")
    
    # Crear o actualizar perfil
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'tenant': tenant,
            'role': 'cajero',
            'is_active': True
        }
    )
    
    if not created:
        profile.role = 'cajero'
        profile.tenant = tenant
        profile.is_active = True
        profile.save()
        print(f"✅ Perfil actualizado para: {username}")
    else:
        print(f"✅ Perfil creado para: {username}")
    
    print(f"🔑 Credenciales de prueba:")
    print(f"   Usuario: {username}")
    print(f"   Contraseña: {password}")
    print(f"   Empresa: {tenant.name}")
    print(f"   Rol: Cajero")
    print()

if __name__ == "__main__":
    print("🧪 Diagnóstico de roles de usuario")
    print("=" * 50)
    
    check_user_roles()
    
    # Preguntar si crear usuario de prueba
    response = input("¿Desea crear un usuario de prueba con rol cajero? (s/n): ")
    if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        create_test_user()
    
    print("✅ Diagnóstico completado") 