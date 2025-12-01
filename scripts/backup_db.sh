#!/bin/bash

# バックアップディレクトリ
BACKUP_DIR="./backups"
DB_FILE="./instance/hirakata_bot.sqlite"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ディレクトリ作成
mkdir -p $BACKUP_DIR

# バックアップ実行
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/hirakata_bot_$TIMESTAMP.sqlite"
    echo "Backup created: $BACKUP_DIR/hirakata_bot_$TIMESTAMP.sqlite"
    
    # 古いバックアップの削除（7日以上前）
    find $BACKUP_DIR -name "hirakata_bot_*.sqlite" -mtime +7 -delete
else
    echo "Database file not found: $DB_FILE"
fi
