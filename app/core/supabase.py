import logging

from supabase.client import Client

from supabase import create_client  # type: ignore[attr-defined]

from .config import settings

logger = logging.getLogger(__name__)

# Global client instances (created lazily)
_supabase_service_client: Client | None = None
_supabase_client: Client | None = None


def get_supabase_service_client() -> Client:
    """Get or create the Supabase service client for admin operations."""
    global _supabase_service_client
    if _supabase_service_client is None:
        if not settings.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_KEY is required")
        _supabase_service_client = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
    return _supabase_service_client


def get_supabase_client() -> Client:
    """Get or create the regular Supabase client for auth operations."""
    global _supabase_client
    if _supabase_client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY are required")
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_anon_key
        )
    return _supabase_client


# Legacy aliases for backwards compatibility
supabase_service_client = get_supabase_service_client
supabase_client = get_supabase_client
