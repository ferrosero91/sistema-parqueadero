#!/bin/bash

# Script de actualización rápida para el sistema de parqueadero
echo "🔄 Actualizando sistema de parqueadero..."

# Verificar que el contenedor esté corriendo
if ! docker ps | grep -q parqueadero-container; then
    echo "❌ El contenedor no está corriendo. Ejecuta ./deploy.sh primero"
    exit 1
fi

# Construir nueva imagen
echo "🔨 Construyendo nueva imagen..."
docker build -t parqueadero-app:latest .

if [ $? -ne 0 ]; then
    echo "❌ Error al construir la imagen"
    exit 1
fi

# Ejecutar migraciones si es necesario
echo "🔄 Ejecutando migraciones..."
docker run --rm \
    --env-file .env.production \
    parqueadero-app:latest \
    python manage.py migrate

# Detener contenedor actual
echo "🛑 Deteniendo contenedor actual..."
docker stop parqueadero-container

# Remover contenedor anterior
docker rm parqueadero-container

# Iniciar nuevo contenedor
echo "🚀 Iniciando contenedor actualizado..."
docker run -d \
    --name parqueadero-container \
    --env-file .env.production \
    -p 8081:8081 \
    --restart unless-stopped \
    parqueadero-app:latest

if [ $? -eq 0 ]; then
    echo "✅ Actualización completada exitosamente!"
    echo "🌐 La aplicación está disponible en:"
    echo "   - http://173.212.208.35:8081"
    echo "   - https://parqueadero.sufactura.store"
else
    echo "❌ Error al actualizar el contenedor"
    exit 1
fi