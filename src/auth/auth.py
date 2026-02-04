import os
import hashlib
import json
import base64
import hmac
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.models.base import SessionLocal
from src.models.users import User

security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "hrms-secret-key-2024")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# API Key from environment variable
API_KEY = os.getenv("API_KEY", "hrms-api-key-2024")

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """Create refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode.update({"exp": expire.timestamp(), "type": "refresh"})
    
    # Simple JWT implementation
    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_encoded}.{payload_encoded}".encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create simple JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    
    # Simple JWT implementation
    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_encoded}.{payload_encoded}".encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"

def verify_token(token: str):
    """Verify JWT token"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Verify signature
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{header_encoded}.{payload_encoded}".encode(),
            hashlib.sha256
        ).digest()
        expected_signature_encoded = base64.urlsafe_b64encode(expected_signature).decode().rstrip('=')
        
        if signature_encoded != expected_signature_encoded:
            raise HTTPException(status_code=401, detail="Invalid token signature")
        
        # Decode payload
        payload_padded = payload_encoded + '=' * (4 - len(payload_encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_padded).decode())
        
        # Check expiration
        if payload.get('exp') and payload['exp'] < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
        
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using simple SHA256"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email: str, password: str) -> User:
    """Authenticate user with email and password"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user
    finally:
        db.close()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token authentication"""
    try:
        payload = verify_token(credentials.credentials)
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")