#!/usr/bin/env bash
# Sauvegarde PostgreSQL de la boucherie.
#
# ⚠️ Le cahier des charges (§7) impose une sauvegarde conçue DÈS l'étape 1
# et stockée HORS du Proxmox (survivre à une panne matérielle du serveur).
# Ce script produit un dump compressé horodaté + rotation locale ; le
# recopiage hors-site (rsync/rclone) est à activer ci-dessous une fois la
# cible choisie (NAS distant, stockage objet, disque externe...).
#
# Usage (sur la VM) :   ./scripts/backup.sh
# Cron conseillé :      quotidien, ex. 0 2 * * *  (à 02h00)
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_SERVICE="${DB_SERVICE:-db}"
DB_USER="${POSTGRES_USER:-boucherie}"
DB_NAME="${POSTGRES_DB:-boucherie}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/boucherie-$STAMP.sql.gz"

echo "[backup] dump $DB_NAME -> $OUT"
docker compose exec -T "$DB_SERVICE" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT"

echo "[backup] rotation : suppression des dumps > $RETENTION_DAYS jours"
find "$BACKUP_DIR" -name 'boucherie-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete

# --- Copie HORS-Proxmox (À ACTIVER) -----------------------------------
# Décommenter et configurer une des cibles ci-dessous. C'est ce qui rend
# la sauvegarde résiliente à une panne du serveur (exigence cahier §7).
#
# rclone copy "$OUT" remote-boucherie:backups/       # stockage objet / cloud
# rsync -a "$OUT" user@nas-distant:/volumes/backups/ # NAS hors-Proxmox
# ----------------------------------------------------------------------

echo "[backup] OK : $OUT ($(du -h "$OUT" | cut -f1))"
echo "[backup] ⚠️ copie hors-site non configurée — voir la section À ACTIVER."
