from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./email_api.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(64), unique=True, index=True, nullable=False)
    secret_key = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    scopes = Column(JSON, nullable=False)  # List of allowed scopes: ["read", "write", "admin"]
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Email credentials (optional - for dynamic email access)
    email_credentials = Column(JSON)  # Encrypted email configuration
    
    def __repr__(self):
        return f"<APIKey(key_id='{self.key_id}', name='{self.name}')>"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, index=True)
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_data = Column(JSON)
    response_status = Column(Integer)
    response_data = Column(JSON)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLog(api_key_id={self.api_key_id}, endpoint='{self.endpoint}', status={self.response_status})>"

# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()