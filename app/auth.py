from datetime import datetime, timedelta
from typing import Optional, Tuple
import os
import sqlite3
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.expanduser("~/.ai-agent-key/master.env"))

# Security configuration
SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# SQLite database configuration
DB_PATH = os.getenv("DB_PATH", "users/users.db")

def ensure_db_exists():
    """Ensure database and users table exist"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[dict]:
    """Get a user from the database"""
    ensure_db_exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None

def create_user(username: str, password: str) -> bool:
    """Create a new user in the database"""
    if get_user(username):
        return False  # User already exists

    hashed_password = get_password_hash(password)

    ensure_db_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    return {"username": username}

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
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username}
    except JWTError:
        return None

def verify_token_with_expiry(token: str) -> Tuple[Optional[dict], Optional[datetime]]:
    """Verify JWT token and return user info with expiration time"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp_timestamp = payload.get("exp")

        if username is None or exp_timestamp is None:
            return None, None

        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        return {"username": username}, exp_datetime
    except JWTError:
        return None, None

def is_token_near_expiry(token: str, threshold_hours: int = 2) -> bool:
    """Check if token will expire within threshold hours"""
    user, exp_time = verify_token_with_expiry(token)
    if not user or not exp_time:
        return True  # Treat invalid tokens as expired

    time_remaining = exp_time - datetime.utcnow()
    threshold = timedelta(hours=threshold_hours)

    return time_remaining <= threshold

def refresh_token_if_needed(token: str, threshold_hours: int = 2) -> Optional[str]:
    """Refresh token if it's near expiry, return new token or None"""
    user, exp_time = verify_token_with_expiry(token)
    if not user or not exp_time:
        return None

    if is_token_near_expiry(token, threshold_hours):
        # Create new token with full expiration time
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        return new_token

    return None  # No refresh needed

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
        
    user = verify_token(credentials.credentials)
    if user is None:
        raise credentials_exception
    return user



def get_user_from_session(request: Request) -> Optional[dict]:
    """Get user from session cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    return verify_token(token)
