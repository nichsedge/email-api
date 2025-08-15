# Secure Email API Documentation

## Overview

The Secure Email API is a production-ready FastAPI application that provides secure email operations with comprehensive authentication, authorization, and security features. It supports dynamic email account management per API key and includes enterprise-grade security measures.

## Features

- 🔐 **API Key Authentication**: Secure authentication with role-based access control
- 📧 **Dynamic Email Support**: Multiple email accounts per API key
- 🛡️ **Input Validation**: Comprehensive input sanitization and validation
- ⚡ **Rate Limiting**: Configurable rate limits per API key
- 📊 **Audit Logging**: Complete request/response tracking
- 🔒 **Security Headers**: Comprehensive protection headers
- 🔐 **Encrypted Credentials**: Secure storage of email credentials
- 📝 **Comprehensive Logging**: Structured logging for monitoring

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
4. [Security Features](#security-features)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.12+
- Email account with app password support (Gmail recommended)
- Database (SQLite for development, PostgreSQL for production)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd email-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment:
```bash
cp .env.example .env
```

4. Configure your `.env` file:
```env
# Database Configuration
DATABASE_URL=sqlite:///./email_api.db

# Security Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-here-generate-with-openssl

# Email Configuration
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Environment Configuration
ENVIRONMENT=development
```

5. Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

6. Run the application:
```bash
python main_secure.py
```

### Create Your First API Key

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First API Key",
    "description": "For my application",
    "scopes": ["read", "write"],
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000
  }'
```

Response:
```json
{
  "status": "success",
  "message": "API key created successfully",
  "data": {
    "key_id": "abc123def456...",
    "secret_key": "ghi789jkl012...",
    "name": "My First API Key",
    "description": "For my application",
    "scopes": ["read", "write"],
    "rate_limits": {
      "per_minute": 60,
      "per_hour": 1000
    }
  }
}
```

## Authentication

### API Key Format

The API uses Bearer token authentication with the format: `key_id:secret_key`

Example header:
```
Authorization: Bearer abc123def456...:ghi789jkl012...
```

### API Key Scopes

- **read**: Read emails and email metadata
- **write**: Send emails and manage email flags
- **admin**: Full access including API key management

### Creating API Keys

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin_key:admin_secret" \
  -d '{
    "name": "Production API Key",
    "description": "For production environment",
    "scopes": ["read", "write"],
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 2000
  }'
```

### Managing API Keys

```bash
# List all API keys (admin only)
curl -X GET "http://localhost:8000/api/v1/api-keys" \
  -H "Authorization: Bearer admin_key:admin_secret"

# Get current API key info
curl -X GET "http://localhost:8000/api/v1/api-keys/me" \
  -H "Authorization: Bearer your_key:your_secret"

# Update API key
curl -X PUT "http://localhost:8000/api/v1/api-keys/abc123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin_key:admin_secret" \
  -d '{
    "rate_limit_per_minute": 120,
    "is_active": true
  }'

# Delete API key (admin only)
curl -X DELETE "http://localhost:8000/api/v1/api-keys/abc123" \
  -H "Authorization: Bearer admin_key:admin_secret"
```

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### API Key Management

#### Create API Key
- **POST** `/api-keys`
- **Description**: Create a new API key
- **Authentication**: Required (admin scope for creation)
- **Request Body**:
```json
{
  "name": "string (required, max 100)",
  "description": "string (optional, max 500)",
  "scopes": ["read", "write", "admin"],
  "rate_limit_per_minute": "integer (default: 60, max: 1000)",
  "rate_limit_per_hour": "integer (default: 1000, max: 10000)"
}
```

#### List API Keys
- **GET** `/api-keys`
- **Description**: List all API keys
- **Authentication**: Required (admin scope)
- **Response**: Array of API key objects

#### Get Current API Key
- **GET** `/api-keys/me`
- **Description**: Get current API key information
- **Authentication**: Required
- **Response**: Current API key object

#### Update API Key
- **PUT** `/api-keys/{key_id}`
- **Description**: Update API key information
- **Authentication**: Required (admin or own key)
- **Request Body**: Partial API key object

