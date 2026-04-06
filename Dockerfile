FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema (incluyendo para pdf2image)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app.py .
COPY config/ config/
COPY core/ core/
COPY ui/ ui/

# Exponer puerto
EXPOSE 8501

# Configuración de Streamlit
RUN mkdir -p ~/.streamlit
RUN echo "[server]\n\
headless = true\n\
port = 8501\n\
enableXsrfProtection = false\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml

# Comando para ejecutar
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
