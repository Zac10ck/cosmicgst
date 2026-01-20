"""Backup service for Google Drive sync and local backups"""
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR, DATA_DIR


class BackupService:
    """Service for database backup to Google Drive and local folders"""

    # Required tables for validation
    REQUIRED_TABLES = ['company', 'products', 'customers', 'invoices', 'invoice_items']

    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.db_path = DB_PATH
        self.local_backup_dir = DATA_DIR / "local_backups"

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

    def create_local_backup(self, destination_folder: str = None) -> dict:
        """
        Create backup to user-specified local folder

        Args:
            destination_folder: Path to backup folder. If None, uses default local_backups folder

        Returns:
            dict with status and details
        """
        try:
            if not self.db_path.exists():
                return {
                    'success': False,
                    'error': 'Database file not found'
                }

            # Use provided folder or default
            if destination_folder:
                backup_dir = Path(destination_folder)
            else:
                backup_dir = self.local_backup_dir

            # Create directory if needed
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_file = backup_dir / f"billing_{timestamp}.db"

            # Copy database
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

    def get_local_backup_list(self, folder_path: str = None) -> list:
        """
        List backups from a local folder

        Args:
            folder_path: Path to search for backups. If None, uses default local_backups folder

        Returns:
            List of backup info dicts
        """
        try:
            if folder_path:
                search_dir = Path(folder_path)
            else:
                search_dir = self.local_backup_dir

            if not search_dir.exists():
                return []

            backups = []
            for f in search_dir.glob("*.db"):
                # Validate it's a SQLite file
                validation = self.validate_backup(str(f))
                backups.append({
                    'filename': f.name,
                    'path': str(f),
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime),
                    'valid': validation['valid'],
                    'validation_message': validation.get('message', '')
                })

            backups.sort(key=lambda x: x['modified'], reverse=True)
            return backups

        except Exception as e:
            print(f"Error listing local backups: {e}")
            return []

    def validate_backup(self, backup_path: str) -> dict:
        """
        Validate backup file integrity before restore

        Args:
            backup_path: Path to backup file

        Returns:
            dict with validation result and details
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                return {
                    'valid': False,
                    'message': 'File not found'
                }

            # Check file size
            if backup_file.stat().st_size < 1000:
                return {
                    'valid': False,
                    'message': 'File too small to be valid database'
                }

            # Check SQLite magic bytes
            with open(backup_file, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3'):
                    return {
                        'valid': False,
                        'message': 'Not a valid SQLite database file'
                    }

            # Try to open and verify tables
            try:
                conn = sqlite3.connect(str(backup_file))
                cursor = conn.cursor()

                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                # Check for required tables
                missing_tables = [t for t in self.REQUIRED_TABLES if t not in tables]
                if missing_tables:
                    conn.close()
                    return {
                        'valid': False,
                        'message': f'Missing tables: {", ".join(missing_tables)}'
                    }

                # Run integrity check
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                if integrity != 'ok':
                    conn.close()
                    return {
                        'valid': False,
                        'message': f'Database integrity check failed: {integrity}'
                    }

                conn.close()

                return {
                    'valid': True,
                    'message': 'Backup is valid',
                    'tables': tables
                }

            except sqlite3.Error as e:
                return {
                    'valid': False,
                    'message': f'SQLite error: {e}'
                }

        except Exception as e:
            return {
                'valid': False,
                'message': f'Validation error: {e}'
            }

    def get_backup_info(self, backup_path: str) -> dict:
        """
        Get detailed information about a backup file

        Args:
            backup_path: Path to backup file

        Returns:
            dict with backup details (invoice count, date range, etc.)
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                return {'error': 'File not found'}

            # Validate first
            validation = self.validate_backup(backup_path)
            if not validation['valid']:
                return {'error': validation['message']}

            # Get counts and info
            conn = sqlite3.connect(str(backup_file))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            info = {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'modified': datetime.fromtimestamp(backup_file.stat().st_mtime),
                'valid': True
            }

            # Count records
            cursor.execute("SELECT COUNT(*) FROM invoices")
            info['invoice_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM products")
            info['product_count'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM customers")
            info['customer_count'] = cursor.fetchone()[0]

            # Get date range of invoices
            cursor.execute("SELECT MIN(invoice_date), MAX(invoice_date) FROM invoices")
            row = cursor.fetchone()
            if row and row[0]:
                info['first_invoice_date'] = row[0]
                info['last_invoice_date'] = row[1]

            # Get company name
            cursor.execute("SELECT name FROM company LIMIT 1")
            row = cursor.fetchone()
            if row:
                info['company_name'] = row[0]

            conn.close()
            return info

        except Exception as e:
            return {'error': str(e)}

    def restore_with_validation(self, backup_path: str) -> dict:
        """
        Restore database from backup with validation

        Args:
            backup_path: Path to backup file

        Returns:
            dict with status and details
        """
        # Validate first
        validation = self.validate_backup(backup_path)
        if not validation['valid']:
            return {
                'success': False,
                'error': f'Invalid backup: {validation["message"]}'
            }

        # Get backup info for confirmation
        info = self.get_backup_info(backup_path)

        # Proceed with restore
        return self.restore_backup(backup_path)
