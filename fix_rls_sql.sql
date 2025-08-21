-- Fix RLS policies to allow user registration
-- This SQL should be run in your Supabase SQL Editor

-- 1. CRITICAL: Add policy to allow service role to insert users
CREATE POLICY "Service role can insert users" ON public.users
    FOR INSERT TO service_role
    WITH CHECK (true);

-- 2. Add policy to allow users to insert their own profile during signup
-- This allows authenticated users to create their own user record
CREATE POLICY "Users can create their own profile during signup" ON public.users
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- 3. Ensure service role has proper permissions
GRANT ALL ON public.users TO service_role;

-- 4. Fix ambiguous column reference issues in RLS functions
-- Drop and recreate functions to avoid column ambiguity
DROP FUNCTION IF EXISTS public.is_org_member(UUID);
CREATE OR REPLACE FUNCTION public.is_org_member(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.organization_members om
        WHERE om.org_id = $1 AND om.user_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP FUNCTION IF EXISTS public.is_org_admin(UUID);
CREATE OR REPLACE FUNCTION public.is_org_admin(org_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.organization_members om
        WHERE om.org_id = $1 AND om.user_id = auth.uid() AND om.role = 'admin'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Alternative: If the above doesn't work, temporarily disable RLS for testing
-- (Uncomment the line below ONLY for testing, then re-enable RLS)
-- ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;

-- 6. To re-enable RLS after testing (if you disabled it)
-- ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
