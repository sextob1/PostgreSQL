# PostgreSQL Backup and Recovery Tools

A collection of Python scripts for managing PostgreSQL database backups and recovery operations.

## Scripts Overview

### 1. Logical Backup and Restore
- `db_backup.py`: Creates logical backups using pg_dump
- `db_restore.py`: Restores logical backups using psql

### 2. Physical Backup and Recovery
- `base_backup.py`: Creates physical backups with WAL archiving support
- `base_recovery.py`: Performs recovery from physical backups with point-in-time recovery support

## Prerequisites

- Python 3.6+
- PostgreSQL 12+ with client tools installed
- System user with appropriate PostgreSQL permissions
- Sufficient disk space for backups

## Installation

1. Clone the repository:
```bash
git clone <repository_url>
cd postgresql-backup-tools
```

2. Ensure scripts are executable:
```bash
chmod +x *.py
```

## Usage

### Logical Backup (db_backup.py)
Creates a SQL dump of a specific database.

```bash
python db_backup.py <database_name> <backup_directory>
```

Example:
```bash
python db_backup.py mydb /path/to/backups
```

### Logical Restore (db_restore.py)
Restores a database from a SQL dump file.

```bash
python db_restore.py <backup_file> <database_name>
```

Example:
```bash
python db_restore.py /path/to/backups/backup_20240319_123456.sql mydb
```

### Physical Base Backup (base_backup.py)
Creates a physical backup with WAL archiving support.

```bash
python base_backup.py <backup_root_dir> [options]
```

Options:
- `--wal-method=fetch|stream`: WAL handling method (default: fetch)
- `--keep-backups=N`: Number of backups to keep (default: 5)
- `--setup-archiving`: Configure WAL archiving

Example:
```bash
# Setup WAL archiving (one-time setup)
python base_backup.py /path/to/backups --setup-archiving

# Create a base backup
python base_backup.py /path/to/backups --wal-method=stream --keep-backups=3
```

### Physical Recovery (base_recovery.py)
Performs recovery from a physical backup.

```bash
python base_recovery.py <backup_root_dir> [options]
```

Options:
- `--pgdata=PATH`: PostgreSQL data directory
- `--target-time='TIMESTAMP'`: Recover to specific point in time
- `--backup-path=PATH`: Use specific backup (default: latest)

Example:
```bash
# Basic recovery
python base_recovery.py /path/to/backups --pgdata=/var/lib/postgresql/data

# Point-in-time recovery
python base_recovery.py /path/to/backups --pgdata=/var/lib/postgresql/data --target-time='2024-03-19 14:30:00'
```

## Backup Types

### Logical Backups (db_backup.py)
- Creates SQL dump files
- Suitable for smaller databases
- Easy to inspect and modify
- Platform-independent
- Slower restoration for large databases

### Physical Backups (base_backup.py)
- Creates binary copy of database files
- Supports point-in-time recovery
- Faster backup and restore
- Requires same PostgreSQL version
- Includes WAL archiving support

## Directory Structure

```
backup_root/
├── base/
│   └── YYYYMMDD_HHMMSS/  # Base backup directories
│       ├── base.tar.gz    # Base backup
│       └── pg_wal.tar.gz  # WAL files
└── wal_archive/          # WAL archive files
```

## Best Practices

1. Regular Testing
   - Regularly test backup and recovery procedures
   - Verify backup integrity
   - Practice recovery procedures

2. Retention Management
   - Configure appropriate backup retention
   - Monitor backup disk space
   - Archive old backups if needed

3. Security
   - Secure backup files with appropriate permissions
   - Use encrypted connections when backing up remote databases
   - Regularly rotate PostgreSQL credentials

4. Monitoring
   - Check backup logs regularly
   - Monitor WAL archiving process
   - Verify backup completion status

## Troubleshooting

### Common Issues

1. Permission Errors
   - Ensure PostgreSQL user has required permissions
   - Check file system permissions

2. Space Issues
   - Monitor available disk space
   - Configure appropriate backup retention
   - Clean up old backups

3. WAL Archiving Issues
   - Verify archive_command configuration
   - Check WAL archive directory permissions
   - Monitor archive_status directory

### Logging

All scripts use Python's logging module with INFO level by default. Logs include:
- Operation timestamps
- Success/failure status
- Error messages and stack traces
- Progress information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Specify your license here] 