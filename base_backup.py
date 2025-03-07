#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import shutil
from datetime import datetime
import configparser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresBackup:
    def __init__(self, backup_root, host='localhost', port=5432, user='postgres'):
        self.backup_root = Path(backup_root)
        self.host = host
        self.port = port
        self.user = user
        self.base_backup_dir = self.backup_root / 'base'
        self.wal_archive_dir = self.backup_root / 'wal_archive'
        
    def check_pg_basebackup_exists(self):
        """Verify pg_basebackup is available"""
        try:
            subprocess.run(['pg_basebackup', '--version'], capture_output=True)
            return True
        except FileNotFoundError:
            logger.error("pg_basebackup not found. Please ensure PostgreSQL tools are installed.")
            return False

    def validate_postgres_connection(self):
        """Check PostgreSQL connection and permissions"""
        try:
            cmd = [
                'psql',
                '-h', self.host,
                '-p', str(self.port),
                '-U', self.user,
                '-c', "SELECT pg_is_in_recovery(), current_setting('data_directory')"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PostgreSQL connection failed: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection validation failed: {str(e)}")
            return False

    def setup_wal_archiving(self):
        """Configure WAL archiving in PostgreSQL"""
        try:
            # Create archive directory if it doesn't exist
            self.wal_archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Get PostgreSQL config file location
            cmd = [
                'psql',
                '-h', self.host,
                '-p', str(self.port),
                '-U', self.user,
                '-tAc', "SHOW config_file"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            postgresql_conf = result.stdout.strip()
            
            # Modify postgresql.conf
            config = configparser.ConfigParser()
            config.read(postgresql_conf)
            
            updates = {
                'wal_level': 'replica',
                'archive_mode': 'on',
                'archive_command': f"cp %p {self.wal_archive_dir}/%f",
                'max_wal_senders': '3'
            }
            
            modified = False
            with open(postgresql_conf, 'r') as f:
                content = f.read()
            
            for key, value in updates.items():
                if key not in content:
                    content += f"\n{key} = '{value}'"
                    modified = True
            
            if modified:
                # Backup original config
                shutil.copy2(postgresql_conf, f"{postgresql_conf}.bak")
                
                # Write updated config
                with open(postgresql_conf, 'w') as f:
                    f.write(content)
                
                logger.info("WAL archiving configured. PostgreSQL restart required.")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WAL archiving: {str(e)}")
            return False

    def create_backup_directory(self):
        """Create timestamped backup directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.base_backup_dir / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def perform_base_backup(self, wal_method='fetch'):
        """
        Perform PostgreSQL base backup using pg_basebackup
        
        Args:
            wal_method (str): WAL handling method ('fetch' or 'stream')
        
        Returns:
            bool: True if backup was successful, False otherwise
        """
        if not self.check_pg_basebackup_exists():
            return False

        if not self.validate_postgres_connection():
            return False

        backup_dir = self.create_backup_directory()
        
        try:
            cmd = [
                'pg_basebackup',
                '-h', self.host,
                '-p', str(self.port),
                '-U', self.user,
                '-D', str(backup_dir),
                '-Ft',  # tar format
                '-z',   # compression
                '-P',   # progress
                '-X', wal_method
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode == 0:
                logger.info(f"Base backup successfully created at: {backup_dir}")
                return True
            else:
                logger.error(f"Base backup failed: {process.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Base backup failed with error: {str(e)}")
            return False

    def cleanup_old_backups(self, keep_count=5):
        """Remove old backups keeping only the specified number of recent ones"""
        try:
            backups = sorted(self.base_backup_dir.glob('*'))
            to_delete = backups[:-keep_count] if len(backups) > keep_count else []
            
            for backup in to_delete:
                if backup.is_dir():
                    shutil.rmtree(backup)
                else:
                    backup.unlink()
                logger.info(f"Removed old backup: {backup}")
                
            return True
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return False

def main():
    if len(sys.argv) < 2:
        print("""Usage: python base_backup.py <backup_root_dir> [options]
Options:
  --wal-method=fetch|stream    WAL handling method (default: fetch)
  --keep-backups=N            Number of backups to keep (default: 5)
  --setup-archiving           Configure WAL archiving
        """)
        sys.exit(1)

    backup_root = sys.argv[1]
    wal_method = 'fetch'
    keep_backups = 5
    setup_archiving = False

    # Parse command line arguments
    for arg in sys.argv[2:]:
        if arg.startswith('--wal-method='):
            wal_method = arg.split('=')[1]
        elif arg.startswith('--keep-backups='):
            keep_backups = int(arg.split('=')[1])
        elif arg == '--setup-archiving':
            setup_archiving = True

    backup = PostgresBackup(backup_root)

    if setup_archiving:
        if backup.setup_wal_archiving():
            logger.info("WAL archiving configured successfully")
        else:
            sys.exit(1)

    if backup.perform_base_backup(wal_method):
        backup.cleanup_old_backups(keep_backups)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 