#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_system.settings')
django.setup()

from django.contrib.auth.models import User
from parking.models import Tenant, UserProfile, VehicleCategory, ParkingTicket, ParkingLot, Caja
from django.db import connection

print("=== DIAGNÓSTICO DE BASE DE DATOS ===\n")

# Verificar conexión a la base de datos
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Conexión a la base de datos: OK")
except Exception as e:
    print(f"❌ Error de conexión a la base de datos: {e}")
    sys.exit(1)

print("\n=== TABLAS EN LA BASE DE DATOS ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

print("\n=== MODELOS Y REGISTROS ===")

# Verificar tenants
tenants = Tenant.objects.all()
print(f"Tenants: {tenants.count()} registros")
for tenant in tenants:
    print(f"  - {tenant.name} (ID: {tenant.id}, Activo: {tenant.is_active})")

# Verificar usuarios
users = User.objects.all()
print(f"\nUsuarios: {users.count()} registros")
for user in users:
    print(f"  - {user.username} (Superuser: {user.is_superuser}, Activo: {user.is_active})")

# Verificar perfiles de usuario
profiles = UserProfile.objects.all()
print(f"\nPerfiles de Usuario: {profiles.count()} registros")
for profile in profiles:
    tenant_name = profile.tenant.name if profile.tenant else "Sin empresa"
    print(f"  - {profile.user.username} -> {tenant_name} ({profile.role})")

# Verificar categorías
categories = VehicleCategory.objects.all()
print(f"\nCategorías: {categories.count()} registros")
for category in categories:
    tenant_name = category.tenant.name if category.tenant else "Sin empresa"
    print(f"  - {category.name} -> {tenant_name}")

# Verificar tickets
tickets = ParkingTicket.objects.all()
print(f"\nTickets: {tickets.count()} registros")

# Verificar empresas de parqueadero
parking_lots = ParkingLot.objects.all()
print(f"\nEmpresas de Parqueadero: {parking_lots.count()} registros")

# Verificar caja
caja_records = Caja.objects.all()
print(f"\nRegistros de Caja: {caja_records.count()} registros")

print("\n=== VERIFICACIÓN DE RELACIONES ===")

# Verificar usuarios sin perfil
users_without_profile = []
for user in User.objects.all():
    try:
        profile = user.profile
    except:
        users_without_profile.append(user.username)

if users_without_profile:
    print(f"⚠️  Usuarios sin perfil: {users_without_profile}")
else:
    print("✅ Todos los usuarios tienen perfil")

# Verificar categorías sin tenant
categories_without_tenant = VehicleCategory.objects.filter(tenant__isnull=True)
if categories_without_tenant.exists():
    print(f"⚠️  Categorías sin tenant: {categories_without_tenant.count()}")
else:
    print("✅ Todas las categorías tienen tenant")

# Verificar tickets sin tenant
tickets_without_tenant = ParkingTicket.objects.filter(tenant__isnull=True)
if tickets_without_tenant.exists():
    print(f"⚠️  Tickets sin tenant: {tickets_without_tenant.count()}")
else:
    print("✅ Todos los tickets tienen tenant")

print("\n=== VERIFICACIÓN DE MIGRACIONES ===")
try:
    from django.core.management import call_command
    from io import StringIO
    
    # Verificar migraciones pendientes
    out = StringIO()
    call_command('showmigrations', 'parking', stdout=out)
    migrations_output = out.getvalue()
    
    if '[X]' in migrations_output:
        print("✅ Todas las migraciones aplicadas")
    else:
        print("⚠️  Hay migraciones pendientes")
        print(migrations_output)
        
except Exception as e:
    print(f"❌ Error verificando migraciones: {e}")

print("\n=== FIN DEL DIAGNÓSTICO ===") 