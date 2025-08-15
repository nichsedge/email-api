# Quick Start Guide

Get the Secure Email API running in minutes with this comprehensive quick start guide.

## 🚀 Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
# Clone the repository
git clone <repository-url>
cd email-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

Set your environment variables:
```env
# Security (generate these!)
SECRET_KEY=your-super-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Email Configuration
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Database
DATABASE_URL=sqlite:///./email_api.db

# Environment
ENVIRONMENT=development
```

### 3. Generate Security Keys
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Run the Application
```bash
# Create database tables
python -c "from models.database import create_tables; create_tables()"

# Start the server
python main_secure.py
```

### 5. Test the API
```bash
# Check health
curl http://localhost:8000/health

# Create your first API key
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key",
    "description": "For testing",
    "scopes": ["read", "write"],
    "rate_limit_per_minute": 60,
    "rate_limit_per_hour": 1000
  }'
```

## 📧 Send Your First Email

### 1. Get Your API Key
From the previous response, copy your `key_id` and `secret_key`.

### 2. Send Email
```bash
curl -X POST "http://localhost:8000/api/v1/emails" \
  -H "Authorization: Bearer your_key_id:your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_email": "recipient@example.com",
    "subject": "Hello from Secure Email API",
    "body": "This is my first email through the secure API!"
  }'
```

### 3. Check Emails
```bash
curl -X GET "http://localhost:8000/api/v1/emails?filter_by=today" \
  -H "Authorization: Bearer your_key_id:your_secret_key"
```

## 🔐 Security Features

### Authentication
- **API Key Required**: All endpoints need authentication
- **Format**: `Authorization: Bearer key_id:secret_key`
- **Scopes**: Control access with read/write/admin permissions

### Rate Limiting
- **Per API Key**: Configurable limits (default: 60/min, 1000/hour)
- **Headers**: See remaining requests in response headers
- **Protection**: Prevents abuse and DoS attacks

### Input Validation
- **Email Format**: RFC-compliant email validation
- **Content Filtering**: Protection against injection attacks
- **Size Limits**: Prevents oversized requests

### Security Headers
- **HTTPS**: Automatic redirect in production
- **CSP**: Content Security Policy enabled
- **XSS Protection**: Built-in XSS filtering

## 📊 API Endpoints

### Authentication
- `POST /api/v1/api-keys` - Create API key
- `GET /api/v1/api-keys/me` - Get current API key info
- `PUT /api/v1/api-keys/{key_id}` - Update API key
- `DELETE /api/v1/api-keys/{key_id}` - Delete API key

### Email Operations
- `POST /api/v1/emails` - Send email
- `GET /api/v1/emails` - Get emails (with filtering)
- `POST /api/v1/emails/{id}/mark-read` - Mark email as read
- `POST /api/v1/emails/mark-read-batch` - Batch mark as read
- `POST /api/v1/emails/mark-unread-batch` - Batch mark as unread

### System
- `GET /health` - Health check
- `GET /api/v1/metrics` - Application metrics

## 🔧 Configuration Options

### Environment Variables
```env
# Database
DATABASE_URL=sqlite:///./email_api.db

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Email
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Rate Limiting
DEFAULT_RATE_LIMIT_PER_MINUTE=60
DEFAULT_RATE_LIMIT_PER_HOUR=1000

# CORS
CORS_ORIGINS=["*"]

# Logging
LOG_LEVEL=INFO
```

### Email Provider Setup

#### Gmail
1. Enable 2FA on your Google account
2. Generate App Password:
   - Go to Google Account → Security
   - Enable 2-Step Verification
   - Generate App Password
   - Select "Mail" and "Other (Custom name)"
3. Use the app password in your `.env` file

#### Outlook
1. Go to Account settings
2. Enable App passwords
3. Generate new password for your app
4. Use in `.env` file

## 🚀 Production Deployment

### 1. Set Production Environment
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@localhost/email_api
```

### 2. Install Gunicorn
```bash
pip install gunicorn
```

### 3. Run with Gunicorn
```bash
gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Set Up Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Enable HTTPS
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## 📱 Client Examples

### Python
```python
import requests

API_KEY = "your_key_id:your_secret_key"
BASE_URL = "http://localhost:8000/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Send email
response = requests.post(
    f"{BASE_URL}/emails",
    headers=headers,
    json={
        "receiver_email": "user@example.com",
        "subject": "Hello",
        "body": "Test message"
    }
)

print(response.json())
```

### JavaScript
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Authorization': 'Bearer your_key_id:your_secret_key',
    'Content-Type': 'application/json'
  }
});

// Send email
api.post('/emails', {
  receiver_email: 'user@example.com',
  subject: 'Hello',
  body: 'Test message'
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

### cURL
```bash
# Send email
curl -X POST "http://localhost:8000/api/v1/emails" \
  -H "Authorization: Bearer your_key_id:your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_email": "user@example.com",
    "subject": "Hello",
    "body": "Test message"
  }'

# Get emails
curl -X GET "http://localhost:8000/api/v1/emails" \
  -H "Authorization: Bearer your_key_id:your_secret_key"
```

## 🔍 Troubleshooting

### Common Issues

#### API Key Authentication
```
Error: Invalid or inactive API key
```
**Solution**: Check API key format and ensure it's active

#### Rate Limiting
```
Error: Rate limit exceeded
```
**Solution**: Wait or increase rate limits in API key settings

#### Email Sending
```
Error: Failed to send email
```
**Solution**: Verify email credentials and app password

#### Database Connection
```
Error: Could not connect to database
```
**Solution**: Check DATABASE_URL and database service

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development

# Run with debug
python main_secure.py
```

### Health Check
```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
python -c "from models.database import get_db; db = next(get_db()); print('Database OK')"
```

## 📚 Next Steps

1. **Read the full documentation**:
   - [Security API Documentation](SECURITY_API_DOCUMENTATION.md)
   - [API Usage Examples](API_USAGE_EXAMPLES.md)
   - [Deployment Guide](DEPLOYMENT_GUIDE.md)

2. **Configure production settings**:
   - Set up PostgreSQL database
   - Configure SSL/TLS certificates
   - Set up monitoring and logging

3. **Explore advanced features**:
   - Dynamic email account management
   - Custom rate limiting
   - Advanced filtering and search

4. **Deploy to cloud**:
   - Docker containers
   - Cloud platforms (AWS, GCP, Azure)
   - Serverless deployment

## 🆘 Need Help?

- **Documentation**: Check the comprehensive docs in this repository
- **Issues**: Report bugs on GitHub
- **Security**: Contact support for security concerns
- **Features**: Request new features via GitHub issues

---

**Happy emailing! 📧✨**