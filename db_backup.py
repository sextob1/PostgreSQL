#!/usr/bin/env python3

import os
import sys
import subprocess
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup_filename():
    """Generate a timestamp-based backup filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'backup_{timestamp}.sql'

def check_pg_dump_exists():
    """Verify pg_dump is available in the system"""
    try:
        subprocess.run(['pg_dump', '--version'], capture_output=True)
        return True
    except FileNotFoundError:
        logger.error("pg_dump not found. Please ensure PostgreSQL tools are installed.")
        return False

def validate_backup_dir(dir_path):
    """Ensure backup directory exists and is writable"""
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except Exception as e:
            logger.error(f"Failed to create backup directory: {e}")
            return False
    
    if not os.access(dir_path, os.W_OK):
        logger.error(f"Backup directory {dir_path} is not writable")
        return False
    return True

def perform_backup(db_name, output_dir):
    """
    Perform PostgreSQL database backup using pg_dump
    
    Args:
        db_name (str): Name of the database to backup
        output_dir (str): Directory to store the backup file
    
    Returns:
        bool: True if backup was successful, False otherwise
    """
    if not check_pg_dump_exists():
        return False

    if not validate_backup_dir(output_dir):
        return False

    backup_file = os.path.join(output_dir, create_backup_filename())
    
    try:
        cmd = [
            'pg_dump',
            '--dbname=postgresql://postgres:postgres@localhost:5432/' + db_name,
            '-F', 'p',  # plain text format
            '-f', backup_file
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            logger.info(f"Backup successfully created at: {backup_file}")
            return True
        else:
            logger.error(f"Backup failed: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Backup failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python db_backup.py <database_name> <backup_directory>")
        sys.exit(1)
    
    database_name = sys.argv[1]
    backup_dir = sys.argv[2]
    
    perform_backup(database_name, backup_dir) 