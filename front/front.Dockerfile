# Imagen base ligera de Python
FROM python:3.10-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivo de dependencias
COPY requirements-front.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements-front.txt

# Copiar el resto del código (incluyendo el .py)
COPY . .

# Expone el puerto que Cloud Run espera
EXPOSE 8080

# Ejecutar Streamlit escuchando en 0.0.0.0:8080 (requerido por Cloud Run)
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]