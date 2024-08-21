# Python 3.11 Slim imajını kullan
FROM python:3.11-slim

# Çalışma dizinini oluştur
WORKDIR /app

# Gereksinimleri yükle
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Projeyi kopyala
COPY . .

# Botu çalıştır
CMD ["python", "biso.py"]
