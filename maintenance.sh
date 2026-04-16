#!/bin/bash

# Script maintenance untuk BPF Asset System

echo "=== BPF Asset Management System Maintenance ==="

# Function untuk backup database
backup_db() {
    echo "?? Creating database backup..."
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    docker exec bpf-ac-system cp /app/data/bpf_ac_ai_system.db /app/backups/backup_${TIMESTAMP}.db
    echo "? Backup created: backups/backup_${TIMESTAMP}.db"
    
    # Hapus backup lama (lebih dari 30 hari)
    docker exec bpf-ac-system find /app/backups -name "backup_*.db" -mtime +30 -delete
    echo "??? Removed backups older than 30 days"
}

# Function untuk restart aplikasi
restart_app() {
    echo "?? Restarting application..."
    docker-compose restart
    echo "? Application restarted"
}

# Function untuk melihat logs
view_logs() {
    echo "?? Showing last 50 lines of logs..."
    docker-compose logs --tail=50
}

# Function untuk cek status
check_status() {
    echo "?? Checking application status..."
    docker-compose ps
    echo ""
    echo "?? Container stats:"
    docker stats --no-stream bpf-ac-system
}

# Menu
echo ""
echo "Pilih tindakan:"
echo "1) Backup Database"
echo "2) Restart Aplikasi"
echo "3) Lihat Logs"
echo "4) Cek Status"
echo "5) Exit"
echo ""
read -p "Masukkan pilihan (1-5): " choice

case $choice in
    1) backup_db ;;
    2) restart_app ;;
    3) view_logs ;;
    4) check_status ;;
    5) echo "Exit"; exit 0 ;;
    *) echo "Invalid option" ;;
esac