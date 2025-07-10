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

# Copiar dependencias
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
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting Django application..."\n\
\n\
# Aplicar migraciones\n\
echo "Applying migrations..."\n\
python manage.py migrate --noinput\n\
\n\
# Recopilar archivos estáticos\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
# Crear superusuario solo si no existe\n\
echo "Creating superuser if not exists..."\n\
python manage.py shell << EOF\n\
from django.contrib.auth.models import User\n\
if not User.objects.filter(username="$DJANGO_SUPERUSER_USERNAME").exists():\n\
    User.objects.create_superuser("$DJANGO_SUPERUSER_USERNAME", "$DJANGO_SUPERUSER_EMAIL", "$DJANGO_SUPERUSER_PASSWORD")\n\
    print("Superuser created successfully")\n\
else:\n\
    print("Superuser already exists")\n\
EOF\n\
\n\
echo "Starting Gunicorn server..."\n\
exec gunicorn parking_system.wsgi:application \\\n\
    --bind 0.0.0.0:8081 \\\n\
    --workers 3 \\\n\
    --timeout 120 \\\n\
    --keepalive 2 \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 50 \\\n\
    --access-logfile - \\\n\
    --error-logfile -\n\
' > /app/start.sh && chmod +x /app/start.sh

# Exponer puerto
EXPOSE 8081

# Comando de inicio
CMD ["/app/start.sh"]
