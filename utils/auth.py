import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.database import get_db, APIKey, AuditLog
from cryptography.fernet import Fernet
import structlog

logger = structlog.get_logger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Generate encryption key for sensitive data
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

security = HTTPBearer()

def generate_api_key(name: str, description: str = None, scopes: List[str] = None, 
                    rate_limit_per_minute: int = 60, rate_limit_per_hour: int = 1000) -> Dict[str, str]:
    """Generate a new API key pair"""
    if scopes is None:
        scopes = ["read"]
    
    # Generate key ID and secret key
    key_id = secrets.token_urlsafe(32)
    secret_key = secrets.token_urlsafe(64)
    
    # Hash the secret key for storage
    hashed_secret = hashlib.sha256(secret_key.encode()).hexdigest()
    
    return {
        "key_id": key_id,
        "secret_key": secret_key,
        "hashed_secret": hashed_secret,
        "name": name,
        "description": description,
        "scopes": scopes,
        "rate_limit_per_minute": rate_limit_per_minute,
        "rate_limit_per_hour": rate_limit_per_hour
    }

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def verify_api_key(key_id: str, secret_key: str, db: Session) -> Optional[APIKey]:
    """Verify API key and return the API key record"""
    # Hash the provided secret key
    hashed_secret = hashlib.sha256(secret_key.encode()).hexdigest()
    
    # Find the API key
    api_key = db.query(APIKey).filter(
        APIKey.key_id == key_id,
        APIKey.secret_key == hashed_secret,
        APIKey.is_active == True
    ).first()
    
    if api_key:
        # Update last used timestamp
        api_key.last_used_at = datetime.utcnow()
        db.commit()
        logger.info("API key verified", key_id=key_id)
        return api_key
    
    logger.warning("Invalid API key attempt", key_id=key_id)
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> APIKey:
    """Get current API key from authorization header"""
    # Extract credentials (format: "Bearer key_id:secret_key")
    try:
        # Remove "Bearer " prefix and split
        auth_string = credentials.credentials
        if ":" not in auth_string:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format. Use: Bearer key_id:secret_key"
            )
        
        key_id, secret_key = auth_string.split(":", 1)
        
        # Verify API key
        api_key = verify_api_key(key_id, secret_key, db)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key"
            )
        
        return api_key
        
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def check_scope(api_key: APIKey, required_scope: str) -> bool:
    """Check if API key has required scope"""
    return required_scope in api_key.scopes

def log_request(db: Session, api_key: APIKey, endpoint: str, method: str, 
                ip_address: str = None, user_agent: str = None, 
                request_data: dict = None, response_status: int = None,
                response_data: dict = None, error_message: str = None):
    """Log request to audit log"""
    audit_log = AuditLog(
        api_key_id=api_key.id,
        endpoint=endpoint,
        method=method,
        ip_address=ip_address,
        user_agent=user_agent,
        request_data=request_data,
        response_status=response_status,
        response_data=response_data,
        error_message=error_message
    )
    db.add(audit_log)
    db.commit()

def validate_email_format(email: str) -> bool:
    """Basic email format validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_email_input(email: str) -> str:
    """Sanitize email input to prevent injection"""
    # Remove potentially dangerous characters
    sanitized = email.strip()
    sanitized = sanitized.replace('\n', '').replace('\r', '')
    sanitized = sanitized.replace(';', '').replace(',', '')
    return sanitized

def sanitize_email_subject(subject: str) -> str:
    """Sanitize email subject to prevent header injection"""
    # Remove newlines and carriage returns
    sanitized = subject.replace('\n', ' ').replace('\r', ' ')
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    return sanitized[:200]  # Limit length

def sanitize_email_body(body: str) -> str:
    """Sanitize email body"""
    # Remove potentially dangerous content
    sanitized = body.replace('\x00', '')  # Remove null bytes
    return sanitized