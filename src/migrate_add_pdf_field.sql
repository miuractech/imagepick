-- ================================================================
-- Migration Script: Add PDF URL field to device_test table
-- ================================================================
-- This script safely adds the pdf_url field to existing device_test table
-- Safe to run multiple times - checks if column already exists
-- ================================================================

-- Add pdf_url column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'device_test' 
        AND column_name = 'pdf_url'
        AND table_schema = 'public'
    ) THEN
        ALTER TABLE public.device_test 
        ADD COLUMN pdf_url text NULL;
        
        RAISE NOTICE 'Added pdf_url column to device_test table';
    ELSE
        RAISE NOTICE 'pdf_url column already exists in device_test table';
    END IF;
END $$;

-- Add index for pdf_url field for better query performance
CREATE INDEX IF NOT EXISTS idx_device_test_pdf_url 
ON public.device_test USING btree (pdf_url) 
TABLESPACE pg_default;

-- Add comment to document the new field
COMMENT ON COLUMN public.device_test.pdf_url IS 'URL of the uploaded PDF file in Supabase storage';

-- Display current table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'device_test' 
AND table_schema = 'public'
ORDER BY ordinal_position;
