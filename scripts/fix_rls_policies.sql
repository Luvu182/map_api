-- Disable RLS temporarily for data import
ALTER TABLE states DISABLE ROW LEVEL SECURITY;
ALTER TABLE counties DISABLE ROW LEVEL SECURITY;
ALTER TABLE cities DISABLE ROW LEVEL SECURITY;
ALTER TABLE roads DISABLE ROW LEVEL SECURITY;
ALTER TABLE city_counties DISABLE ROW LEVEL SECURITY;

-- Or if you want to keep RLS enabled, add insert policies
-- CREATE POLICY "Enable insert for all users" ON states FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable insert for all users" ON counties FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable insert for all users" ON cities FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable insert for all users" ON roads FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Enable insert for all users" ON city_counties FOR INSERT WITH CHECK (true);