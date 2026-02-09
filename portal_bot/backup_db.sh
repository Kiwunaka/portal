#!/bin/bash
# Ежедневный бэкап портала
# Добавить в crontab: 0 3 * * * /root/portal_bot/backup_db.sh

BACKUP_DIR="/root/backups"
DB_PATH="/root/portal_bot/portal.db"
DATE=$(date +%Y-%m-%d_%H-%M)
KEEP_DAYS=7

# Создать папку если нет
mkdir -p $BACKUP_DIR

# Создать бэкап
cp $DB_PATH "$BACKUP_DIR/portal_$DATE.db"

# Сжать
gzip "$BACKUP_DIR/portal_$DATE.db"

# Удалить старые бэкапы (старше KEEP_DAYS дней)
find $BACKUP_DIR -name "portal_*.db.gz" -mtime +$KEEP_DAYS -delete

echo "Backup done: portal_$DATE.db.gz"
