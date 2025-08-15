# API Usage Examples

This document provides practical examples for using the Secure Email API.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [API Key Management](#api-key-management)
3. [Email Operations](#email-operations)
4. [Error Handling](#error-handling)
5. [Advanced Features](#advanced-features)
6. [Client Implementations](#client-implementations)

## Basic Setup

### Using curl

```bash
# Set your API key
API_KEY="your_key_id:your_secret_key"

# Base URL
BASE_URL="http://localhost:8000/api/v1"
```

### Using Python

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_key_id:your_secret_key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
```

### Using JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'your_key_id:your_secret_key';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  }
});
```

## API Key Management

### Create API Key

```bash
curl -X POST "${BASE_URL}/api-keys" \
  -H "${HEADERS}" \
  -d '{
    "name": "Production Key",
    "description": "For production environment",
    "scopes": ["read", "write"],
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 2000
  }'
```

**Python Example:**
```python
def create_api_key():
    data = {
        "name": "Production Key",
        "description": "For production environment",
        "scopes": ["read", "write"],
        "rate_limit_per_minute": 100,
        "rate_limit_per_hour": 2000
    }
    
    response = requests.post(
        f"{BASE_URL}/api-keys",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code == 201:
        result = response.json()
        api_key = f"{result['data']['key_id']}:{result['data']['secret_key']}"
        print(f"Created API Key: {api_key}")
        return api_key
    else:
        print(f"Error: {response.text}")
        return None
```

**JavaScript Example:**
```javascript
async function createApiKey() {
  const data = {
    name: "Production Key",
    description: "For production environment",
    scopes: ["read", "write"],
    rate_limit_per_minute: 100,
    rate_limit_per_hour: 2000
  };

  try {
    const response = await api.post('/api-keys', data);
    const { key_id, secret_key } = response.data.data;
    const apiKey = `${key_id}:${secret_key}`;
    console.log(`Created API Key: ${apiKey}`);
    return apiKey;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    return null;
  }
}
```

### List API Keys

```bash
curl -X GET "${BASE_URL}/api-keys" \
  -H "${HEADERS}"
```

### Get Current API Key Info

```bash
curl -X GET "${BASE_URL}/api-keys/me" \
  -H "${HEADERS}"
```

### Update API Key

```bash
curl -X PUT "${BASE_URL}/api-keys/your_key_id" \
  -H "${HEADERS}" \
  -d '{
    "rate_limit_per_minute": 150,
    "description": "Updated description"
  }'
```

### Delete API Key

```bash
curl -X DELETE "${BASE_URL}/api-keys/your_key_id" \
  -H "${HEADERS}"
```

## Email Operations

### Send Email

```bash
curl -X POST "${BASE_URL}/emails" \
  -H "${HEADERS}" \
  -d '{
    "receiver_email": "recipient@example.com",
    "subject": "Hello from Secure Email API",
    "body": "This is a test email sent through the secure API."
  }'
```

**Python Example:**
```python
def send_email(recipient, subject, body):
    data = {
        "receiver_email": recipient,
        "subject": subject,
        "body": body
    }
    
    response = requests.post(
        f"{BASE_URL}/emails",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Email sent: {result['message']}")
        return True
    else:
        print(f"Error sending email: {response.text}")
        return False

# Usage
send_email(
    recipient="user@example.com",
    subject="Test Email",
    body="This is a test email from the Secure Email API."
)
```

**JavaScript Example:**
```javascript
async function sendEmail(recipient, subject, body) {
  const data = { recipient, subject, body };

  try {
    const response = await api.post('/emails', data);
    console.log('Email sent:', response.data.message);
    return true;
  } catch (error) {
    console.error('Error sending email:', error.response?.data || error.message);
    return false;
  }
}

// Usage
await sendEmail(
  'user@example.com',
  'Test Email',
  'This is a test email from the Secure Email API.'
);
```

### Read Emails

```bash
# Get today's emails
curl -X GET "${BASE_URL}/emails?filter_by=today" \
  -H "${HEADERS}"

# Get all emails
curl -X GET "${BASE_URL}/emails?filter_by=all" \
  -H "${HEADERS}"

# Get emails from date range
curl -X GET "${BASE_URL}/emails?filter_by=date_range&start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z" \
  -H "${HEADERS}"

# Mark emails as read after retrieval
curl -X GET "${BASE_URL}/emails?filter_by=today&mark_as_read=true" \
  -H "${HEADERS}"
```

**Python Example:**
```python
def get_emails(filter_by="today", mark_as_read=False):
    params = {
        "filter_by": filter_by,
        "mark_as_read": mark_as_read
    }
    
    response = requests.get(
        f"{BASE_URL}/emails",
        headers=HEADERS,
        params=params
    )
    
    if response.status_code == 200:
        result = response.json()
        emails = result['emails']
        print(f"Found {len(emails)} emails")
        
        for email in emails:
            print(f"From: {email['from']}")
            print(f"Subject: {email['subject']}")
            print(f"Body: {email['body'][:100]}...")
            print("-" * 50)
        
        return emails
    else:
        print(f"Error getting emails: {response.text}")
        return None

# Usage
emails = get_emails(filter_by="today")
```

### Mark Email as Read

```bash
curl -X POST "${BASE_URL}/emails/email_id/mark-read" \
  -H "${HEADERS}"
```

### Batch Mark as Read

```bash
curl -X POST "${BASE_URL}/emails/mark-read-batch" \
  -H "${HEADERS}" \
  -d '{
    "email_ids": ["email_id_1", "email_id_2", "email_id_3"]
  }'
```

**Python Example:**
```python
def mark_emails_as_read_batch(email_ids):
    data = {"email_ids": email_ids}
    
    response = requests.post(
        f"{BASE_URL}/emails/mark-read-batch",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Batch operation completed:")
        print(f"Total processed: {result['total_processed']}")
        print(f"Success: {result['success_count']}")
        print(f"Failed: {result['failure_count']}")
        return result
    else:
        print(f"Error in batch operation: {response.text}")
        return None

# Usage
mark_emails_as_read_batch(["email_id_1", "email_id_2", "email_id_3"])
```

### Batch Mark as Unread

```bash
curl -X POST "${BASE_URL}/emails/mark-unread-batch" \
  -H "${HEADERS}" \
  -d '{
    "email_ids": ["email_id_1", "email_id_2"]
  }'
```

## Error Handling

### Authentication Errors

```bash
# Invalid API key
curl -X GET "${BASE_URL}/emails" \
  -H "Authorization: Bearer invalid_key:invalid_secret"

# Response
{
  "error": "Authentication Required",
  "message": "Valid API key authentication is required"
}
```

**Python Error Handling:**
```python
def handle_api_request():
    try:
        response = requests.get(f"{BASE_URL}/emails", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed. Check your API key.")
        elif e.response.status_code == 429:
            print("Rate limit exceeded. Try again later.")
        else:
            print(f"HTTP Error: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None
```

### Rate Limit Errors

```bash
# When rate limited
curl -X GET "${BASE_URL}/emails" \
  -H "${HEADERS}"

# Response
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "remaining_minute": 5,
  "remaining_hour": 50
}
```

**Python Rate Limit Handling:**
```python
import time

def rate_limited_request():
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/emails", headers=HEADERS)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', retry_delay))
                print(f"Rate limited. Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 429:
                raise
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
    
    return None
```

### Validation Errors

```bash
# Invalid email format
curl -X POST "${BASE_URL}/emails" \
  -H "${HEADERS}" \
  -d '{
    "receiver_email": "invalid-email",
    "subject": "Test",
    "body": "Test body"
  }'

# Response
{
  "error": "Validation Error",
  "message": "value is not a valid email address"
}
```

## Advanced Features

### Dynamic Email Configuration

```python
def configure_dynamic_email():
    """Configure API key with custom email credentials"""
    
    # First, create API key
    key_data = {
        "name": "Custom Email Account",
        "description": "Using custom email provider",
        "scopes": ["read", "write"],
        "rate_limit_per_minute": 50,
        "rate_limit_per_hour": 500
    }
    
    response = requests.post(
        f"{BASE_URL}/api-keys",
        headers=HEADERS,  # Using admin key
        json=key_data
    )
    
    if response.status_code == 201:
        api_key_info = response.json()['data']
        
        # Configure email credentials
        email_config = {
            "email_provider": "gmail",
            "email_address": "custom@gmail.com",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "allowed_domains": ["example.com"],
            "password": "your-app-password"  # This will be encrypted
        }
        
        # Update API key with email credentials
        update_data = {"email_credentials": email_config}
        
        update_response = requests.put(
            f"{BASE_URL}/api-keys/{api_key_info['key_id']}",
            headers={"Authorization": f"Bearer {ADMIN_API_KEY}"},
            json=update_data
        )
        
        if update_response.status_code == 200:
            print("Email credentials configured successfully")
            return api_key_info['key_id']
    
    return None
```

### Monitoring and Metrics

```python
def get_api_metrics():
    """Get API usage metrics"""
    
    response = requests.get(
        f"{BASE_URL}/metrics",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        metrics = response.json()
        print("API Metrics:")
        print(f"Total Requests: {metrics['total_requests']}")
        print(f"Active Connections: {metrics['active_connections']}")
        print(f"Uptime: {metrics['uptime']:.2f} seconds")
        return metrics
    else:
        print(f"Error getting metrics: {response.text}")
        return None

def check_health():
    """Check API health"""
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        health = response.json()
        print("Health Status:")
        print(f"Status: {health['status']}")
        print(f"Database: {health['database']}")
        print(f"Uptime: {health['uptime']:.2f} seconds")
        return health['status'] == 'healthy'
    else:
        print("API is unhealthy")
        return False
```

### Batch Operations

```python
def process_email_batch():
    """Example of processing emails in batch"""
    
    # Get unread emails
    emails = get_emails(filter_by="today")
    if not emails:
        print("No emails to process")
        return
    
    email_ids = [email['id'] for email in emails]
    
    # Process emails (mark as read after processing)
    for email in emails:
        print(f"Processing email from {email['from']}")
        print(f"Subject: {email['subject']}")
        
        # Add your processing logic here
        # For example: extract data, send notifications, etc.
        
        # Mark as read
        mark_emails_as_read_batch([email['id']])
    
    print(f"Processed {len(emails)} emails")
```

## Client Implementations

### Python Client Class

```python
class SecureEmailClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_api_key(self, name, description=None, scopes=None, 
                      rate_limit_per_minute=60, rate_limit_per_hour=1000):
        """Create a new API key"""
        data = {
            "name": name,
            "description": description,
            "scopes": scopes or ["read"],
            "rate_limit_per_minute": rate_limit_per_minute,
            "rate_limit_per_hour": rate_limit_per_hour
        }
        
        response = requests.post(
            f"{self.base_url}/api-keys",
            headers=self.headers,
            json=data
        )
        
        response.raise_for_status()
        return response.json()
    
    def send_email(self, recipient, subject, body):
        """Send an email"""
        data = {
            "receiver_email": recipient,
            "subject": subject,
            "body": body
        }
        
        response = requests.post(
            f"{self.base_url}/emails",
            headers=self.headers,
            json=data
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_emails(self, filter_by="today", mark_as_read=False):
        """Get emails"""
        params = {
            "filter_by": filter_by,
            "mark_as_read": mark_as_read
        }
        
        response = requests.get(
            f"{self.base_url}/emails",
            headers=self.headers,
            params=params
        )
        
        response.raise_for_status()
        return response.json()
    
    def mark_email_as_read(self, email_id):
        """Mark email as read"""
        response = requests.post(
            f"{self.base_url}/emails/{email_id}/mark-read",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()

# Usage
client = SecureEmailClient(api_key="your_key:your_secret")
client.send_email("user@example.com", "Hello", "This is a test email")
```

### JavaScript Client Class

```javascript
class SecureEmailClient {
  constructor(baseUrl = 'http://localhost:8000/api/v1', apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.axios = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async createApiKey(name, description = null, scopes = null, 
                    rateLimitPerMinute = 60, rateLimitPerHour = 1000) {
    const data = {
      name,
      description,
      scopes: scopes || ['read'],
      rate_limit_per_minute: rateLimitPerMinute,
      rate_limit_per_hour: rateLimitPerHour
    };

    const response = await this.axios.post('/api-keys', data);
    return response.data;
  }

  async sendEmail(recipient, subject, body) {
    const data = { recipient, subject, body };
    const response = await this.axios.post('/emails', data);
    return response.data;
  }

  async getEmails(filterBy = 'today', markAsRead = false) {
    const params = { filter_by: filterBy, mark_as_read: markAsRead };
    const response = await this.axios.get('/emails', { params });
    return response.data;
  }

  async markEmailAsRead(emailId) {
    const response = await this.axios.post(`/emails/${emailId}/mark-read`);
    return response.data;
  }

  async getHealth() {
    const response = await this.axios.get('/health');
    return response.data;
  }
}

// Usage
const client = new SecureEmailClient(null, 'your_key:your_secret');
await client.sendEmail('user@example.com', 'Hello', 'This is a test email');
```

### React Hook Example

```javascript
import { useState, useEffect } from 'react';

function useSecureEmailClient(apiKey) {
  const [client, setClient] = useState(null);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (apiKey) {
      const emailClient = new SecureEmailClient(null, apiKey);
      setClient(emailClient);
    }
  }, [apiKey]);

  const fetchEmails = async (filterBy = 'today') => {
    if (!client) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await client.getEmails(filterBy);
      setEmails(response.emails);
    } catch (err) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  const sendEmail = async (recipient, subject, body) => {
    if (!client) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await client.sendEmail(recipient, subject, body);
      await fetchEmails(); // Refresh emails
    } catch (err) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    emails,
    loading,
    error,
    fetchEmails,
    sendEmail
  };
}

// Usage
function EmailComponent({ apiKey }) {
  const { emails, loading, error, fetchEmails, sendEmail } = useSecureEmailClient(apiKey);

  return (
    <div>
      <button onClick={() => fetchEmails()}>Refresh Emails</button>
      <button onClick={() => sendEmail('user@example.com', 'Test', 'Body')}>
        Send Test Email
      </button>
      
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      
      <div className="email-list">
        {emails.map(email => (
          <div key={email.id} className="email">
            <h3>{email.subject}</h3>
            <p>From: {email.from}</p>
            <p>{email.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

These examples provide a comprehensive guide to using the Secure Email API in various scenarios and programming languages.