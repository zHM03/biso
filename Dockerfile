# Kullanılacak temel imaj
FROM python:3.11-slim

# Çalışma dizinini oluştur
WORKDIR /app

# Gereksinimlerinizi kopyalayın
COPY requirements.txt .

# Gereksinimleri yükleyin
RUN pip install --no-cache-dir -r requirements.txt

# FFmpeg ve FFprobe'yi yükleyin
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Proje dosyalarınızı kopyalayın
COPY . .

# Komutları çalıştırın
CMD ["python", "biso.py"]
