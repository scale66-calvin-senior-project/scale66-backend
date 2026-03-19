from fastapi import Depends
from supabase import Client
from functools import lru_cache

from app.core.supabase import get_supabase_admin_client
from app.core.security import get_current_user_id


def get_supabase() -> Client:
    """
    Dependency to get Supabase admin client.
    Uses singleton pattern for efficiency.
    """
    return get_supabase_admin_client()


def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    """
    Dependency to get current authenticated user ID.
    
    This is a simple pass-through that makes the intent clearer in route signatures.
    The actual authentication is done by get_current_user_id.
    """
    return user_id
