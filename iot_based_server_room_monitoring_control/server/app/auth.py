from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import logging

from .database import get_db
from .models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
# Log the loaded SECRET_KEY to verify
logger.info(f"Loaded SECRET_KEY: '{SECRET_KEY[:5]}...{SECRET_KEY[-5:]}'" if SECRET_KEY else "SECRET_KEY not loaded!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
# Ensure tokenUrl starts with a slash
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Load expected API Key for Pi communication
EXPECTED_PI_API_KEY = os.getenv("RASPBERRY_PI_API_KEY")

# API Key dependency function
def get_api_key(
    x_api_key: Optional[str] = Header(None, description="API Key for Raspberry Pi communication")
) -> str:
    """Dependency function to validate the X-API-Key header."""
    if not EXPECTED_PI_API_KEY:
        logger.critical("RASPBERRY_PI_API_KEY is not set in the server environment!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key validation mechanism not configured on server."
        )
    if not x_api_key:
        logger.warning("Missing X-API-Key header in request.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key header (X-API-Key)",
        )
    if x_api_key != EXPECTED_PI_API_KEY:
        logger.warning("Invalid API Key received in X-API-Key header.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return x_api_key # Return the key if valid (could also return True)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use the configured expiration time by default
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Explicitly pass key to decode
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM]) 
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Log the username we are looking for
    logger.debug(f"Looking up user '{username}' in database for token validation.")
    # --- Remove DB Session Logging ---
    # if db is None:
    #     logger.error("!!! DB session is None in get_current_user !!!")
    #     raise credentials_exception
    # if not isinstance(db, Session):
    #     logger.error(f"!!! DB object is not a Session in get_current_user (type: {type(db)}) !!!")
    #     raise credentials_exception
    # logger.debug(f"DB session object in get_current_user: {db}")
    # --- End DB Session Logging ---
    user = db.query(User).filter(User.username == username).first()
    # Log whether the user was found
    logger.debug(f"Database query result for user '{username}': {'Found' if user else 'Not Found'}") 
    if user is None:
        raise credentials_exception
    return user

def create_user(db: Session, username: str, password: str, email: str, is_admin: bool = False) -> User:
    """Create a new user"""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        hashed_password=hashed_password,
        email=email,
        is_active=True,
        is_admin=is_admin
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise