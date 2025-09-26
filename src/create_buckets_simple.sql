-- ================================================================
-- Simple Storage Buckets Creation Script
-- ================================================================
-- Creates the required storage buckets with basic public access
-- Run this in Supabase SQL Editor or via REST API
-- ================================================================

-- Create Images bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('images', 'images', true)
ON CONFLICT (id) DO NOTHING;

-- Create PDFs bucket  
INSERT INTO storage.buckets (id, name, public)
VALUES ('pdfs', 'pdfs', true)
ON CONFLICT (id) DO NOTHING;

-- Verify buckets were created
SELECT id, name, public, created_at 
FROM storage.buckets 
WHERE id IN ('images', 'pdfs');
