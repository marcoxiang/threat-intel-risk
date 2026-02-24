# Daily Backup Example

Run backup at 02:00 UTC daily:

```cron
0 2 * * * cd /opt/ThreatIntelRisk && DATABASE_URL='postgresql://threatintel:threatintel@localhost:5432/threatintel' BACKUP_KEY='replace-me' BACKUP_DIR='/var/backups/threatintel' ./infra/backup/backup.sh >> /var/log/threatintel-backup.log 2>&1
```
