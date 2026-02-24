"""Custom type definitions for the application"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    SupabaseClient = "supabase.Client"  # String literal instead of import
else:
    SupabaseClient = Any
