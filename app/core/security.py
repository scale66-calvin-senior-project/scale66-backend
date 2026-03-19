from typing import Optional
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


def verify_jwt_token(token: str) -> dict:
    """
    Verify Supabase JWT token and extract payload.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    if not settings.supabase_jwt_secret:
        raise AuthenticationError("SUPABASE_JWT_SECRET is not configured")
    
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase tokens don't always have audience
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to extract and validate user_id from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        
    Returns:
        str: User ID (UUID) from token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        
        # Extract user_id from Supabase JWT payload
        # Supabase uses 'sub' claim for user ID
        user_id = payload.get("sub")
        
        if not user_id:
            logger.error("Token payload missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier"
            )
        
        return user_id
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


# Optional: For endpoints that can work with or without authentication
def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional authentication dependency.
    Returns user_id if valid token provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        return payload.get("sub")
    except Exception:
        return None
