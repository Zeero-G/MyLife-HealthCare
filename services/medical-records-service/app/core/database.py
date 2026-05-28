from supabase import create_client, Client, ClientOptions
from app.core.config import settings

supabase_medical: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="medical_schema")
)

supabase_auth: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="auth_schema")
)

supabase_family: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="family_schema")
)

supabase = supabase_medical
