-- ================================================================
-- Database Deployment Script
-- ================================================================
-- This script handles both fresh installations and updates
-- It will create the table if it doesn't exist, or update it if it does
-- ================================================================

-- Check if table exists and handle accordingly
DO $deploy$ 
DECLARE
    table_exists boolean;
    pdf_column_exists boolean;
BEGIN 
    -- Check if table exists
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'device_test' 
        AND table_schema = 'public'
    ) INTO table_exists;
    
    IF NOT table_exists THEN
        RAISE NOTICE 'Creating device_test table from scratch...';
        
        -- Create the complete table with all fields including pdf_url
        CREATE TABLE public.device_test (
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
        
        RAISE NOTICE 'Table device_test created successfully';
        
    ELSE
        RAISE NOTICE 'Table device_test already exists, checking for pdf_url column...';
        
        -- Check if pdf_url column exists
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'device_test' 
            AND column_name = 'pdf_url'
            AND table_schema = 'public'
        ) INTO pdf_column_exists;
        
        IF NOT pdf_column_exists THEN
            -- Add the pdf_url column
            ALTER TABLE public.device_test 
            ADD COLUMN pdf_url text NULL;
            
            RAISE NOTICE 'Added pdf_url column to existing device_test table';
        ELSE
            RAISE NOTICE 'pdf_url column already exists';
        END IF;
    END IF;
END $deploy$;

-- ================================================================
-- Create all indexes (safe to run multiple times)
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_device_test_data ON public.device_test USING gin (data) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_data_type ON public.device_test USING btree (data_type) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_device_id ON public.device_test USING btree (device_id) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_folder_name ON public.device_test USING btree (folder_name) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_metadata ON public.device_test USING gin (metadata) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_results ON public.device_test USING gin (test_results) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_status ON public.device_test USING btree (test_status) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_test_date ON public.device_test USING btree (test_date) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_device_test_pdf_url ON public.device_test USING btree (pdf_url) TABLESPACE pg_default;

-- ================================================================
-- Create or update trigger
-- ================================================================

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS update_device_test_updated_at ON public.device_test;
CREATE TRIGGER update_device_test_updated_at BEFORE UPDATE
ON public.device_test FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- Add table and column comments
-- ================================================================

COMMENT ON TABLE public.device_test IS 'Stores device test results with images, PDFs, and metadata';
COMMENT ON COLUMN public.device_test.pdf_url IS 'URL of the uploaded PDF file in Supabase storage';
COMMENT ON COLUMN public.device_test.images IS 'Array of image URLs in Supabase storage';
COMMENT ON COLUMN public.device_test.metadata IS 'JSON metadata including upload information and file details';

-- ================================================================
-- Display final table structure
-- ================================================================

\echo 'Final table structure:'
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'device_test' 
AND table_schema = 'public'
ORDER BY ordinal_position;
