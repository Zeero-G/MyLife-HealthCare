-- Run in Supabase SQL Editor if emergency_access_tokens is not yet present.

CREATE TABLE IF NOT EXISTS medical_schema.emergency_access_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    token      TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emergency_access_token
    ON medical_schema.emergency_access_tokens(token);
