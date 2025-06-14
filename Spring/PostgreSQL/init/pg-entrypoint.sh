#!/bin/bash
set -e

DB_NAME="postgres"
DUMP_FILE="/backups/latest.dump"
DB_INIT_FILE="/docker-entrypoint-initdb.d/init.sql"

# 先啟動 PostgreSQL（背景）
/usr/local/bin/docker-entrypoint.sh postgres &
pid="$!"

echo "等待 PostgreSQL 準備就緒..."
until pg_isready -U "$POSTGRES_USER"; do sleep 1; done
echo "PostgreSQL 已啟動"

if [ -f "$DUMP_FILE" ]; then
  echo "偵測到備份檔，還原中：$DUMP_FILE"
  pg_restore -U "$POSTGRES_USER" -d "$DB_NAME" --clean "$DUMP_FILE"
  echo "還原完成"
else
  echo "無備份，初始化資料表..."

  psql -U "$POSTGRES_USER" -d "$DB_NAME" -f "$DB_INIT_FILE"

  echo "初始化完成"
fi

# 關閉處理
shutdown_handler() {
  echo "偵測到容器停止，開始備份..."

  timestamp=$(date +%Y%m%d_%H%M%S)
  backup_dir="/backups/$timestamp"
  mkdir -p "$backup_dir"

  echo "等待 PostgreSQL 準備好..."
  until pg_isready -U "$POSTGRES_USER"; do sleep 1; done

  pg_dump -U "$POSTGRES_USER" -F c -Z 9 -f "$backup_dir/backup.dump" postgres
  cp "$backup_dir/backup.dump" $DUMP_FILE

  echo "備份完成：$backup_dir/backup.dump"

  # 結束 PostgreSQL 主行程
  kill "$pid"
  wait "$pid"
  exit 0
}

# 註冊 signal trap
trap shutdown_handler SIGTERM SIGINT

# 等待 PostgreSQL 程序結束
wait "$pid"