#### Delete API Key
- **DELETE** `/api-keys/{key_id}`
- **Description**: Delete API key
- **Authentication**: Required (admin scope)

### Email Operations

#### Send Email
- **POST** `/emails`
- **Description**: Send an email
- **Authentication**: Required (write scope)
- **Request Body**:
```json
{
  "receiver_email": "string (valid email)",
  "subject": "string (max 200)",
  "body": "string (max 50000)"
}
```

#### Read Emails
- **GET** `/emails`
- **Description**: Retrieve unread emails
- **Authentication**: Required (read scope)
- **Query Parameters**:
  - `filter_by`: "today", "all", "date_range" (default: "today")
  - `start_date`: ISO datetime (required for date_range)
  - `end_date`: ISO datetime (required for date_range)
  - `mark_as_read`: boolean (default: false)

#### Mark Email as Read
- **POST** `/emails/{id}/mark-read`
- **Description**: Mark a specific email as read
- **Authentication**: Required (write scope)
- **Path Parameters**:
  - `id`: Email ID

#### Batch Mark as Read
- **POST** `/emails/mark-read-batch`
- **Description**: Mark multiple emails as read
- **Authentication**: Required (write scope)
- **Request Body**:
```json
{
  "email_ids": ["string", "string", ...]
}
```

#### Batch Mark as Unread
- **POST** `/emails/mark-unread-batch`
- **Description**: Mark multiple emails as unread
- **Authentication**: Required (write scope)
- **Request Body**:
```json
{
  "email_ids": ["string", "string", ...]
}
```

### System Endpoints

#### Health Check
- **GET** `/health`
- **Description**: System health status
- **Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "database": "connected",
  "uptime": 1234.56
}
```

#### Metrics
- **GET** `/api/v1/metrics`
- **Description**: Application metrics
- **Authentication**: Required (admin scope)
- **Response**:
```json
{
  "total_requests": 1000,
  "active_connections": 5,
  "uptime": 1234.56,
  "version": "2.0.0"
}
```

## Security Features

### Authentication & Authorization

- **API Key Authentication**: Secure authentication using hashed API keys
- **Role-Based Access Control**: Granular permissions (read, write, admin)
- **JWT Support**: Extensible token-based authentication
- **Secure Credential Storage**: Encrypted storage of sensitive data

### Input Validation & Sanitization

- **Pydantic Schemas**: Type-safe request/response validation
- **Email Validation**: RFC-compliant email format validation
- **Content Filtering**: Protection against header injection
- **Input Sanitization**: Removal of potentially dangerous characters

### Rate Limiting

- **Per-API Key Limits**: Configurable rate limits per API key
- **IP-Based Fallback**: Additional protection for unauthenticated requests
- **Real-time Headers**: Rate limit information in response headers
- **Configurable Windows**: Minute and hourly rate limiting

### Security Headers

- **Content Security Policy**: Protection against XSS attacks
- **X-Frame-Options**: Clickjacking protection
- **X-Content-Type-Options**: MIME type sniffing protection
- **X-XSS-Protection**: Built-in XSS protection
- **Strict Transport Security**: HTTPS enforcement

### Audit Logging

- **Request Logging**: Complete request/response tracking
- **Security Events**: Authentication failures and rate limit hits
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Performance Metrics**: Response time and throughput tracking

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///./email_api.db` | Yes |
| `SECRET_KEY` | JWT secret key | Auto-generated | Yes |
| `ENCRYPTION_KEY` | Data encryption key | Auto-generated | Yes |
| `GMAIL_EMAIL` | Default email address | - | Yes |
| `GMAIL_APP_PASSWORD` | Default email app password | - | Yes |
| `ENVIRONMENT` | Environment (development/production) | `development` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | No |
| `DEFAULT_RATE_LIMIT_PER_MINUTE` | Default rate limit per minute | `60` | No |
| `DEFAULT_RATE_LIMIT_PER_HOUR` | Default rate limit per hour | `1000` | No |

### Database Configuration

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///./email_api.db
```

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql://user:password@localhost/email_api
```

### Security Configuration

