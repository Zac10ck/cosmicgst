"""Backup service for Google Drive sync"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR, DATA_DIR


class BackupService:
    """Service for database backup to Google Drive"""

    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.db_path = DB_PATH

    def setup_backup_directory(self) -> bool:
        """
        Set up the backup directory structure

        Returns True if Google Drive folder exists and is accessible
        """
        try:
            # Check if Google Drive folder exists
            google_drive_base = Path.home() / "Google Drive"

            # Also check for "Google Drive" in common locations on Windows
            possible_paths = [
                Path.home() / "Google Drive",
                Path.home() / "GoogleDrive",
                Path("G:/My Drive"),  # Google Drive desktop app
                Path.home() / "My Drive",
            ]

            for path in possible_paths:
                if path.exists():
                    self.backup_dir = path / "Billing Backup"
                    break

            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            (self.backup_dir / "backups").mkdir(exist_ok=True)

            return True
        except Exception as e:
            print(f"Backup setup error: {e}")
            return False

    def create_backup(self, manual: bool = False) -> dict:
        """
        Create a backup of the database

        Args:
            manual: If True, create timestamped backup in backups folder

        Returns:
            dict with status and details
        """
        try:
            if not self.db_path.exists():
                return {
                    'success': False,
                    'error': 'Database file not found'
                }

            self.setup_backup_directory()

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

            if manual:
                # Create timestamped backup
                backup_file = self.backup_dir / "backups" / f"billing_{timestamp}.db"
                shutil.copy2(self.db_path, backup_file)
            else:
                # Copy to main sync location
                backup_file = self.backup_dir / "billing.db"
                shutil.copy2(self.db_path, backup_file)

            return {
                'success': True,
                'backup_path': str(backup_file),
                'timestamp': timestamp,
                'size': backup_file.stat().st_size
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_backup_list(self) -> list:
        """Get list of available backups"""
        try:
            backups_dir = self.backup_dir / "backups"
            if not backups_dir.exists():
                return []

            backups = []
            for f in backups_dir.glob("billing_*.db"):
                backups.append({
                    'filename': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime)
                })

            # Sort by date, newest first
            backups.sort(key=lambda x: x['modified'], reverse=True)

            return backups

        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

    def restore_backup(self, backup_path: str) -> dict:
        """
        Restore database from a backup

        Args:
            backup_path: Path to backup file

        Returns:
            dict with status and details
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }

            # Create backup of current database before restore
            if self.db_path.exists():
                current_backup = DATA_DIR / f"billing_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.db_path, current_backup)

            # Restore
            shutil.copy2(backup_file, self.db_path)

            return {
                'success': True,
                'restored_from': backup_path
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_old_backups(self, keep_days: int = 30):
        """
        Remove backups older than specified days

        Args:
            keep_days: Number of days to keep backups
        """
        try:
            backups_dir = self.backup_dir / "backups"
            if not backups_dir.exists():
                return

            cutoff = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

            for f in backups_dir.glob("billing_*.db"):
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    print(f"Deleted old backup: {f.name}")

        except Exception as e:
            print(f"Cleanup error: {e}")

    def get_backup_status(self) -> dict:
        """Get current backup status"""
        try:
            # Check if Google Drive is available
            google_drive_available = self.setup_backup_directory()

            # Check last backup time
            main_backup = self.backup_dir / "billing.db"
            last_backup = None
            if main_backup.exists():
                last_backup = datetime.fromtimestamp(main_backup.stat().st_mtime)

            backups = self.get_backup_list()

            return {
                'google_drive_available': google_drive_available,
                'backup_dir': str(self.backup_dir),
                'last_backup': last_backup,
                'backup_count': len(backups),
                'total_size': sum(b['size'] for b in backups)
            }

        except Exception as e:
            return {
                'google_drive_available': False,
                'error': str(e)
            }
