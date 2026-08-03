/*
# EcoBiome aquatic ecosystem simulator schema

1. Purpose
- Persist aquatic ecosystem simulation data: water bodies (aquariums, ponds,
  aquaponic systems), their physical parameters, time-series measurements,
  diagnostic sessions with causal explanations, scientific journal entries
  (traceable knowledge), and a media library.

2. New Tables
- `water_bodies`: a simulated aquatic environment (aquarium, pond, or aquaponic
  system). Columns: id, name, type (aquarium/pond/aquaponic), volume_liters,
  status (stable/warning/critical), created_at, updated_at.
- `organisms`: living components of a water body (plants, bacteria, microfauna,
  animals). Columns: id, water_body_id, name, kind (plant/bacteria/microfauna/
  animal), population, health (0-100), created_at.
- `measurements`: time-series sensor readings for a water body. Columns: id,
  water_body_id, metric (temperature/ph/ammonia/nitrite/nitrate/oxygen/
  phosphate/iron/co2/gh/kh), value, unit, recorded_at.
- `diagnostics`: a diagnostic session analyzing a water body's state. Columns:
  id, water_body_id, status (healthy/warning/critical), summary, root_cause,
  confidence (0-100), created_at.
- `diagnostic_findings`: individual findings within a diagnostic session,
  including a causal chain explanation. Columns: id, diagnostic_id, severity
  (info/warning/critical), metric, observation, explanation, causal_chain
  (jsonb array of steps).
- `journal_entries`: traceable scientific knowledge entries. Columns: id,
  title, source (youtube_transcript/manual/literature), source_ref, tags
  (text[]), summary, content, created_at.
- `media_items`: media library entries (images of water bodies, organisms,
  habitats). Columns: id, water_body_id, title, kind (photo/illustration/
  diagram), url, caption, created_at.

3. Security
- Single-tenant app (no sign-in). RLS enabled on every table. Policies use
  `TO anon, authenticated` with `USING (true)` / `WITH CHECK (true)` because
  the data is intentionally shared/public.
*/

-- Water bodies
CREATE TABLE IF NOT EXISTS water_bodies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL DEFAULT 'aquarium' CHECK (type IN ('aquarium', 'pond', 'aquaponic')),
  volume_liters numeric NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'stable' CHECK (status IN ('stable', 'warning', 'critical')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE water_bodies ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "wb_select" ON water_bodies;
CREATE POLICY "wb_select" ON water_bodies FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "wb_insert" ON water_bodies;
CREATE POLICY "wb_insert" ON water_bodies FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "wb_update" ON water_bodies;
CREATE POLICY "wb_update" ON water_bodies FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "wb_delete" ON water_bodies;
CREATE POLICY "wb_delete" ON water_bodies FOR DELETE TO anon, authenticated USING (true);

-- Organisms
CREATE TABLE IF NOT EXISTS organisms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  water_body_id uuid NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
  name text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('plant', 'bacteria', 'microfauna', 'animal')),
  population integer NOT NULL DEFAULT 1,
  health integer NOT NULL DEFAULT 80 CHECK (health >= 0 AND health <= 100),
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE organisms ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "org_select" ON organisms;
CREATE POLICY "org_select" ON organisms FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "org_insert" ON organisms;
CREATE POLICY "org_insert" ON organisms FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "org_update" ON organisms;
CREATE POLICY "org_update" ON organisms FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "org_delete" ON organisms;
CREATE POLICY "org_delete" ON organisms FOR DELETE TO anon, authenticated USING (true);

-- Measurements
CREATE TABLE IF NOT EXISTS measurements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  water_body_id uuid NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
  metric text NOT NULL,
  value numeric NOT NULL,
  unit text NOT NULL DEFAULT '',
  recorded_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "meas_select" ON measurements;
