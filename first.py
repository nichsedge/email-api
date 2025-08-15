from sqlalchemy.orm import Session
from datetime import datetime
from models.database import get_db, APIKey, create_tables
from utils.auth import generate_api_key  # the function you already wrote

def create_first_admin_key(db: Session):
    # Generate key data
    key_data = generate_api_key(
        name="Initial Admin",
        description="First admin API key",
        scopes=["admin", "read", "write"],
        rate_limit_per_minute=500,
        rate_limit_per_hour=5000
    )
    
    api_key = APIKey(
        key_id=key_data["key_id"],
        secret_key=key_data["hashed_secret"],  # store HASH, not raw
        name=key_data["name"],
        description=key_data["description"],
        scopes=key_data["scopes"],
        rate_limit_per_minute=key_data["rate_limit_per_minute"],
        rate_limit_per_hour=key_data["rate_limit_per_hour"],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    print("✅ Admin API Key Created")
    print(f"Key ID: {key_data['key_id']}")
    print(f"Secret Key: {key_data['secret_key']}")  # only show now
    return key_data

if __name__ == "__main__":
    create_tables()
    with next(get_db()) as db:
        create_first_admin_key(db)
