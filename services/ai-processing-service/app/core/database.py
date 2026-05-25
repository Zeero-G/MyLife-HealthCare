from supabase import create_client, Client, ClientOptions
from app.core.config import settings

supabase: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SERVICE_KEY,
    options=ClientOptions(schema="ai_schema")
)
