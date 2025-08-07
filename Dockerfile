# Usar Python 3.11 slim como imagen base
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/static /app/staticfiles /app/media

# Variables de entorno por defecto para el superusuario
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@parqueadero.com
ENV DJANGO_SUPERUSER_PASSWORD=admin123

# Crear script de inicio optimizado
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Iniciando aplicación Django..."\n\
\n\
# Verificar conexión a la base de datos\n\
echo "🔍 Verificando conexión a la base de datos..."\n\
python manage.py check --database default\n\
\n\
# Aplicar migraciones\n\
echo "📦 Aplicando migraciones..."\n\
python manage.py migrate --noinput\n\
\n\
# Recopilar archivos estáticos\n\
echo "📁 Recopilando archivos estáticos..."\n\
python manage.py collectstatic --noinput --clear\n\
\n\
# Crear superusuario si no existe\n\
echo "👤 Verificando superusuario..."\n\
python manage.py shell -c "\n\
from django.contrib.auth.models import User\n\
import os\n\
username = os.environ.get(\"DJANGO_SUPERUSER_USERNAME\", \"admin\")\n\
email = os.environ.get(\"DJANGO_SUPERUSER_EMAIL\", \"admin@parqueadero.com\")\n\
password = os.environ.get(\"DJANGO_SUPERUSER_PASSWORD\", \"admin123\")\n\
if not User.objects.filter(username=username).exists():\n\
    User.objects.create_superuser(username, email, password)\n\
    print(f\"✅ Superusuario creado: {username}\")\n\
else:\n\
    print(f\"ℹ️  Superusuario ya existe: {username}\")\n\
"\n\
\n\
echo "🌐 Iniciando servidor Gunicorn..."\n\
exec gunicorn parking_system.wsgi:application \\\n\
    --bind 0.0.0.0:8081 \\\n\
    --workers 3 \\\n\
    --worker-class sync \\\n\
    --timeout 120 \\\n\
    --keep-alive 5 \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 100 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level info\n\
' > /app/start.sh && chmod +x /app/start.sh

# Exponer puerto 8081
EXPOSE 8081

# Comando de inicio
CMD ["/app/start.sh"]
