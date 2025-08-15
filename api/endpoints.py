from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from models.database import get_db, APIKey, AuditLog
from utils.auth import (
    get_current_api_key, 
    generate_api_key, 
    create_access_token,
    verify_token,
    log_request,
    check_scope
)
from utils.rate_limiter import rate_limit_middleware
from schemas import (
    APIKeyCreate, APIKeyResponse, APIKeyUpdate, EmailRequest, EmailBatchRequest,
    EmailFilterRequest, EmailListResponse, BatchOperationResponse, ErrorResponse,
    SuccessResponse, HealthCheckResponse, MetricsResponse
)
from utils.secure_email import secure_email_client

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.post("/api-keys", response_model=SuccessResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    try:
        # Generate API key pair
        key_data = generate_api_key(
            name=api_key_data.name,
            description=api_key_data.description,
            scopes=[scope.value for scope in api_key_data.scopes],
            rate_limit_per_minute=api_key_data.rate_limit_per_minute,
            rate_limit_per_hour=api_key_data.rate_limit_per_hour
        )
        
        # Create API key record
        db_api_key = APIKey(
            key_id=key_data["key_id"],
            secret_key=key_data["hashed_secret"],
            name=key_data["name"],
            description=key_data["description"],
            scopes=key_data["scopes"],
            rate_limit_per_minute=key_data["rate_limit_per_minute"],
            rate_limit_per_hour=key_data["rate_limit_per_hour"]
        )
        
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        
        # Log the creation
        log_request(
            db=db,
            api_key=db_api_key,
            endpoint="/api-keys",
            method="POST",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data=api_key_data.dict(),
            response_status=status.HTTP_201_CREATED,
            response_data={"key_id": key_data["key_id"], "secret_key": key_data["secret_key"]}
        )
        
        return SuccessResponse(
            status="success",
            message="API key created successfully",
            data={
                "key_id": key_data["key_id"],
                "secret_key": key_data["secret_key"],
                "name": key_data["name"],
                "description": key_data["description"],
                "scopes": key_data["scopes"],
                "rate_limits": {
                    "per_minute": key_data["rate_limit_per_minute"],
                    "per_hour": key_data["rate_limit_per_hour"]
                }
            }
        )
        
    except Exception as e:
        logger.error("Failed to create API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """List all API keys (admin only)"""
    if not check_scope(current_api_key, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    api_keys = db.query(APIKey).all()
    return api_keys

@router.get("/api-keys/me", response_model=APIKeyResponse)
async def get_current_api_key_info(
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Get current API key information"""
    return current_api_key

@router.put("/api-keys/{key_id}", response_model=SuccessResponse)
async def update_api_key(
    key_id: str,
    api_key_update: APIKeyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Update API key information"""
    try:
        # Check if user can update this key (admin or own key)
        if not check_scope(current_api_key, "admin") and current_api_key.key_id != key_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Find the API key
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update fields
        update_data = api_key_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email_credentials" and value:
                # Encrypt email credentials
                encrypted_password = secure_email_client.cipher_suite.encrypt(
                    value["password"].encode()
                ).decode()
                value["password"] = f"encrypted:{encrypted_password}"
            
            setattr(api_key, field, value)
        
        api_key.updated_at = datetime.utcnow()
        db.commit()
        
        # Log the update
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint=f"/api-keys/{key_id}",
            method="PUT",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data=api_key_update.dict(),
            response_status=status.HTTP_200_OK
        )
        
        return SuccessResponse(
            status="success",
            message="API key updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
async def delete_api_key(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Delete API key (admin only)"""
    if not check_scope(current_api_key, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        api_key = db.query(APIKey).filter(APIKey.key_id == key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        db.delete(api_key)
        db.commit()
        
        # Log the deletion
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint=f"/api-keys/{key_id}",
            method="DELETE",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            response_status=status.HTTP_200_OK
        )
        
        return SuccessResponse(
            status="success",
            message="API key deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.post("/emails", response_model=SuccessResponse)
async def send_email(
    email_request: EmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Send email using API key's email credentials or default"""
    try:
        if not check_scope(current_api_key, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Use API key's email credentials if available, otherwise use default
        email_credentials = current_api_key.email_credentials
        if not email_credentials:
            # Fallback to default credentials (for backward compatibility)
            from utils.email_utils import SENDER_EMAIL, APP_PASSWORD
            email_credentials = {
                "email_address": SENDER_EMAIL,
                "password": APP_PASSWORD,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            }
        
        # Send email
        result = secure_email_client.send_email(
            email_credentials=email_credentials,
            receiver_email=email_request.receiver_email,
            subject=email_request.subject,
            body=email_request.body
        )
        
        # Log the operation
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint="/emails",
            method="POST",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data=email_request.dict(),
            response_status=status.HTTP_200_OK if result["status"] == "success" else status.HTTP_400_BAD_REQUEST,
            response_data=result
        )
        
        return SuccessResponse(
            status=result["status"],
            message=result["message"],
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.get("/emails", response_model=EmailListResponse)
async def read_emails(
    filter_by: str = "today",
    mark_as_read: bool = False,
    request: Request = None,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Read emails using API key's email credentials or default"""
    try:
        if not check_scope(current_api_key, "read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Use API key's email credentials if available, otherwise use default
        email_credentials = current_api_key.email_credentials
        if not email_credentials:
            # Fallback to default credentials (for backward compatibility)
            from utils.email_utils import SENDER_EMAIL, APP_PASSWORD
            email_credentials = {
                "email_address": SENDER_EMAIL,
                "password": APP_PASSWORD,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            }
        
        # Get emails
        emails = secure_email_client.get_unread_emails(
            email_credentials=email_credentials,
            filter_by=filter_by,
            mark_as_read=mark_as_read
        )
        
        # Log the operation
        if request:
            log_request(
                db=db,
                api_key=current_api_key,
                endpoint="/emails",
                method="GET",
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                request_data={"filter_by": filter_by, "mark_as_read": mark_as_read},
                response_status=status.HTTP_200_OK,
                response_data={"count": len(emails)}
            )
        
        return EmailListResponse(
            count=len(emails),
            emails=emails
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to read emails", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.post("/emails/{id}/mark-read", response_model=SuccessResponse)
async def mark_email_as_read(
    id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Mark email as read using API key's email credentials or default"""
    try:
        if not check_scope(current_api_key, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Use API key's email credentials if available, otherwise use default
        email_credentials = current_api_key.email_credentials
        if not email_credentials:
            # Fallback to default credentials (for backward compatibility)
            from utils.email_utils import SENDER_EMAIL, APP_PASSWORD
            email_credentials = {
                "email_address": SENDER_EMAIL,
                "password": APP_PASSWORD,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            }
        
        # Mark email as read
        result = secure_email_client.mark_email_as_read(
            email_credentials=email_credentials,
            email_id=id
        )
        
        # Log the operation
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint=f"/emails/{id}/mark-read",
            method="POST",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data={"email_id": id},
            response_status=status.HTTP_200_OK if result["status"] == "success" else status.HTTP_400_BAD_REQUEST,
            response_data=result
        )
        
        return SuccessResponse(
            status=result["status"],
            message=result["message"],
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to mark email as read", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.post("/emails/mark-read-batch", response_model=BatchOperationResponse)
async def mark_emails_as_read_batch(
    batch_request: EmailBatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Mark multiple emails as read using API key's email credentials or default"""
    try:
        if not check_scope(current_api_key, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Use API key's email credentials if available, otherwise use default
        email_credentials = current_api_key.email_credentials
        if not email_credentials:
            # Fallback to default credentials (for backward compatibility)
            from utils.email_utils import SENDER_EMAIL, APP_PASSWORD
            email_credentials = {
                "email_address": SENDER_EMAIL,
                "password": APP_PASSWORD,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            }
        
        # Mark emails as read in batch
        result = secure_email_client.mark_emails_as_read_batch(
            email_credentials=email_credentials,
            email_ids=batch_request.email_ids
        )
        
        # Log the operation
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint="/emails/mark-read-batch",
            method="POST",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data=batch_request.dict(),
            response_status=status.HTTP_200_OK,
            response_data=result
        )
        
        return BatchOperationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to batch mark emails as read", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )

@router.post("/emails/mark-unread-batch", response_model=BatchOperationResponse)
async def mark_emails_as_unread_batch(
    batch_request: EmailBatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_api_key: APIKey = Depends(get_current_api_key)
):
    """Mark multiple emails as unread using API key's email credentials or default"""
    try:
        if not check_scope(current_api_key, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Use API key's email credentials if available, otherwise use default
        email_credentials = current_api_key.email_credentials
        if not email_credentials:
            # Fallback to default credentials (for backward compatibility)
            from utils.email_utils import SENDER_EMAIL, APP_PASSWORD
            email_credentials = {
                "email_address": SENDER_EMAIL,
                "password": APP_PASSWORD,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993
            }
        
        # Mark emails as unread in batch
        result = secure_email_client.mark_emails_as_unread_batch(
            email_credentials=email_credentials,
            email_ids=batch_request.email_ids
        )
        
        # Log the operation
        log_request(
            db=db,
            api_key=current_api_key,
            endpoint="/emails/mark-unread-batch",
            method="POST",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_data=batch_request.dict(),
            response_status=status.HTTP_200_OK,
            response_data=result
        )
        
        return BatchOperationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to batch mark emails as unread", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )