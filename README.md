# Secure Email API

A production-ready FastAPI email service with enterprise-grade security, authentication, and comprehensive monitoring features.

## 🚀 Quick Start

Get started in minutes:

```bash
# Clone and install
git clone <repository-url>
cd email-api
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your email credentials

# Generate security keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run the application
python main_secure.py
```

**📖 Full Documentation:**
- [Quick Start Guide](QUICK_START.md) - 5-minute setup
- [Security API Documentation](SECURITY_API_DOCUMENTATION.md) - Complete reference
- [API Usage Examples](API_USAGE_EXAMPLES.md) - Code examples
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment

## ✨ Key Features

### 🔐 Security & Authentication
- **API Key Authentication**: Secure authentication with role-based access control
- **Rate Limiting**: Configurable per-API key limits to prevent abuse
- **Input Validation**: Comprehensive sanitization and validation
- **Security Headers**: CSP, XSS protection, HTTPS enforcement
- **Audit Logging**: Complete request/response tracking

### 📧 Email Operations
- **Dynamic Email Support**: Multiple email accounts per API key
- **Encrypted Credentials**: Secure storage of email credentials
- **Batch Operations**: Efficient bulk email management
- **Advanced Filtering**: Date ranges, categories, and custom filters
- **Read Status Management**: Mark emails as read/unread

### 🛠️ Enterprise Features
- **Database Support**: PostgreSQL (production) and SQLite (development)
- **Monitoring**: Health checks, metrics, and structured logging
- **Scalability**: Docker support and cloud deployment ready
- **High Availability**: Load balancing and failover support

## 📊 API Overview

### Authentication
```bash
# Create API key
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My API Key",
    "scopes": ["read", "write"],
    "rate_limit_per_minute": 60
  }'
```

### Email Operations
```bash
# Send email
curl -X POST "http://localhost:8000/api/v1/emails" \
  -H "Authorization: Bearer your_key:your_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_email": "user@example.com",
    "subject": "Hello",
    "body": "Test message"
  }'

# Get emails
curl -X GET "http://localhost:8000/api/v1/emails?filter_by=today" \
  -H "Authorization: Bearer your_key:your_secret"
```

## 🔧 Configuration

### Environment Variables
```env
# Security
SECRET_KEY=your-super-secret-key
ENCRYPTION_KEY=your-encryption-key

# Email
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Database
DATABASE_URL=postgresql://user:pass@localhost/email_api

# Environment
ENVIRONMENT=production
```

### Email Provider Setup

#### Gmail
1. Enable 2FA on your Google account
2. Generate App Password: Google Account → Security → 2-Step Verification → App Passwords
3. Use the app password in your `.env` file

#### Outlook
1. Go to Account settings → Security → App passwords
2. Generate new password for your app
3. Use in `.env` file

## 🚀 Deployment Options

### Production Deployment
```bash
# Environment setup
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@localhost/email_api

# Run with Gunicorn
gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  email-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/email_api
      - SECRET_KEY=your-secret-key
      - ENVIRONMENT=production
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=email_api
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
```

### Cloud Deployment
- **Render**: Use `render.yaml` for one-click deployment
- **AWS ECS**: Container orchestration with auto-scaling
- **Google Cloud Run**: Serverless deployment
- **Azure Container Instances**: Cloud-based containers

## 🔍 Security Features

### Authentication & Authorization
- API key-based authentication with proper validation
- Role-based access control (read, write, admin scopes)
- Secure credential hashing and validation
- JWT support for future extensibility

### Input Validation & Sanitization
- Pydantic schemas for all request/response models
- Email format validation and sanitization
- Subject and body content filtering
- Protection against header injection attacks

### Rate Limiting & Monitoring
- Per-API key rate limiting (configurable limits)
- IP-based fallback rate limiting
- Real-time rate limit headers in responses
- Comprehensive audit logging and metrics

### Secure Configuration
- Encrypted storage of email credentials
- Environment-based configuration management
- HTTPS enforcement for production
- Comprehensive security headers

## 📈 Monitoring & Observability

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Application metrics
curl -X GET "http://localhost:8000/api/v1/metrics" \
  -H "Authorization: Bearer your_key:your_secret"
```

### Logging
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Request Tracking**: Complete request/response audit trails
- **Security Events**: Authentication failures and rate limit hits
- **Performance Metrics**: Response time and throughput tracking

### Integration Support
- **Prometheus**: Metrics collection and alerting
- **ELK Stack**: Log aggregation and analysis
- **Datadog**: Cloud monitoring and APM
- **Grafana**: Visualization and dashboards

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Local Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with auto-reload
uvicorn main_secure:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICK_START.md](QUICK_START.md) | 5-minute setup guide | Everyone |
| [SECURITY_API_DOCUMENTATION.md](SECURITY_API_DOCUMENTATION.md) | Complete API reference | Developers |
| [API_USAGE_EXAMPLES.md](API_USAGE_EXAMPLES.md) | Code examples | Developers |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment | DevOps |

## 🔧 Troubleshooting

### Common Issues

#### Authentication Errors
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

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development

# Run with debug
python main_secure.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints for all new code
- Include comprehensive tests
- Update documentation for new features
- Ensure security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check the comprehensive docs in this repository
- **Issues**: Report bugs on [GitHub Issues](https://github.com/your-repo/issues)
- **Security**: Contact support for security concerns
- **Features**: Request new features via GitHub issues

### Community
- **Discussions**: GitHub Discussions for general questions
- **Stack Overflow**: Tag your questions with `secure-email-api`
- **Discord**: Join our community server (link in README)

---

## 🎯 Roadmap

### Version 2.1 (Planned)
- [ ] OAuth2 support for email providers
- [ ] Advanced email filtering and search
- [ ] Webhook support for email events
- [ ] Multi-factor authentication for API keys

### Version 2.2 (Planned)
- [ ] Email templates and campaigns
- [ ] Attachment support
- [ ] Advanced analytics and reporting
- [ ] Rate limit analytics dashboard

### Version 3.0 (Future)
- [ ] Microservices architecture
- [ ] GraphQL API
- [ ] Real-time email synchronization
- [ ] Advanced security features (IP whitelisting, etc.)

---

**Built with ❤️ for secure, reliable email operations. 📧✨**

---

## Deploy FastAPI on Render

Use this repo as a template to deploy a Python [FastAPI](https://fastapi.tiangolo.com) service on Render.

See https://render.com/docs/deploy-fastapi or follow the steps below:

### Manual Steps

1. You may use this repository directly or [create your own repository from this template](https://github.com/render-examples/fastapi/generate) if you'd like to customize the code.
2. Create a new Web Service on Render.
3. Specify the URL to your new repository or this repository.
4. Render will automatically detect that you are deploying a Python service and use `pip` to download the dependencies.
5. Specify the following as the Start Command.

    ```shell
    uvicorn main_secure:app --host 0.0.0.0 --port $PORT
    ```

6. Click Create Web Service.

Or simply click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

## Thanks

Thanks to [Harish](https://harishgarg.com) for the [inspiration to create a FastAPI quickstart for Render](https://twitter.com/harishkgarg/status/1435084018677010434) and for some sample code!
