#!/usr/bin/env python3

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_psql_exists():
    """Verify psql is available in the system"""
    try:
        subprocess.run(['psql', '--version'], capture_output=True)
        return True
    except FileNotFoundError:
        logger.error("psql not found. Please ensure PostgreSQL tools are installed.")
        return False

def validate_backup_file(file_path):
    """Ensure backup file exists and is readable"""
    if not os.path.exists(file_path):
        logger.error(f"Backup file not found: {file_path}")
        return False
    
    if not os.path.isfile(file_path):
        logger.error(f"Specified path is not a file: {file_path}")
        return False
    
    if not os.access(file_path, os.R_OK):
        logger.error(f"Backup file is not readable: {file_path}")
        return False
    
    return True

def create_database_if_missing(db_name):
    """Create the database if it doesn't exist"""
    try:
        # Check if database exists
        check_cmd = [
            'psql',
            '--dbname=postgresql://postgres:postgres@localhost:5432/postgres',
            '-tAc',
            f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"
        ]
        
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if not result.stdout.strip():
            # Database doesn't exist, create it
            create_cmd = [
                'createdb',
                '--host=localhost',
                '--port=5432',
                '--username=postgres',
                db_name
            ]
            
            subprocess.run(create_cmd, capture_output=True, text=True)
            logger.info(f"Created database: {db_name}")
            
        return True
    
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}")
        return False

def perform_restore(backup_file, db_name):
    """
    Restore PostgreSQL database from backup file
    
    Args:
        backup_file (str): Path to the backup file
        db_name (str): Name of the database to restore to
    
    Returns:
        bool: True if restore was successful, False otherwise
    """
    if not check_psql_exists():
        return False

    if not validate_backup_file(backup_file):
        return False

    if not create_database_if_missing(db_name):
        return False

    try:
        cmd = [
            'psql',
            '--dbname=postgresql://postgres:postgres@localhost:5432/' + db_name,
            '-f', backup_file
        ]
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            logger.info(f"Database {db_name} successfully restored from {backup_file}")
            return True
        else:
            logger.error(f"Restore failed: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Restore failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python db_restore.py <backup_file> <database_name>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    database_name = sys.argv[2]
    
    perform_restore(backup_file, database_name) 