# Imagen base de Python
FROM python:3.11

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar todos los archivos del proyecto al contenedor
COPY . .

# Actualizar pip e instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Recoger archivos estáticos al momento de construir la imagen
RUN python manage.py collectstatic --noinput

# Exponer el puerto 8080 porque Coolify ya usa el 8000 localmente
EXPOSE 8080

# Comando para ejecutar la aplicación con Gunicorn en el puerto 8080
CMD ["gunicorn", "parking_system.wsgi:application", "--bind", "0.0.0.0:8080"]
