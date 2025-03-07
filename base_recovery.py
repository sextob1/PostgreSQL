#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import shutil
from datetime import datetime
from pathlib import Path
import tarfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresRecovery:
    def __init__(self, backup_root, pgdata=None, host='localhost', port=5432, user='postgres'):
        self.backup_root = Path(backup_root)
        self.base_backup_dir = self.backup_root / 'base'
        self.wal_archive_dir = self.backup_root / 'wal_archive'
        self.pgdata = Path(pgdata) if pgdata else Path('/var/lib/postgresql/data')
        self.host = host
        self.port = port
        self.user = user

    def find_latest_backup(self):
        """Find the most recent base backup"""
        try:
            backups = sorted(self.base_backup_dir.glob('*'))
            if not backups:
                logger.error("No backups found in backup directory")
                return None
            return backups[-1]
        except Exception as e:
            logger.error(f"Failed to find latest backup: {str(e)}")
            return None

    def validate_backup(self, backup_path):
        """Validate backup files and WAL archives"""
        try:
            # Check base backup files
            base_files = list(Path(backup_path).glob('base.tar.gz'))
            wal_files = list(Path(backup_path).glob('pg_wal.tar.gz'))
            
            if not base_files or not wal_files:
                logger.error("Backup files are incomplete")
                return False
            
            # Verify base backup integrity
            with tarfile.open(base_files[0], 'r:gz') as tar:
                if tar.getmembers()[0].name.startswith('pg_'):
                    return True
                    
            logger.error("Backup files appear to be corrupted")
            return False
            
        except Exception as e:
            logger.error(f"Backup validation failed: {str(e)}")
            return False

    def stop_postgres(self):
        """Stop PostgreSQL server"""
        try:
            subprocess.run(['pg_ctl', 'stop', '-D', str(self.pgdata)], check=True)
            logger.info("PostgreSQL server stopped")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop PostgreSQL: {str(e)}")
            return False

    def configure_recovery(self, backup_path, target_time=None):
        """Configure recovery settings"""
        try:
            recovery_conf = self.pgdata / 'postgresql.auto.conf'
            
            settings = [
                "restore_command = 'cp {}/wal_archive/%f %p'".format(self.backup_root),
                "recovery_target_action = 'promote'"
            ]
            
            if target_time:
                settings.append(f"recovery_target_time = '{target_time}'")
            
            with open(recovery_conf, 'a') as f:
                for setting in settings:
                    f.write(f"{setting}\n")
            
            # Create recovery signal file
            (self.pgdata / 'recovery.signal').touch()
            
            logger.info("Recovery configuration created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure recovery: {str(e)}")
            return False

    def restore_base_backup(self, backup_path):
        """Restore base backup files"""
        try:
            # Clear PGDATA directory
            if self.pgdata.exists():
                shutil.rmtree(self.pgdata)
            self.pgdata.mkdir(parents=True, exist_ok=True)
            
            # Extract base backup
            base_tar = next(Path(backup_path).glob('base.tar.gz'))
            with tarfile.open(base_tar, 'r:gz') as tar:
                tar.extractall(path=self.pgdata)
            
            # Extract WAL files
            wal_tar = next(Path(backup_path).glob('pg_wal.tar.gz'))
            with tarfile.open(wal_tar, 'r:gz') as tar:
                tar.extractall(path=self.pgdata)
            
            logger.info("Base backup restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore base backup: {str(e)}")
            return False

    def start_postgres(self):
        """Start PostgreSQL server"""
        try:
            subprocess.run(['pg_ctl', 'start', '-D', str(self.pgdata)], check=True)
            logger.info("PostgreSQL server started in recovery mode")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start PostgreSQL: {str(e)}")
            return False

    def perform_recovery(self, backup_path=None, target_time=None):
        """
        Perform full recovery from base backup and WAL archives
        
        Args:
            backup_path: Path to specific backup, or None for latest
            target_time: Optional timestamp for point-in-time recovery
        
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        if not backup_path:
            backup_path = self.find_latest_backup()
            if not backup_path:
                return False

        if not self.validate_backup(backup_path):
            return False

        if not self.stop_postgres():
            return False

        if not self.restore_base_backup(backup_path):
            return False

        if not self.configure_recovery(backup_path, target_time):
            return False

        if not self.start_postgres():
            return False

        logger.info("Recovery process initiated successfully")
        logger.info("Check PostgreSQL logs for recovery progress")
        return True

def main():
    if len(sys.argv) < 2:
        print("""Usage: python base_recovery.py <backup_root_dir> [options]
Options:
  --pgdata=PATH              PostgreSQL data directory
  --target-time='TIMESTAMP'  Recover to specific point in time
  --backup-path=PATH         Use specific backup (default: latest)
        """)
        sys.exit(1)

    backup_root = sys.argv[1]
    pgdata = None
    target_time = None
    backup_path = None

    # Parse command line arguments
    for arg in sys.argv[2:]:
        if arg.startswith('--pgdata='):
            pgdata = arg.split('=')[1]
        elif arg.startswith('--target-time='):
            target_time = arg.split('=')[1]
        elif arg.startswith('--backup-path='):
            backup_path = arg.split('=')[1]

    recovery = PostgresRecovery(backup_root, pgdata)
    
    if not recovery.perform_recovery(backup_path, target_time):
        sys.exit(1)

if __name__ == "__main__":
    main() 