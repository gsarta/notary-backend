FROM python:3.9-slim-buster

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para FFmpeg
# FFmpeg es crucial para pydub
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requerimientos e instala las dependencias de Python
# Esto se hace primero para aprovechar el cache de Docker si los requirements no cambian
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu aplicación al directorio de trabajo en el contenedor
# El .dockerignore ayudará a no copiar archivos innecesarios
COPY . .

# Expone el puerto en el que la aplicación Gunicorn escuchará.
EXPOSE 8000

# Comando para ejecutar la aplicación usando Gunicorn
# 'app:app' indica que Gunicorn debe buscar una variable 'app' dentro del módulo 'app.py'
# '-b 0.0.0.0:8000' le dice a Gunicorn que escuche en todas las interfaces en el puerto 8000
# '--workers 4' define el número de procesos worker de Gunicorn (ajustar según la CPU y memoria)
# '--timeout 120' es un timeout para las solicitudes (útil para transcripciones largas)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "300", "run:app"]

# Notas:
# - 'app:app' asume que tu archivo principal en la raíz es app.py y la instancia de Flask se llama 'app'.
# - Si tu app se ejecuta a través de run.py y la instancia se crea en app/__init__.py,
#   el CMD podría necesitar ser ajustado (ej. python run.py si run.py es el ejecutable de gunicorn,
#   o si gunicorn puede apuntar a app/__init__.py:create_app() si es una factory function)