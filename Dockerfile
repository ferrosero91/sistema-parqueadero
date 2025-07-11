# Fase 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt

# Fase 2: Contenedor final
FROM python:3.11-slim
WORKDIR /app

# Crear usuario sin privilegios
RUN useradd -m myuser

# Copiar dependencias del builder
COPY --from=builder /root/.local /home/myuser/.local

# Copiar el proyecto
COPY . .

# Crear carpetas necesarias
RUN mkdir -p /app/static /app/staticfiles /app/media && \
    chown -R myuser:myuser /app

# Establecer PATH y permisos
ENV PATH="/home/myuser/.local/bin:$PATH"
USER myuser

# Variables de entorno para superusuario
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=Admin123

# Crear script de inicio
RUN echo '#!/bin/bash
set -e

echo "Starting Django application..."

# Aplicar migraciones
echo "Applying migrations..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Crear superusuario solo si no existe
echo "Creating superuser if not exists..."
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username="$DJANGO_SUPERUSER_USERNAME").exists():
    User.objects.create_superuser("$DJANGO_SUPERUSER_USERNAME", "$DJANGO_SUPERUSER_EMAIL", "$DJANGO_SUPERUSER_PASSWORD")
    print("Superuser created successfully")
else:
    print("Superuser already exists")
EOF

echo "Starting Gunicorn server..."
exec gunicorn parking_system.wsgi:application \
    --bind 0.0.0.0:8081 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
' > /app/start.sh && chmod +x /app/start.sh

# Exponer puerto
EXPOSE 8081

# Comando de inicio
CMD ["/app/start.sh"]
