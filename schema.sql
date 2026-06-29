-- 1. Create the stores table
CREATE TABLE IF NOT EXISTS public.stores (
    name TEXT PRIMARY KEY,
    region TEXT,
    cuisine TEXT,
    address TEXT,
    time TEXT,
    lat TEXT,
    lon TEXT,
    theme TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Enable Row-Level Security (RLS) to protect data from unauthorized manipulation
ALTER TABLE public.stores ENABLE ROW LEVEL SECURITY;

-- 3. Create a public read-only access policy for anonymous users (SELECT)
CREATE POLICY "Allow public read-only access" 
ON public.stores 
FOR SELECT 
TO anon 
USING (true);

-- 4. Enable service role full access (This is implicit in Supabase, but added here for safety)
CREATE POLICY "Allow service_role write access" 
ON public.stores 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
