#!/bin/bash

# Script untuk deploy aplikasi BPF Asset Management

echo "?? Starting BPF Asset Management System Deployment..."

# Buat direktori yang diperlukan
mkdir -p data
mkdir -p config

# Set permission
chmod 755 data

# Build dan jalankan container
echo "?? Building Docker image..."
docker-compose build

# Stop container lama jika ada
echo "?? Stopping old container..."
docker-compose down

# Jalankan container baru
echo "?? Starting new container..."
docker-compose up -d

# Cek status
echo "? Checking container status..."
docker-compose ps

# Tampilkan logs
echo "?? Recent logs:"
docker-compose logs --tail=20

echo ""
echo "?? Aplikasi berjalan di: http://localhost:8501"
echo "?? Untuk melihat logs: docker-compose logs -f"
echo "?? Untuk stop: docker-compose down"