CREATE POLICY "meas_select" ON measurements FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "meas_insert" ON measurements;
CREATE POLICY "meas_insert" ON measurements FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "meas_update" ON measurements;
CREATE POLICY "meas_update" ON measurements FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "meas_delete" ON measurements;
CREATE POLICY "meas_delete" ON measurements FOR DELETE TO anon, authenticated USING (true);

-- Diagnostics
CREATE TABLE IF NOT EXISTS diagnostics (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  water_body_id uuid NOT NULL REFERENCES water_bodies(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'healthy' CHECK (status IN ('healthy', 'warning', 'critical')),
  summary text NOT NULL DEFAULT '',
  root_cause text NOT NULL DEFAULT '',
  confidence integer NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 100),
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE diagnostics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "diag_select" ON diagnostics;
CREATE POLICY "diag_select" ON diagnostics FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "diag_insert" ON diagnostics;
CREATE POLICY "diag_insert" ON diagnostics FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "diag_update" ON diagnostics;
CREATE POLICY "diag_update" ON diagnostics FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "diag_delete" ON diagnostics;
CREATE POLICY "diag_delete" ON diagnostics FOR DELETE TO anon, authenticated USING (true);

-- Diagnostic findings
CREATE TABLE IF NOT EXISTS diagnostic_findings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  diagnostic_id uuid NOT NULL REFERENCES diagnostics(id) ON DELETE CASCADE,
  severity text NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
  metric text NOT NULL DEFAULT '',
  observation text NOT NULL DEFAULT '',
  explanation text NOT NULL DEFAULT '',
  causal_chain jsonb NOT NULL DEFAULT '[]'::jsonb
);
ALTER TABLE diagnostic_findings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "df_select" ON diagnostic_findings;
CREATE POLICY "df_select" ON diagnostic_findings FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "df_insert" ON diagnostic_findings;
CREATE POLICY "df_insert" ON diagnostic_findings FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "df_update" ON diagnostic_findings;
CREATE POLICY "df_update" ON diagnostic_findings FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "df_delete" ON diagnostic_findings;
CREATE POLICY "df_delete" ON diagnostic_findings FOR DELETE TO anon, authenticated USING (true);

-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  source text NOT NULL DEFAULT 'manual' CHECK (source IN ('youtube_transcript', 'manual', 'literature')),
  source_ref text NOT NULL DEFAULT '',
  tags text[] NOT NULL DEFAULT '{}',
  summary text NOT NULL DEFAULT '',
  content text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "je_select" ON journal_entries;
CREATE POLICY "je_select" ON journal_entries FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "je_insert" ON journal_entries;
CREATE POLICY "je_insert" ON journal_entries FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "je_update" ON journal_entries;
CREATE POLICY "je_update" ON journal_entries FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "je_delete" ON journal_entries;
CREATE POLICY "je_delete" ON journal_entries FOR DELETE TO anon, authenticated USING (true);

-- Media items
CREATE TABLE IF NOT EXISTS media_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  water_body_id uuid REFERENCES water_bodies(id) ON DELETE SET NULL,
  title text NOT NULL,
  kind text NOT NULL DEFAULT 'photo' CHECK (kind IN ('photo', 'illustration', 'diagram')),
  url text NOT NULL,
  caption text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE media_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "mi_select" ON media_items;
CREATE POLICY "mi_select" ON media_items FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "mi_insert" ON media_items;
CREATE POLICY "mi_insert" ON media_items FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "mi_update" ON media_items;
CREATE POLICY "mi_update" ON media_items FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "mi_delete" ON media_items;
CREATE POLICY "mi_delete" ON media_items FOR DELETE TO anon, authenticated USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_organisms_water_body ON organisms(water_body_id);
CREATE INDEX IF NOT EXISTS idx_measurements_water_body ON measurements(water_body_id);
CREATE INDEX IF NOT EXISTS idx_measurements_recorded ON measurements(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_diagnostics_water_body ON diagnostics(water_body_id);
CREATE INDEX IF NOT EXISTS idx_findings_diagnostic ON diagnostic_findings(diagnostic_id);