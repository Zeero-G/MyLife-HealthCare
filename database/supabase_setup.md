# MyLife – Required Supabase SQL Setup

Run these two SQL blocks in your **Supabase SQL Editor**
(Dashboard → SQL Editor → New Query).

---

## ✅ Step 1: Create the `appointments` table (public schema)

```sql
-- public.appointments
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

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON public.appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor  ON public.appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_status  ON public.appointments(status);
```

---

## ✅ Step 2: Create the `linked_accounts` table (public schema)

```sql
-- public.linked_accounts
CREATE TABLE IF NOT EXISTS public.linked_accounts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id       UUID NOT NULL,
    linked_user_id UUID NOT NULL,
    relationship   TEXT NOT NULL DEFAULT 'family',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(owner_id, linked_user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_linked_owner ON public.linked_accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_linked_user  ON public.linked_accounts(linked_user_id);
```

---

## ✅ Step 3: Rebuild Docker containers

After running the SQL, rebuild and restart the backend containers so the new code is loaded:

```bash
cd /home/malan/Desktop/ZeeroG/MyLife-HealthCare
docker-compose up --build
```

---

## Why this works

| Table | Old Schema | New Schema | Why |
|-------|-----------|------------|-----|
| `appointments` | `medical_schema` (not exposed) | `public` | Supabase always exposes `public` via PostgREST |
| `linked_accounts` | `family_schema` (not exposed) | `public` | Same reason |
| `users` | `auth_schema` | `auth_schema` | Auth service already works ✅ |
| `medical_records` | `medical_schema` | `medical_schema` | Already works ✅ |

The `PGRST205` error (`Could not find table in schema cache`) happens when a custom schema like
`medical_schema` or `family_schema` **is not listed in Supabase's exposed schemas**.
Moving `appointments` and `linked_accounts` to `public` avoids that entirely.
