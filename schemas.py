from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FilterBy(str, Enum):
    """Email filter options"""
    TODAY = "today"
    ALL = "all"
    DATE_RANGE = "date_range"

class EmailScope(str, Enum):
    """API key scopes"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class APIKeyCreate(BaseModel):
    """Schema for creating API key"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    scopes: List[EmailScope] = Field(default=["read"], description="List of allowed scopes")
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000, description="Requests per minute limit")
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=10000, description="Requests per hour limit")

class APIKeyResponse(BaseModel):
    """Schema for API key response"""
    id: int
    key_id: str
    name: str
    description: Optional[str]
    scopes: List[EmailScope]
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EmailRequest(BaseModel):
    """Schema for sending email"""
    receiver_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    body: str = Field(..., min_length=1, max_length=50000, description="Email body")

    @validator('subject')
    def validate_subject(cls, v):
        """Validate and sanitize email subject"""
        if len(v) > 200:
            raise ValueError("Subject too long (max 200 characters)")
        # Check for potential header injection
        if '\n' in v or '\r' in v:
            raise ValueError("Subject cannot contain newlines")
        return v.strip()

    @validator('body')
    def validate_body(cls, v):
        """Validate email body"""
        if len(v) > 50000:
            raise ValueError("Email body too long (max 50000 characters)")
        return v

class EmailBatchRequest(BaseModel):
    """Schema for batch email operations"""
    email_ids: List[str] = Field(..., min_items=1, max_items=100, description="List of email IDs")

class EmailFilterRequest(BaseModel):
    """Schema for email filtering"""
    filter_by: FilterBy = Field(default=FilterBy.TODAY, description="Filter option")
    start_date: Optional[datetime] = Field(None, description="Start date for date range filter")
    end_date: Optional[datetime] = Field(None, description="End date for date range filter")
    mark_as_read: bool = Field(default=False, description="Mark emails as read after retrieval")

    @validator('start_date', 'end_date')
    def validate_dates(cls, v, values):
        """Validate date range"""
        if values.get('filter_by') == FilterBy.DATE_RANGE:
            if v is None:
                raise ValueError("Date range filter requires both start_date and end_date")
        return v

    @validator('filter_by')
    def validate_filter_by(cls, v, values):
        """Validate filter parameters"""
        if v == FilterBy.DATE_RANGE:
            if values.get('start_date') is None or values.get('end_date') is None:
                raise ValueError("Date range filter requires both start_date and end_date")
            if values.get('start_date') >= values.get('end_date'):
                raise ValueError("start_date must be before end_date")
        return v

class EmailResponse(BaseModel):
    id: str
    subject: str
    from_email: Optional[str] = None
    body: str
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None

class EmailListResponse(BaseModel):
    """Schema for email list response"""
    count: int
    emails: List[EmailResponse]

class BatchOperationResponse(BaseModel):
    """Schema for batch operation response"""
    status: str
    total_processed: int
    success_count: int
    failure_count: int
    details: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """Schema for success response"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

class APIKeyCredentials(BaseModel):
    """Schema for API key email credentials"""
    email_provider: str = Field(..., description="Email provider (gmail, outlook, etc.)")
    email_address: EmailStr = Field(..., description="Email address")
    smtp_server: str = Field(..., description="SMTP server address")
    smtp_port: int = Field(..., ge=1, le=65535, description="SMTP port")
    imap_server: str = Field(..., description="IMAP server address")
    imap_port: int = Field(..., ge=1, le=65535, description="IMAP port")
    allowed_domains: List[str] = Field(default=[], description="Allowed email domains")

class APIKeyUpdate(BaseModel):
    """Schema for updating API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scopes: Optional[List[EmailScope]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None
    email_credentials: Optional[APIKeyCredentials] = None

class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    database: str
    uptime: float

class MetricsResponse(BaseModel):
    """Schema for metrics response"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    active_api_keys: int
    rate_limit_hits: int
    average_response_time: float
    top_endpoints: List[Dict[str, Any]]