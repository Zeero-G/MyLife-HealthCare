-- ════════════════════════════════════════════════════════════════
-- MYLIFE – Supabase PostgreSQL Schema
-- Run this in the Supabase SQL Editor to initialise all schemas
-- ════════════════════════════════════════════════════════════════

-- ── SCHEMA CREATION ───────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS auth_schema;
CREATE SCHEMA IF NOT EXISTS medical_schema;
CREATE SCHEMA IF NOT EXISTS family_schema;
CREATE SCHEMA IF NOT EXISTS ai_schema;
CREATE SCHEMA IF NOT EXISTS notification_schema;

-- ════════════════════════════════════════════════════════════════
-- AUTH SCHEMA
-- ════════════════════════════════════════════════════════════════
CREATE TABLE auth_schema.users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    full_name     TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'patient' CHECK (role IN ('patient', 'doctor', 'admin', 'family_member')),
    gender        TEXT CHECK (gender IN ('male', 'female')),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE auth_schema.sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES auth_schema.users(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    expires_at    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE auth_schema.users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_own_data ON auth_schema.users
    USING (id = auth.uid());

-- ════════════════════════════════════════════════════════════════
-- MEDICAL SCHEMA
-- ════════════════════════════════════════════════════════════════
CREATE TABLE medical_schema.medical_records (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL,
    title        TEXT NOT NULL,
    record_type  TEXT NOT NULL CHECK (record_type IN ('diagnosis','lab','prescription','imaging','other')),
    description  TEXT,
    doctor_name  TEXT,
    visit_date   DATE,
    diagnosis    TEXT,
    file_url     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE medical_schema.shared_records (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id   UUID NOT NULL REFERENCES medical_schema.medical_records(id) ON DELETE CASCADE,
    token       TEXT UNIQUE NOT NULL,
    created_by  UUID NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE medical_schema.emergency_profiles (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  UUID UNIQUE NOT NULL,
    blood_type               TEXT,
    allergies                TEXT[] DEFAULT '{}',
    chronic_conditions       TEXT[] DEFAULT '{}',
    emergency_contact_name   TEXT,
    emergency_contact_phone  TEXT,
    current_medications      TEXT[] DEFAULT '{}',
    updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════
-- APPOINTMENTS TABLE (NEW)
-- ════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.appointments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id   UUID NOT NULL,
    doctor_id    UUID NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    reason       TEXT,
    status       TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled')),
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE medical_schema.doctor_notes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id  UUID REFERENCES medical_schema.medical_records(id) ON DELETE CASCADE,
    doctor_id  UUID NOT NULL,
    patient_id UUID NOT NULL,
    note       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE medical_schema.audit_log (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID,
    action     TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id  UUID,
    timestamp  TIMESTAMPTZ DEFAULT NOW()
);

-- RLS on medical records
ALTER TABLE medical_schema.medical_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY records_owner ON medical_schema.medical_records
    USING (user_id = auth.uid());

-- ════════════════════════════════════════════════════════════════
-- FAMILY SCHEMA
-- ════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.linked_accounts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id       UUID NOT NULL,
    linked_user_id UUID NOT NULL,
    relationship   TEXT NOT NULL DEFAULT 'family',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (owner_id, linked_user_id)
);

CREATE TABLE family_schema.family_profiles (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID UNIQUE NOT NULL,
    birth_date DATE,
    gender     TEXT,
    notes      TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE family_schema.caregiver_permissions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    caregiver_id    UUID NOT NULL,
    patient_id      UUID NOT NULL,
    permission_level TEXT NOT NULL DEFAULT 'read' CHECK (permission_level IN ('read','write')),
    granted_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE family_schema.menstrual_cycles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL,
    start_date   DATE NOT NULL,
    end_date     DATE,
    cycle_length INTEGER,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE family_schema.pregnancy_records (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    lmp_date   DATE NOT NULL,
    due_date   DATE,
    notes      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════
-- AI SCHEMA
-- ════════════════════════════════════════════════════════════════
CREATE TABLE ai_schema.uploaded_documents (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    file_url   TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE ai_schema.extracted_reports (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID NOT NULL REFERENCES ai_schema.uploaded_documents(id),
    user_id          UUID NOT NULL,
    extracted_data   JSONB NOT NULL,
    confidence_score FLOAT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════
-- NOTIFICATION SCHEMA
-- ════════════════════════════════════════════════════════════════
CREATE TABLE notification_schema.notifications (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL,
    fcm_token      TEXT,
    reminder_type  TEXT,
    scheduled_at   TIMESTAMPTZ,
    status         TEXT DEFAULT 'pending',
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notification_schema.notification_logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL,
    channel    TEXT NOT NULL CHECK (channel IN ('email','push','sms')),
    event      TEXT NOT NULL,
    status     TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════════════════════════════
-- INDEXES (performance)
-- ════════════════════════════════════════════════════════════════
CREATE INDEX idx_medical_records_user_id   ON medical_schema.medical_records(user_id);
CREATE INDEX idx_shared_records_token      ON medical_schema.shared_records(token);
CREATE INDEX IF NOT EXISTS idx_linked_owner ON public.linked_accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_linked_user  ON public.linked_accounts(linked_user_id);
CREATE INDEX idx_cycles_user_id            ON family_schema.menstrual_cycles(user_id);
CREATE INDEX idx_extracted_user_id         ON ai_schema.extracted_reports(user_id);
CREATE INDEX idx_notif_logs_user_id        ON notification_schema.notification_logs(user_id);
-- NEW:
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON public.appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor  ON public.appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status  ON public.appointments(status);
CREATE INDEX idx_doctor_notes_record       ON medical_schema.doctor_notes(record_id);
