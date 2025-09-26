-- ================================================================
-- Device Test Table Schema
-- ================================================================
-- This script creates the device_test table and associated indexes
-- Safe to run multiple times - uses IF NOT EXISTS clauses
-- ================================================================

-- Create the main device_test table
CREATE TABLE IF NOT EXISTS public.device_test (
  id uuid not null default gen_random_uuid (),
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  folder_name text not null,
  images text[] null default '{}'::text[],
  pdf_url text null,
  device_id uuid null,
  device_name text null,
  device_type text null,
  test_results jsonb null,
  test_date timestamp with time zone null,
  test_status text null,
  upload_batch text null,
  notes text null,
  metadata jsonb null default '{}'::jsonb,
  data jsonb null,
  data_type text null,
  constraint device_test_pkey primary key (id),
  constraint unique_folder_device unique (folder_name, device_id),
  constraint device_test_device_id_fkey foreign KEY (device_id) references devices (id),
  constraint device_test_test_status_check check (
    (
      test_status = any (
        array[
          'pending'::text,
          'passed'::text,
          'failed'::text,
          'incomplete'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;

-- ================================================================
-- Indexes for performance optimization
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_device_test_data ON public.device_test USING gin (data) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_data_type ON public.device_test USING btree (data_type) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_device_id ON public.device_test USING btree (device_id) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_folder_name ON public.device_test USING btree (folder_name) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_metadata ON public.device_test USING gin (metadata) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_results ON public.device_test USING gin (test_results) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_status ON public.device_test USING btree (test_status) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_device_test_test_date ON public.device_test USING btree (test_date) TABLESPACE pg_default;

-- Index for PDF URL field
CREATE INDEX IF NOT EXISTS idx_device_test_pdf_url ON public.device_test USING btree (pdf_url) TABLESPACE pg_default;

-- ================================================================
-- Triggers for automatic timestamp updates
-- ================================================================
-- Note: Assumes update_updated_at_column() function exists

-- Create trigger (drops first if exists to handle updates safely)
DROP TRIGGER IF EXISTS update_device_test_updated_at ON public.device_test;
CREATE TRIGGER update_device_test_updated_at BEFORE UPDATE
ON public.device_test FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- Comments for documentation
-- ================================================================

COMMENT ON TABLE public.device_test IS 'Stores device test results with images, PDFs, and metadata';
COMMENT ON COLUMN public.device_test.pdf_url IS 'URL of the uploaded PDF file in Supabase storage';
COMMENT ON COLUMN public.device_test.images IS 'Array of image URLs in Supabase storage';
COMMENT ON COLUMN public.device_test.metadata IS 'JSON metadata including upload information and file details';