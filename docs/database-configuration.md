# Database Configuration Guide

## Table of Contents

1. [Overview](#overview)
2. [Database Connection Strings](#database-connection-strings)
3. [PostgreSQL Setup](#postgresql-setup)
4. [Connection Pooling](#connection-pooling)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [High Availability](#high-availability)
7. [Backup & Recovery](#backup--recovery)
8. [Monitoring](#monitoring)

---

## Overview

The Toombos supports multiple database backends for production deployment. This guide focuses on PostgreSQL as the recommended production database.

### Supported Databases

- **PostgreSQL** (Recommended) - Version 12+
- **MySQL** - Version 8.0+
- **MongoDB** - Version 4.4+ (for document-based storage)

---

## Database Connection Strings

### PostgreSQL Connection String Format

```
postgresql://[user]:[password]@[host]:[port]/[database]?[parameters]
```

### Production Connection String Examples

#### Basic Connection
```bash
DATABASE_URL=postgresql://halcytone_user:SECURE_PASSWORD@db.production.com:5432/halcytone_prod
```

#### With SSL/TLS
```bash
DATABASE_URL=postgresql://halcytone_user:SECURE_PASSWORD@db.production.com:5432/halcytone_prod?sslmode=require&sslcert=/path/to/client-cert.pem&sslkey=/path/to/client-key.pem&sslrootcert=/path/to/ca-cert.pem
```

#### With Connection Pool Parameters
```bash
DATABASE_URL=postgresql://halcytone_user:SECURE_PASSWORD@db.production.com:5432/halcytone_prod?pool_size=20&max_overflow=10&pool_timeout=30&pool_recycle=3600
```

#### AWS RDS PostgreSQL
```bash
DATABASE_URL=postgresql://halcytone_admin:SECURE_PASSWORD@halcytone-prod.abc123.us-east-1.rds.amazonaws.com:5432/halcytone_prod?sslmode=require
```

#### Azure Database for PostgreSQL
```bash
DATABASE_URL=postgresql://halcytone@halcytone-prod:SECURE_PASSWORD@halcytone-prod.postgres.database.azure.com:5432/halcytone_prod?sslmode=require
```

#### Google Cloud SQL PostgreSQL
```bash
DATABASE_URL=postgresql://halcytone_user:SECURE_PASSWORD@/halcytone_prod?host=/cloudsql/project-id:region:instance-name&sslmode=require
```

### SSL Mode Options

| Mode | Description | Use Case |
|------|-------------|----------|
| `disable` | No SSL | Development only, never production |
| `allow` | Try SSL, fallback to non-SSL | Not recommended |
| `prefer` | Prefer SSL, fallback to non-SSL | Not recommended |
| `require` | **Require SSL** | **Production minimum** |
| `verify-ca` | Require SSL and verify CA | Production recommended |
| `verify-full` | Require SSL and verify hostname | Production best practice |

---

## PostgreSQL Setup

### 1. Create Production Database

```sql
-- Connect as superuser
psql -h db.production.com -U postgres

-- Create database
CREATE DATABASE halcytone_prod
  WITH
  ENCODING = 'UTF8'
  LC_COLLATE = 'en_US.UTF-8'
  LC_CTYPE = 'en_US.UTF-8'
  TEMPLATE = template0;

-- Create application user
CREATE USER halcytone_user WITH
  PASSWORD 'SECURE_PASSWORD_HERE'
  CONNECTION LIMIT 50;

-- Grant privileges
GRANT CONNECT ON DATABASE halcytone_prod TO halcytone_user;
GRANT ALL PRIVILEGES ON DATABASE halcytone_prod TO halcytone_user;

-- Connect to database
\c halcytone_prod

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO halcytone_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO halcytone_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO halcytone_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO halcytone_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON TABLES TO halcytone_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON SEQUENCES TO halcytone_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON FUNCTIONS TO halcytone_user;
```

### 2. Create Required Tables

```sql
-- Content generation audit log
CREATE TABLE content_audit (
  id SERIAL PRIMARY KEY,
  content_id VARCHAR(255) NOT NULL,
  operation VARCHAR(50) NOT NULL,
  user_id VARCHAR(255),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_content_audit_timestamp (timestamp),
  INDEX idx_content_audit_content_id (content_id)
);

-- Cache metadata
CREATE TABLE cache_metadata (
  cache_key VARCHAR(512) PRIMARY KEY,
  target VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  size_bytes INTEGER,
  hit_count INTEGER DEFAULT 0,
  last_accessed TIMESTAMP,
  INDEX idx_cache_expires (expires_at),
  INDEX idx_cache_target (target)
);

-- AB test results
CREATE TABLE ab_test_results (
  id SERIAL PRIMARY KEY,
  test_id VARCHAR(255) NOT NULL,
  variant_id VARCHAR(255) NOT NULL,
  metric_name VARCHAR(100) NOT NULL,
  metric_value DECIMAL(10, 4),
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_test_results_test_id (test_id),
  INDEX idx_test_results_timestamp (timestamp)
);

-- Content generation metrics
CREATE TABLE content_metrics (
  id SERIAL PRIMARY KEY,
  content_id VARCHAR(255) NOT NULL,
  channel VARCHAR(50) NOT NULL,
  generation_time_ms INTEGER,
  ai_tokens_used INTEGER,
  quality_score DECIMAL(3, 2),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_content_metrics_channel (channel),
  INDEX idx_content_metrics_created (created_at)
);

-- User segments
CREATE TABLE user_segments (
  segment_id VARCHAR(255) PRIMARY KEY,
  segment_name VARCHAR(255) NOT NULL,
  criteria JSONB NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Scheduled content
CREATE TABLE scheduled_content (
  id SERIAL PRIMARY KEY,
  content_id VARCHAR(255) NOT NULL UNIQUE,
  channel VARCHAR(50) NOT NULL,
  scheduled_time TIMESTAMP NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  retry_count INTEGER DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  published_at TIMESTAMP,
  error_message TEXT,
  INDEX idx_scheduled_status (status),
  INDEX idx_scheduled_time (scheduled_time)
);
```

### 3. Configure PostgreSQL for Production

```ini
# postgresql.conf optimizations

# Connection Settings
max_connections = 200
superuser_reserved_connections = 3

# Memory Settings (adjust based on server resources)
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB
work_mem = 16MB

# Write Ahead Log (WAL)
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

# Query Planner
random_page_cost = 1.1                  # For SSD storage
effective_io_concurrency = 200          # For SSD storage

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 1GB
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'                   # Log DDL only
log_min_duration_statement = 1000       # Log slow queries (>1s)

# Statistics
track_activity_query_size = 2048
track_io_timing = on
```

---

## Connection Pooling

### Application-Level Pooling (SQLAlchemy)

```python
# src/halcytone_content_generator/core/database.py
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import os

def create_db_engine():
    """Create database engine with production pooling"""
    database_url = os.getenv('DATABASE_URL')

    engine = create_engine(
        database_url,
        # Pool settings
        pool_size=20,                    # Number of persistent connections
        max_overflow=10,                 # Additional connections when needed
        pool_timeout=30,                 # Wait 30s for available connection
        pool_recycle=3600,               # Recycle connections after 1 hour
        pool_pre_ping=True,              # Verify connection before use

        # Execution settings
        echo=False,                      # Don't log SQL in production
        echo_pool=False,                 # Don't log pool events
        connect_args={
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30s query timeout
            'sslmode': 'require',
            'sslcert': os.getenv('DATABASE_SSL_CERT'),
            'sslkey': os.getenv('DATABASE_SSL_KEY'),
            'sslrootcert': os.getenv('DATABASE_SSL_CA'),
        }
    )

    return engine

# Create session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### PgBouncer Configuration (Recommended for Production)

```ini
# /etc/pgbouncer/pgbouncer.ini

[databases]
halcytone_prod = host=db.production.com port=5432 dbname=halcytone_prod

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction              # Transaction pooling (recommended)
max_client_conn = 1000               # Maximum client connections
default_pool_size = 25               # Connections per database
reserve_pool_size = 5                # Emergency reserve
reserve_pool_timeout = 3             # Seconds

# Server settings
server_reset_query = DISCARD ALL
server_check_delay = 30
server_lifetime = 3600               # Close server after 1 hour
server_idle_timeout = 600            # Close idle servers after 10 min

# Connection settings
tcp_keepalive = 1
tcp_keepidle = 60
tcp_keepintvl = 10

# Logging
admin_users = pgbouncer_admin
stats_users = pgbouncer_stats
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

#### Using PgBouncer

```bash
# Update connection string to use PgBouncer
DATABASE_URL=postgresql://halcytone_user:PASSWORD@pgbouncer.production.com:6432/halcytone_prod
```

---

## SSL/TLS Configuration

### Generate SSL Certificates

#### Option 1: Self-Signed (Development/Testing)

```bash
# Generate CA key and certificate
openssl req -new -x509 -days 3650 -nodes -out ca.crt -keyout ca.key \
  -subj "/CN=Halcytone CA"

# Generate server key and certificate signing request
openssl req -new -nodes -out server.csr -keyout server.key \
  -subj "/CN=db.production.com"

# Sign server certificate with CA
openssl x509 -req -in server.csr -days 365 -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt

# Generate client key and certificate
openssl req -new -nodes -out client.csr -keyout client.key \
  -subj "/CN=halcytone_user"

openssl x509 -req -in client.csr -days 365 -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt

# Set permissions
chmod 600 server.key client.key
chmod 644 server.crt client.crt ca.crt
```

#### Option 2: AWS RDS (Managed SSL)

```bash
# Download RDS CA certificate bundle
wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

# Use in connection string
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db?sslmode=verify-full&sslrootcert=/path/to/global-bundle.pem
```

### Configure PostgreSQL for SSL

```ini
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'
```

### Application SSL Configuration

```bash
# .env.production
DATABASE_SSL_MODE=verify-full
DATABASE_SSL_CERT=/app/certs/client.crt
DATABASE_SSL_KEY=/app/certs/client.key
DATABASE_SSL_CA=/app/certs/ca.crt
```

---

## High Availability

### Read Replicas

#### Primary-Replica Configuration

```python
# Multiple database URLs
PRIMARY_DB_URL = "postgresql://user:pass@primary-db:5432/halcytone_prod"
REPLICA_DB_URL = "postgresql://user:pass@replica-db:5432/halcytone_prod"

# Create engines
primary_engine = create_engine(PRIMARY_DB_URL, pool_size=20)
replica_engine = create_engine(REPLICA_DB_URL, pool_size=30)

# Route reads to replica
def get_db_read():
    """Use replica for read-only operations"""
    return SessionLocal(bind=replica_engine)

def get_db_write():
    """Use primary for write operations"""
    return SessionLocal(bind=primary_engine)
```

### Connection Failover

```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import Pool
import logging

logger = logging.getLogger(__name__)

@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Test connection on checkout"""
    connection_record.info['pid'] = dbapi_conn.get_backend_pid()
    logger.info(f"New connection established: PID {connection_record.info['pid']}")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Verify connection is alive on checkout"""
    pid = connection_record.info.get('pid')
    if pid is not None:
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            logger.warning(f"Stale connection detected (PID {pid}), invalidating")
            raise DisconnectionError()
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# scripts/backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
BACKUP_FILE="$BACKUP_DIR/halcytone_prod_$DATE.sql.gz"

# Create backup
pg_dump -h db.production.com \
  -U halcytone_admin \
  -d halcytone_prod \
  --format=custom \
  --compress=9 \
  --file="$BACKUP_FILE"

# Upload to S3
aws s3 cp "$BACKUP_FILE" s3://halcytone-backups/database/

# Keep only last 30 days locally
find $BACKUP_DIR -name "halcytone_prod_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

### Point-in-Time Recovery

```bash
# Enable WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'aws s3 cp %p s3://halcytone-backups/wal/%f'
```

### Restore Procedure

```bash
# Restore from backup
pg_restore -h db.production.com \
  -U postgres \
  -d halcytone_prod_restore \
  --clean \
  --if-exists \
  /backups/halcytone_prod_20250930.sql.gz

# Verify restore
psql -h db.production.com -U postgres -d halcytone_prod_restore -c "\dt"
```

---

## Monitoring

### Key Metrics to Monitor

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'halcytone_prod';

-- Connection breakdown by state
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = 'halcytone_prod'
GROUP BY state;

-- Long-running queries (>30s)
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
  AND now() - query_start > interval '30 seconds'
ORDER BY duration DESC;

-- Database size
SELECT pg_size_pretty(pg_database_size('halcytone_prod'));

-- Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Cache hit ratio (should be >99%)
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit)  as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Prometheus Exporter

```yaml
# docker-compose.yml - Add postgres_exporter
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://monitor:password@postgres:5432/halcytone_prod?sslmode=disable"
  ports:
    - "9187:9187"
```

### Alert Rules

```yaml
# prometheus/alerts/database.yml
groups:
  - name: database
    interval: 30s
    rules:
      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighConnectionCount
        expr: pg_stat_activity_count > 150
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High connection count ({{ $value }})"

      - alert: SlowQueries
        expr: pg_slow_queries > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of slow queries"
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Pool Exhausted

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached
```

**Solution**: Increase pool size or investigate connection leaks
```python
engine = create_engine(url, pool_size=30, max_overflow=20)
```

#### 2. SSL Connection Failed

```
connection requires a valid client certificate
```

**Solution**: Verify SSL certificates are properly configured
```bash
# Test SSL connection
psql "postgresql://user@host/db?sslmode=require&sslcert=client.crt&sslkey=client.key&sslrootcert=ca.crt"
```

#### 3. Too Many Connections

```
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

**Solution**: Use connection pooler (PgBouncer) or increase max_connections

---

## Production Checklist

- [ ] Database created with proper encoding (UTF-8)
- [ ] Application user created with limited privileges
- [ ] All required tables and indexes created
- [ ] SSL/TLS enabled and verified
- [ ] Connection pooling configured (application or PgBouncer)
- [ ] Backup automation configured and tested
- [ ] Monitoring and alerts configured
- [ ] Read replicas configured (if needed)
- [ ] Performance tuning applied
- [ ] Firewall rules configured (database only accessible from app servers)
- [ ] Credentials stored in secrets manager
- [ ] Connection strings tested from production environment
