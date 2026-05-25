from supabase import create_client, Client, ClientOptions
from app.core.config import settings

# Primary client – scoped to family_schema
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="family_schema")
)

# Auth client – scoped to auth_schema (users table cross-schema lookups)
supabase_auth: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="auth_schema")
)

# Public client – scoped to public schema (linked_accounts table)
# Tables in public schema are always exposed by Supabase PostgREST by default.
supabase_public: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    # No ClientOptions schema override = uses 'public' (default)
)
