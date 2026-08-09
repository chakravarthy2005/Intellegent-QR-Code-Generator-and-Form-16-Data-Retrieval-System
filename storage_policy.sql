-- =====================================================================
-- Supabase Storage - Private Bucket RLS Policy
-- Run this in your Supabase SQL Editor AFTER creating the bucket.
-- =====================================================================

-- Step 1: Allow your application (anon/service_role) to upload and
--         download files from the private 'qr_codes' bucket.
--         This does NOT make files publicly accessible by URL.

CREATE POLICY "App can manage qr_codes"
ON storage.objects
FOR ALL
TO anon, authenticated
USING ( bucket_id = 'qr_codes' )
WITH CHECK ( bucket_id = 'qr_codes' );

-- =====================================================================
-- BUCKET SETUP CHECKLIST (do these steps in the Supabase Dashboard)
-- =====================================================================
-- 1. Go to Storage > New Bucket
-- 2. Name: qr_codes
-- 3. Toggle Public: OFF  (VERY IMPORTANT - keeps files private)
-- 4. Click Save
-- 5. Go to SQL Editor and run the CREATE POLICY statement above
-- =====================================================================
