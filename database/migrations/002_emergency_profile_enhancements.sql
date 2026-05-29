-- Emergency profile enhancements: status fields, contacts JSONB, confirmation timestamp.
-- Run in Supabase SQL Editor on existing databases.

ALTER TABLE medical_schema.emergency_profiles
    ADD COLUMN IF NOT EXISTS emergency_contacts JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS allergies_status TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS conditions_status TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS medications_status TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS last_confirmed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS show_emergency_contacts_publicly BOOLEAN NOT NULL DEFAULT FALSE;

-- Add check constraints if columns were added without them
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'emergency_profiles_allergies_status_check'
    ) THEN
        ALTER TABLE medical_schema.emergency_profiles
            ADD CONSTRAINT emergency_profiles_allergies_status_check
            CHECK (allergies_status IN ('unknown', 'none', 'has_items'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'emergency_profiles_conditions_status_check'
    ) THEN
        ALTER TABLE medical_schema.emergency_profiles
            ADD CONSTRAINT emergency_profiles_conditions_status_check
            CHECK (conditions_status IN ('unknown', 'none', 'has_items'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'emergency_profiles_medications_status_check'
    ) THEN
        ALTER TABLE medical_schema.emergency_profiles
            ADD CONSTRAINT emergency_profiles_medications_status_check
            CHECK (medications_status IN ('unknown', 'none', 'has_items'));
    END IF;
END $$;

-- Migrate legacy single contact into emergency_contacts JSONB
UPDATE medical_schema.emergency_profiles
SET emergency_contacts = jsonb_build_array(
    jsonb_build_object(
        'name', emergency_contact_name,
        'phone', emergency_contact_phone,
        'relationship', 'Emergency contact',
        'priority', 1,
        'notes', NULL
    )
)
WHERE emergency_contact_name IS NOT NULL
  AND emergency_contact_phone IS NOT NULL
  AND (emergency_contacts IS NULL OR emergency_contacts = '[]'::jsonb);

-- Infer status from existing arrays where still unknown
UPDATE medical_schema.emergency_profiles
SET allergies_status = 'has_items'
WHERE allergies_status = 'unknown'
  AND allergies IS NOT NULL
  AND array_length(allergies, 1) > 0;

UPDATE medical_schema.emergency_profiles
SET conditions_status = 'has_items'
WHERE conditions_status = 'unknown'
  AND chronic_conditions IS NOT NULL
  AND array_length(chronic_conditions, 1) > 0;

UPDATE medical_schema.emergency_profiles
SET medications_status = 'has_items'
WHERE medications_status = 'unknown'
  AND current_medications IS NOT NULL
  AND array_length(current_medications, 1) > 0;
