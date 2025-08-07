#!/bin/bash

# Script de despliegue para el sistema de parqueadero
echo "🚀 Iniciando despliegue del sistema de parqueadero..."

# Verificar que existe el archivo de configuración
if [ ! -f ".env.production" ]; then
    echo "❌ Error: No se encontró el archivo .env.production"
    echo "📝 Copia .env.example como .env.production y configura las variables"
    exit 1
fi

# Limpiar imágenes Docker antiguas
echo "🧹 Limpiando imágenes Docker antiguas..."
docker image prune -f

# Construir la imagen Docker
echo "🔨 Construyendo imagen Docker..."
docker build -t parqueadero-app:latest .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen Docker"
    exit 1
fi

# Detener contenedor existente si existe
echo "🛑 Deteniendo contenedor existente..."
docker stop parqueadero-container 2>/dev/null || true
docker rm parqueadero-container 2>/dev/null || true

# Ejecutar migraciones antes de iniciar el contenedor
echo "🔄 Ejecutando migraciones de base de datos..."
docker run --rm \
    --env-file .env.production \
    parqueadero-app:latest \
    python manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Error al ejecutar migraciones"
    exit 1
fi

# Crear superusuario si no existe
echo "👤 Verificando superusuario..."
docker run --rm \
    --env-file .env.production \
    parqueadero-app:latest \
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@parqueadero.com', 'admin123')
    print('Superusuario creado: admin/admin123')
else:
    print('Superusuario ya existe')
"

# Ejecutar el nuevo contenedor
echo "🚀 Iniciando nuevo contenedor..."
docker run -d \
    --name parqueadero-container \
    --env-file .env.production \
    -p 8081:8081 \
    --restart unless-stopped \
    parqueadero-app:latest

if [ $? -eq 0 ]; then
    echo "✅ Despliegue completado exitosamente!"
    echo "🌐 La aplicación está disponible en:"
    echo "   - http://173.212.208.35:8081"
    echo "   - https://parqueadero.sufactura.store"
    echo ""
    echo "👤 Credenciales de administrador:"
    echo "   Usuario: admin"
    echo "   Contraseña: admin123"
    echo ""
    echo "📊 Para ver los logs:"
    echo "   docker logs -f parqueadero-container"
    echo ""
    echo "🔧 Para acceder al contenedor:"
    echo "   docker exec -it parqueadero-container bash"
    echo ""
    echo "🔄 Para reiniciar el contenedor:"
    echo "   docker restart parqueadero-container"
else
    echo "❌ Error al iniciar el contenedor"
    exit 1
fi