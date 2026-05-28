from supabase import create_client, Client, ClientOptions
from app.core.config import settings

supabase_ai: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="ai_schema")
)

supabase_medical: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="medical_schema")
)

supabase = supabase_ai
