-- ================================================================
-- Storage Buckets Creation Script
-- ================================================================
-- This script creates the necessary storage buckets for the image upload system
-- Creates separate buckets for images and PDFs with appropriate policies
-- ================================================================

-- ================================================================
-- Create Images Storage Bucket
-- ================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'images',
    'images', 
    true,
    52428800,  -- 50MB file size limit
    ARRAY['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;
 
-- ================================================================
-- Create PDFs Storage Bucket
-- ================================================================

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'pdfs',
    'pdfs',
    true,
    104857600,  -- 100MB file size limit for PDFs
    ARRAY['application/pdf']
)
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- ================================================================
-- Storage Policies for Images Bucket
-- ================================================================

-- Allow public read access to images
CREATE POLICY IF NOT EXISTS "Public read access for images"
ON storage.objects FOR SELECT
USING (bucket_id = 'images');

-- Allow authenticated users to upload images
CREATE POLICY IF NOT EXISTS "Authenticated users can upload images"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'images' AND auth.role() = 'authenticated');

-- Allow authenticated users to update their own images
CREATE POLICY IF NOT EXISTS "Users can update their own images"
ON storage.objects FOR UPDATE
USING (bucket_id = 'images' AND auth.role() = 'authenticated');

-- Allow authenticated users to delete their own images
CREATE POLICY IF NOT EXISTS "Users can delete their own images"
ON storage.objects FOR DELETE
USING (bucket_id = 'images' AND auth.role() = 'authenticated');

-- ================================================================
-- Storage Policies for PDFs Bucket
-- ================================================================

-- Allow public read access to PDFs
CREATE POLICY IF NOT EXISTS "Public read access for pdfs"
ON storage.objects FOR SELECT
USING (bucket_id = 'pdfs');

-- Allow authenticated users to upload PDFs
CREATE POLICY IF NOT EXISTS "Authenticated users can upload pdfs"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'pdfs' AND auth.role() = 'authenticated');

-- Allow authenticated users to update their own PDFs
CREATE POLICY IF NOT EXISTS "Users can update their own pdfs"
ON storage.objects FOR UPDATE
USING (bucket_id = 'pdfs' AND auth.role() = 'authenticated');

-- Allow authenticated users to delete their own PDFs
CREATE POLICY IF NOT EXISTS "Users can delete their own pdfs"
ON storage.objects FOR DELETE
USING (bucket_id = 'pdfs' AND auth.role() = 'authenticated');

-- ================================================================
-- Alternative: More permissive policies for service role uploads
-- ================================================================
-- Uncomment these if you're using service role for uploads

/*
-- Allow service role to manage images
CREATE POLICY IF NOT EXISTS "Service role can manage images"
ON storage.objects FOR ALL
USING (bucket_id = 'images' AND auth.jwt() ->> 'role' = 'service_role');

-- Allow service role to manage PDFs
CREATE POLICY IF NOT EXISTS "Service role can manage pdfs"
ON storage.objects FOR ALL
USING (bucket_id = 'pdfs' AND auth.jwt() ->> 'role' = 'service_role');
*/

-- ================================================================
-- Enable RLS (Row Level Security) on storage.objects if not already enabled
-- ================================================================

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- ================================================================
-- Display created buckets
-- ================================================================

SELECT 
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types,
    created_at
FROM storage.buckets 
WHERE id IN ('images', 'pdfs')
ORDER BY id;
