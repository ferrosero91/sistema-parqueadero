# Imagen base de Python
FROM python:3.11

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiar archivos al contenedor
COPY . .

# Actualizar pip e instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exponer puerto 8000
EXPOSE 8000

# Comando para ejecutar la app con Gunicorn
CMD ["gunicorn", "parking_system.wsgi:application", "--bind", "0.0.0.0:8000"]
