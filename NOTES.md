# Project Management Notes

## Core Principles
- Maintain alignment with DESIGN.md
- Prefer coded solutions over new libraries
- Avoid sprawl (DB, File, General)
- Keep changes minimal and focused
- Externalize embedded code (HTML, JavaScript)
- Preserve foundational/API code
- Monitor file sizes for modularization
- Maintain detailed documentation

## Function Registry

### Database Backup Functions
- `perform_backup(db_name, output_dir)`: Creates a PostgreSQL database backup
- `create_backup_filename()`: Generates timestamped backup filename
- `check_pg_dump_exists()`: Validates pg_dump is available
- `validate_backup_dir(dir_path)`: Ensures backup directory exists/is writable

### Database Restore Functions
- `perform_restore(backup_file, db_name)`: Restores PostgreSQL database from backup
- `check_psql_exists()`: Validates psql is available
- `validate_backup_file(file_path)`: Ensures backup file exists and is readable
- `create_database_if_missing(db_name)`: Creates database if it doesn't exist

### Base Backup Functions
- `perform_base_backup(backup_dir, wal_method='fetch')`: Creates PostgreSQL base backup
- `setup_wal_archiving(archive_dir)`: Configures WAL archiving
- `check_pg_basebackup_exists()`: Validates pg_basebackup availability
- `validate_postgres_connection()`: Checks PostgreSQL connection and permissions
- `configure_recovery_conf(backup_dir)`: Creates recovery configuration
- `cleanup_old_backups(backup_dir, keep_count)`: Manages backup retention

### Base Recovery Functions
- `perform_recovery(backup_path, target_time=None)`: Restores PostgreSQL from base backup
- `find_latest_backup()`: Finds most recent base backup
- `validate_backup(backup_path)`: Ensures backup is valid and complete
- `restore_base_backup(backup_path)`: Restores the base backup files
- `configure_recovery(target_time)`: Sets up recovery.conf for point-in-time recovery
- `apply_wal_archives()`: Applies WAL archives during recovery

## State Management
Current Task: Base Recovery Implementation
- Using pg_basebackup restoration process
- Implementing point-in-time recovery
- Handling WAL archive application
- Managing recovery configuration

## Change History
[Significant changes will be logged here] 