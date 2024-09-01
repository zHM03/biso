# Python 3.11 Slim imajını kullan
FROM python:3.11-slim

# Çalışma dizinini oluştur
WORKDIR /app

# FFmpeg yükle
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Gereksinimleri yükle
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Projeyi kopyala
COPY . .

# Botu çalıştır
CMD ["python", "biso.py"]
