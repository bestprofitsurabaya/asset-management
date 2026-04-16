#!/bin/bash

# Setup cron job untuk auto backup setiap hari jam 1 pagi

# Buat script backup harian
cat > ~/asset_management/daily-backup.sh << 'EOF'
#!/bin/bash
cd ~/asset_management
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
docker exec bpf-ac-system cp /app/data/bpf_ac_ai_system.db /app/backups/auto_backup_${TIMESTAMP}.db
# Keep only last 7 days of auto backups
docker exec bpf-ac-system find /app/backups -name "auto_backup_*.db" -mtime +7 -delete
EOF

chmod +x ~/asset_management/daily-backup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 1 * * * /home/it-ef/asset_management/daily-backup.sh") | crontab -

echo "? Cron job installed. Daily backup at 1 AM"