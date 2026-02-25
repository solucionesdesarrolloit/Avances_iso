# Usa una imagen base de Python ligera
FROM python:3.11-slim

# Crea un directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto a /app
COPY . /app

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto de Streamlit
EXPOSE 8501

# Configura el comando para ejecutar la app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
