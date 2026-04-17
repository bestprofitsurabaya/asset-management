#!/bin/bash

echo "========================================="
echo "?? BPF Asset Management System Deployment"
echo "========================================="

# Create required directories
echo "?? Membuat direktori yang diperlukan..."
mkdir -p data config logs data/backups

# Set permissions
echo "?? Mengatur permissions..."
chmod -R 755 data config logs

# Stop existing containers if any
echo "?? Menghentikan container yang sedang berjalan..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "??? Membangun dan menjalankan container..."
docker-compose up -d --build

# Check if container is running
sleep 5
if docker ps | grep -q "bpf-asset-system"; then
    echo ""
    echo "========================================="
    echo "? DEPLOYMENT BERHASIL!"
    echo "========================================="
    echo ""
    echo "?? Akses aplikasi di: http://$(hostname -I | awk '{print $1}'):8501"
    echo ""
    echo "?? Default Credentials:"
    echo "   - Admin    : admin / admin123"
    echo "   - Teknisi  : teknisi / teknisi123"
    echo "   - Manager  : manager / manager123"
    echo "   - Demo     : demo / demo123"
    echo ""
    echo "?? Perintah Berguna:"
    echo "   - Lihat log    : docker-compose logs -f"
    echo "   - Stop service : docker-compose down"
    echo "   - Restart      : docker-compose restart"
    echo "   - Status       : docker-compose ps"
    echo "========================================="
else
    echo "? Deployment gagal. Cek log dengan: docker-compose logs"
fi