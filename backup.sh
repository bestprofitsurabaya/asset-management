#!/bin/bash

# Script backup database

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_FILE="./data/bpf_ac_ai_system.db"

# Buat direktori backup jika belum ada
mkdir -p $BACKUP_DIR

# Backup database
if [ -f "$DB_FILE" ]; then
    cp $DB_FILE "$BACKUP_DIR/bpf_ac_ai_system_$TIMESTAMP.db"
    echo "? Database backed up to $BACKUP_DIR/bpf_ac_ai_system_$TIMESTAMP.db"
    
    # Hapus backup lebih dari 30 hari
    find $BACKUP_DIR -name "*.db" -mtime +30 -delete
    echo "??? Removed backups older than 30 days"
else
    echo "? Database file not found!"
fi