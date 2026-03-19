from supabase import create_client, Client
from functools import lru_cache

from app.core.config import settings


@lru_cache()
def get_supabase_admin_client() -> Client:
    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL is not configured.")
    
    if not settings.supabase_service_key:
        raise ValueError("SUPABASE_SERVICE_KEY is not configured.")
    
    return create_client(settings.supabase_url, settings.supabase_service_key)