#### Generate Encryption Key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### Set Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment

### Production Deployment

1. **Environment Setup**:
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:password@localhost/email_api
export SECRET_KEY=your-production-secret-key
export ENCRYPTION_KEY=your-production-encryption-key
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Database Migration**:
```bash
python -c "from models.database import create_tables; create_tables()"
```

4. **Run with Gunicorn**:
```bash
gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main_secure:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  email-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/email_api
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
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cloud Deployment

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
```

## Monitoring

### Logging

The application uses structured logging with JSON format. Logs include:

- Request/response information
- Authentication events
- Security incidents
- Performance metrics
- Error details

### Health Checks

- **Endpoint**: `/health`
- **Metrics**: Database connectivity, uptime, version
- **Status Codes**: 200 (healthy), 500 (unhealthy)

### Metrics Collection

- **Total Requests**: Request count
- **Response Times**: Average processing time
- **Rate Limit Hits**: Abuse detection
- **Active Connections**: Current connections
- **Error Rates**: Failure tracking

### Monitoring Integration

#### Prometheus
```python
# Add to main_secure.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
```

#### Alerting Rules
```yaml
# Example Prometheus alerting rules
groups:
- name: email-api
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on Email API"
      description: "Error rate is {{ $value }} for 5 minutes"
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Invalid or inactive API key
```
**Solution**: 
1. Verify API key format: `key_id:secret_key`
2. Check API key status in database
3. Ensure proper scopes for requested operation

#### Rate Limit Errors
```
Error: Rate limit exceeded
```
**Solution**:
1. Check rate limit headers in response
2. Monitor usage patterns
3. Adjust rate limits if needed

#### Database Connection Issues
```
Error: Could not connect to database
```
**Solution**:
1. Verify database URL configuration
2. Check database service status
3. Ensure proper database permissions

#### Email Sending Failures
```
Error: Failed to send email
```
**Solution**:
1. Verify email credentials
2. Check email provider settings
3. Ensure app password is used (not regular password)

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

### Performance Issues

1. **Database Optimization**:
   - Add proper indexes
   - Use connection pooling
   - Optimize queries

2. **Rate Limiting**:
   - Adjust limits based on usage
   - Monitor for abuse patterns
   - Implement caching where appropriate

3. **Memory Usage**:
   - Monitor memory consumption
   - Implement proper cleanup
   - Use efficient data structures

### Security Incidents

#### Suspicious Activity Detection
Monitor for:
- Multiple failed authentication attempts
- Unusual request patterns
- Rate limit threshold breaches
- Access from unusual IP addresses

#### Incident Response
1. **Immediate Actions**:
   - Disable compromised API keys
   - Review audit logs
   - Check for data breaches

2. **Investigation**:
   - Analyze request patterns
   - Check for unauthorized access
   - Review system logs

3. **Recovery**:
   - Rotate credentials
   - Update security configurations
   - Implement additional monitoring

### Backup and Recovery

#### Database Backups
```bash
# PostgreSQL backup
pg_dump email_api > backup.sql

# SQLite backup
cp email_api.db backup_email_api.db
```

#### Configuration Backup
```bash
# Backup environment configuration
cp .env backup_env.conf
```

#### Recovery Procedure
1. Restore database from backup
2. Restore configuration files
3. Restart application services
4. Verify functionality

## Best Practices

### Security
- Use strong, unique API keys
- Implement proper secret management
- Regularly rotate credentials
- Monitor for suspicious activity
- Keep dependencies updated

### Performance
- Use appropriate rate limits
- Implement caching strategies
- Monitor resource usage
- Optimize database queries
- Use connection pooling

### Monitoring
- Set up comprehensive logging
- Implement health checks
- Monitor key metrics
- Set up alerting
- Regular security audits

### Maintenance
- Regular security updates
- Database maintenance
- Performance optimization
- Documentation updates
- Backup verification

## Support

For support and questions:
- Review this documentation
- Check troubleshooting section
- Review audit logs for errors
- Monitor system metrics
- Contact development team

---

*This documentation covers the Secure Email API version 2.0.0. For the latest updates, please refer to the repository documentation.*