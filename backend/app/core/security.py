from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings


# ─────────────────────────────────────────
# OAuth2 SCHEME
# Tells FastAPI where to find the token
# Points to the login endpoint
# ─────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin/login"
)


# ─────────────────────────────────────────
# TOKEN CONFIGURATION
# ─────────────────────────────────────────

ALGORITHM      = "HS256"        # HMAC SHA-256 — industry standard
TOKEN_EXPIRE_HOURS = 24         # Token valid for 24 hours


# ─────────────────────────────────────────
# TOKEN CREATION
# ─────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload to encode in token
              Example: {"sub": "admin"}

    Returns:
        Signed JWT string
    """
    settings = get_settings()

    # Copy data to avoid mutating the original dict
    to_encode = data.copy()

    # Set token expiry time
    expire = datetime.utcnow() + timedelta(
        hours=TOKEN_EXPIRE_HOURS
    )
    to_encode.update({"exp": expire})

    # Sign and encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.admin_secret_key,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ─────────────────────────────────────────
# TOKEN VERIFICATION
# ─────────────────────────────────────────

def verify_token(token: str) -> dict | None:
    """
    Decode and verify a JWT token.
    Returns payload if valid, None if invalid or expired.

    Args:
        token: JWT string to verify

    Returns:
        Decoded payload dict or None
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.admin_secret_key,
            algorithms=[ALGORITHM]
        )
        return payload

    except JWTError:
        # Token is invalid, expired, or tampered with
        return None


# ─────────────────────────────────────────
# ADMIN VERIFICATION
# FastAPI dependency for protected routes
# ─────────────────────────────────────────

async def get_current_admin(
    token: str = Depends(oauth2_scheme)
) -> str:
    """
    FastAPI dependency that protects admin routes.
    Verifies the JWT token from the Authorization header.

    Usage on protected routes:
        @router.get("/protected")
        async def protected_route(
            admin = Depends(get_current_admin)
        ):

    Args:
        token: JWT token extracted from Authorization header
               by OAuth2PasswordBearer automatically

    Returns:
        Username string if token is valid

    Raises:
        HTTPException 401 if token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify the token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    # Extract username from token payload
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    return username


# ─────────────────────────────────────────
# PASSWORD VERIFICATION
# Constant time comparison to prevent
# timing attacks on password checking
# ─────────────────────────────────────────

def verify_password(
    plain_password: str,
    stored_password: str
) -> bool:
    """
    Verify a password using constant time comparison.
    Prevents timing attacks where an attacker could
    guess the password length by measuring response time.

    Args:
        plain_password:  Password from login request
        stored_password: Password from settings/.env

    Returns:
        True if passwords match, False otherwise
    """
    import hmac
    return hmac.compare_digest(
        plain_password.encode("utf-8"),
        stored_password.encode("utf-8")
    )