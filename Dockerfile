# Etapa de construcción
FROM python:3.11-slim AS builder

WORKDIR /app

# Copiamos dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt

# Etapa final
FROM python:3.11-slim

WORKDIR /app

# Copiamos paquetes del builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copiamos el resto del proyecto
COPY . .

# Crear usuario sin privilegios
RUN useradd -m myuser
USER myuser

# Recolección de estáticos y migraciones + creación de superusuario si no existe
RUN python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    echo "from django.contrib.auth import get_user_model; \
User = get_user_model(); \
User.objects.filter(username='admin').exists() or \
User.objects.create_superuser('admin', 'admin@example.com', 'Admin123')" \
| python manage.py shell

# Comando para arrancar gunicorn
CMD ["gunicorn", "parking_system.wsgi:application", "--bind", "0.0.0.0:8081"]

