# Deployment Guide

This guide covers deploying the Secure Email API in various environments with proper security configurations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Deployment Options](#deployment-options)
6. [Production Hardening](#production-hardening)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.12 or higher
- **Memory**: Minimum 512MB RAM (1GB recommended)
- **Storage**: Minimum 1GB free space
- **Network**: Internet access for email services

### Required Tools

- **Python Package Manager**: pip
- **Database Server**: PostgreSQL 13+ (recommended) or SQLite (development)
- **Web Server**: Gunicorn or Uvicorn
- **Reverse Proxy**: Nginx or Apache (production)
- **Process Manager**: systemd or supervisor

### Email Provider Requirements

- **Gmail**: App password enabled (2FA required)
- **Outlook**: App password or OAuth2
- **Other SMTP/IMAP**: Server access with authentication

## Environment Setup

### Development Environment

```bash
# Clone repository
git clone <repository-url>
cd email-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit environment file
nano .env
```

### Production Environment

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash emailapi
sudo su - emailapi

# Clone repository
git clone <repository-url>
cd email-api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

## Database Configuration

### SQLite (Development Only)

```env
DATABASE_URL=sqlite:///./email_api.db
```

### PostgreSQL (Production)

#### Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb

# macOS
brew install postgresql
brew services start postgresql
```

#### Create Database and User
```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE email_api;
CREATE USER email_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE email_api TO email_user;
\q
```

#### Configure PostgreSQL
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf

# Set these parameters:
listen_addresses = 'localhost'
max_connections = 200
shared_buffers = 128MB
effective_cache_size = 4GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Edit pg_hba.conf
sudo nano /etc/postgresql/13/main/pg_hba.conf

# Add line:
host    email_api        email_user        127.0.0.1/32            md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Set Database URL
```env
DATABASE_URL=postgresql://email_user:secure_password@localhost/email_api
```

### Database Migration

```bash
# Create tables
python -c "from models.database import create_tables; create_tables()"

# For production with Alembic (if available)
alembic upgrade head
```

## Security Configuration

### Generate Secure Keys

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Environment Configuration

```env
# Security Configuration
SECRET_KEY=your-generated-secret-key
ENCRYPTION_KEY=your-generated-encryption-key

# Email Configuration
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Environment
ENVIRONMENT=production

# CORS Configuration
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Rate Limiting
DEFAULT_RATE_LIMIT_PER_MINUTE=60
DEFAULT_RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### SSL/TLS Configuration

#### Generate Self-Signed Certificate (Development)
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/email-api.key \
  -out /etc/ssl/certs/email-api.crt
```

#### Let's Encrypt Certificate (Production)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Deployment Options

### 1. Direct Deployment with Gunicorn

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/email-api.service
```

```ini
[Unit]
Description=Secure Email API
After=network.target

[Service]
Type=exec
User=emailapi
Group=emailapi
WorkingDirectory=/home/emailapi/email-api
Environment=PATH=/home/emailapi/email-api/venv/bin
ExecStart=/home/emailapi/email-api/venv/bin/gunicorn \
  --workers 4 \
  --bind unix:/run/email-api.sock \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --graceful-timeout 30 \
  --access-logfile - \
  --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
  main_secure:app

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl start email-api
sudo systemctl enable email-api
```

### 2. Docker Deployment

#### Create Dockerfile
```dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "main_secure:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Create docker-compose.yml
```yaml
version: '3.8'

services:
  email-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://email_user:secure_password@db:5432/email_api
      - SECRET_KEY=your-secret-key
      - ENCRYPTION_KEY=your-encryption-key
      - ENVIRONMENT=production
      - GMAIL_EMAIL=your-email@gmail.com
      - GMAIL_APP_PASSWORD=your-app-password
      - CORS_ORIGINS=["https://yourdomain.com"]
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=email_api
      - POSTGRES_USER=email_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U email_user -d email_api"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - email-api
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Create nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream email_api {
        server email-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/ssl/certs/email-api.crt;
        ssl_certificate_key /etc/ssl/private/email-api.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 1d;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;

        # Proxy to API
        location / {
            proxy_pass http://email_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            proxy_pass http://email_api/health;
            access_log off;
        }
    }
}
```

### 3. Cloud Deployment

#### Render Deployment
```yaml
# render.yaml
services:
  - type: web
    name: email-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
    envVars:
      - key: DATABASE_URL
        value: your-database-url
      - key: SECRET_KEY
        value: your-secret-key
      - key: ENCRYPTION_KEY
        value: your-encryption-key
      - key: ENVIRONMENT
        value: production
      - key: GMAIL_EMAIL
        value: your-email@gmail.com
      - key: GMAIL_APP_PASSWORD
        value: your-app-password
      - key: CORS_ORIGINS
        value: '["https://yourdomain.com"]'
    healthCheck:
      path: /health
      interval: 30s
      timeout: 5s
      unhealthyThreshold: 2
      healthyThreshold: 2
    instanceCount: 2
    instanceSize: "medium"
    disk:
      name: email-api-storage
      sizeGB: 10
```

#### AWS ECS Deployment
```json
{
  "family": "email-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "email-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/email-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint/email_api"
        },
        {
          "name": "SECRET_KEY",
          "value": "your-secret-key"
        },
        {
          "name": "ENCRYPTION_KEY",
          "value": "your-encryption-key"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/email-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Production Hardening

### File Permissions
```bash
# Set proper permissions
sudo chown -R emailapi:emailapi /home/emailapi/email-api
sudo chmod 750 /home/emailapi/email-api
sudo chmod 600 /home/emailapi/email-api/.env

# Set umask
echo "umask 077" >> /home/emailapi/.bashrc
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### System Security
```bash
# Fail2Ban for SSH
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit jail.local
sudo nano /etc/fail2ban/jail.local

# Add SSH protection
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h

# Restart fail2ban
sudo systemctl restart fail2ban
```

### Application Security
```bash
# Disable debug mode
export ENVIRONMENT=production

# Set secure cookies
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Configure CORS properly
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=false
```

## Monitoring and Logging

### Structured Logging
```python
# Configure logging in main_secure.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/email-api/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
```

### Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/email-api

# Add configuration
/var/log/email-api/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 emailapi emailapi
    postrotate
        systemctl reload email-api
    endscript
}
```

### Monitoring with Prometheus
```python
# Add to main_secure.py
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
ERROR_COUNT = Counter('errors_total', 'Total errors', ['error_type'])

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    if response.status_code >= 400:
        ERROR_COUNT.labels(error_type=f"{response.status_code}").inc()
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY))
```

### Health Checks
```python
# Enhanced health check
@app.get("/health")
async def health_check():
    # Check database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Check external services
    services = {
        "database": db_status,
        "email": "unknown"  # Could add email provider check
    }
    
    all_healthy = all(status == "connected" for status in services.values())
    
    return HealthCheckResponse(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=time.time(),
        version="2.0.0",
        database=db_status,
        uptime=time.time() - start_time,
        services=services
    )
```

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="email_api"
DB_USER="email_user"
DB_HOST="localhost"

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/email_api_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/email_api_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "email_api_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/email_api_$DATE.sql.gz s3://your-backup-bucket/email_api_$DATE.sql.gz
```

### Configuration Backup
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /home/emailapi/email-api/.env \
    /etc/nginx/nginx.conf \
    /etc/systemd/system/email-api.service

# Keep only last 30 days
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

### Automated Backup
```bash
# Add to crontab
crontab -e

# Add lines:
# Daily database backup at 2 AM
0 2 * * * /home/emailapi/scripts/backup_db.sh

# Daily config backup at 3 AM
0 3 * * * /home/emailapi/scripts/backup_config.sh

# Weekly cleanup at 4 AM on Sunday
0 4 * * 0 /home/emailapi/scripts/cleanup_backups.sh
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  email-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    environment:
      - DATABASE_URL=postgresql://email_user:secure_password@db:5432/email_api
      - SECRET_KEY=your-secret-key
      - ENCRYPTION_KEY=your-encryption-key
      - ENVIRONMENT=production
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=email_api
      - POSTGRES_USER=email_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U email_user -d email_api"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - email-api
    restart: unless-stopped

volumes:
  postgres_data:
```

### Load Balancing
```nginx
# nginx.conf with load balancing
upstream email_api {
    server email-api-1:8000;
    server email-api-2:8000;
    server email-api-3:8000;
    
    # Health check
    health_check interval=30s fails=3 passes=2;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://email_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Load balancing settings
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
    }
}
```

### Database Scaling
```sql
-- Read replicas setup (PostgreSQL)
-- On primary server:
CREATE USER replica_user WITH REPLICATION PASSWORD 'replica_password';
GRANT REPLICATION ON ALL DATABASES TO replica_user;

-- On replica server:
sudo -u postgres pg_basebackup -h primary-server -U replica_user -D /var/lib/postgresql/15/main -Fp -Xs -P

# Configure recovery.conf
echo "standby_mode = 'on'
primary_conninfo = 'host=primary-server user=replica_user password=replica_password'
restore_command = 'cp /backups/%f %p'
archive_cleanup_command = 'pg_archivecleanup /var/lib/postgresql/15/main %r'
trigger_file = '/var/lib/postgresql/15/main/trigger'" > /var/lib/postgresql/15/main/recovery.conf
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service status
sudo systemctl status email-api

# Check logs
sudo journalctl -u email-api -f

# Check for syntax errors
python -m py_compile main_secure.py
```

#### Database Connection Issues
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Reset database connection pool
sudo systemctl restart postgresql
```

#### Memory Issues
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### Performance Issues
```bash
# Monitor performance
htop
iotop
nethogs

# Check database performance
EXPLAIN ANALYZE SELECT * FROM emails WHERE created_at > NOW() - INTERVAL '1 day';

# Optimize database
VACUUM ANALYZE;
REINDEX DATABASE email_api;
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development

# Run with debug
python main_secure.py
```

### Health Check Script
```bash
#!/bin/bash
# health_check.sh

API_URL="http://localhost:8000/health"
EMAIL="your-email@gmail.com"

# Check API health
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $response -eq 200 ]; then
    echo "API is healthy"
else
    echo "API is unhealthy (HTTP $response)"
    # Send alert email
    echo "API health check failed" | mail -s "API Alert" $EMAIL
    exit 1
fi
```

### Performance Monitoring
```python
# Add performance monitoring
import time
import psutil

@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    response = await call_next(request)
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    process_time = end_time - start_time
    memory_usage = end_memory - start_memory
    
    # Log performance metrics
    logger.info(
        "Performance metrics",
        endpoint=request.url.path,
        process_time=process_time,
        memory_usage=memory_usage,
        status_code=response.status_code
    )
    
    return response
```

This deployment guide provides comprehensive instructions for deploying and maintaining the Secure Email API in production environments.