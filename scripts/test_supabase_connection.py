#!/usr/bin/env python3
"""
Test Supabase connection and basic queries
"""

from supabase import create_client, Client

# Your Supabase credentials
SUPABASE_URL = "https://zutlqkirprynkzfddnlt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1dGxxa2lycHJ5bmt6ZmRkbmx0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMjIxNjksImV4cCI6MjA2NDY5ODE2OX0.KDznN7sp_1enMlocM3dFnLEthzCEOzlG9WWO8uKTMi4"

def test_connection():
    """Test basic connection to Supabase"""
    try:
        # Create client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Successfully connected to Supabase")
        
        # Test query (will fail if tables don't exist yet)
        try:
            result = supabase.table('states').select("*").limit(1).execute()
            print("✓ Tables exist and are accessible")
        except:
            print("! Tables not created yet - run the SQL schema first")
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def sample_queries():
    """Show sample queries after data is imported"""
    print("\n=== Sample Queries ===")
    print("""
1. Search roads by name:
   SELECT * FROM search_roads('Broadway', 10);

2. Get all roads in a city:
   SELECT * FROM city_roads 
   WHERE city_name = 'New York' 
   LIMIT 100;

3. Get road statistics by state:
   SELECT * FROM road_statistics 
   ORDER BY total_roads DESC;

4. Find roads with fuzzy matching:
   SELECT linearid, fullname, similarity(fullname, 'Brodway') as sim
   FROM roads
   WHERE fullname % 'Brodway'
   ORDER BY sim DESC
   LIMIT 10;
""")

if __name__ == "__main__":
    print("Testing Supabase connection...")
    if test_connection():
        sample_queries()
        print("\nNext steps:")
        print("1. Go to Supabase dashboard > SQL Editor")
        print("2. Copy and run the content of 'supabase_schema.sql'")
        print("3. Install supabase Python client: pip install supabase")
        print("4. Run: python import_to_supabase.py")