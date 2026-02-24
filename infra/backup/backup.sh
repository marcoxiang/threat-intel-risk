#!/usr/bin/env sh
set -eu

TS="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${BACKUP_DIR:-/tmp/threatintel-backups}"
KEY="${BACKUP_KEY:-change-me}"

mkdir -p "$OUT_DIR"

PG_DUMP_FILE="$OUT_DIR/postgres-$TS.sql"
ARTIFACT_FILE="$OUT_DIR/uploads-$TS.tar.gz"

pg_dump "$DATABASE_URL" > "$PG_DUMP_FILE"
tar -czf "$ARTIFACT_FILE" uploads

openssl enc -aes-256-cbc -salt -pbkdf2 -in "$PG_DUMP_FILE" -out "$PG_DUMP_FILE.enc" -k "$KEY"
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$ARTIFACT_FILE" -out "$ARTIFACT_FILE.enc" -k "$KEY"

rm -f "$PG_DUMP_FILE" "$ARTIFACT_FILE"
echo "Backups written to $OUT_DIR"
