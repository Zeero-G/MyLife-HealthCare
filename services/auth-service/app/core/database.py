from supabase import create_client, Client
from app.core.config import settings

# Supabase client (service-role key bypasses RLS – use only in backend)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
