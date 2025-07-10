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

# Crear superusuario automáticamente si no existe
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=Admin123

# Comando de inicio
CMD sh -c "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    python manage.py createsuperuser --noinput || true && \
    gunicorn parking_system.wsgi:application --bind 0.0.0.0:8081"
