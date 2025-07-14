#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del sistema cuando una empresa está inactiva
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from parking.models import Tenant, UserProfile

def test_tenant_inactive():
    """Probar el comportamiento cuando una empresa está inactiva"""
    
    # Crear un cliente de prueba
    client = Client()
    
    # Buscar una empresa existente
    tenant = Tenant.objects.first()
    if not tenant:
        print("No hay empresas en el sistema. Creando una empresa de prueba...")
        tenant = Tenant.objects.create(
            name="Empresa de Prueba",
            identifier="TEST001",
            is_active=True
        )
    
    # Crear un usuario de prueba
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    
    # Crear perfil de usuario
    profile = UserProfile.objects.create(
        user=user,
        tenant=tenant,
        role='operator'
    )
    
    print(f"Usuario de prueba creado: {user.username}")
    print(f"Empresa asignada: {tenant.name} (ID: {tenant.id})")
    print(f"Estado de empresa: {'Activa' if tenant.is_active else 'Inactiva'}")
    
    # Hacer login
    login_success = client.login(username='testuser', password='testpass123')
    print(f"Login exitoso: {login_success}")
    
    # Probar acceso al dashboard
    response = client.get('/dashboard/')
    print(f"Dashboard - Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Dashboard - URL final: {response.url}")
    
    # Desactivar la empresa
    print("\n--- Desactivando empresa ---")
    tenant.is_active = False
    tenant.save()
    print(f"Empresa desactivada: {tenant.name}")
    
    # Probar acceso al dashboard después de desactivar
    response = client.get('/dashboard/')
    print(f"Dashboard después de desactivar - Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Dashboard después de desactivar - URL final: {response.url}")
    
    # Probar acceso directo a tenant-inactive
    response = client.get('/tenant-inactive/')
    print(f"Tenant inactive directo - Status: {response.status_code}")
    
    # Reactivar la empresa
    print("\n--- Reactivando empresa ---")
    tenant.is_active = True
    tenant.save()
    print(f"Empresa reactivada: {tenant.name}")
    
    # Probar acceso al dashboard después de reactivar
    response = client.get('/dashboard/')
    print(f"Dashboard después de reactivar - Status: {response.status_code}")
    if hasattr(response, 'url'):
        print(f"Dashboard después de reactivar - URL final: {response.url}")
    
    # Limpiar datos de prueba
    user.delete()
    if tenant.name == "Empresa de Prueba":
        tenant.delete()
    
    print("\n--- Prueba completada ---")

if __name__ == '__main__':
    test_tenant_inactive() 