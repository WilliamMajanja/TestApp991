#!/usr/bin/env python3
"""
Simple Supabase Database Setup Script for PowerSync Integration
Uses Supabase client to create tables and configure for PowerSync
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def setup_database():
    """Set up the database schema using Supabase client"""
    
    print("🚀 Setting up Supabase database for PowerSync integration...")
    
    if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
        print("❌ Missing environment variables. Check your .env file.")
        return False
    
    try:
        # Create Supabase client with service role key
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        print("✅ Connected to Supabase")
        
        # Test connection first
        result = supabase.table("_test").select("*").limit(1).execute()
        print("✅ Supabase client connection test successful")
        
        # Note: We can't create tables directly through the Supabase client
        # The user needs to run SQL commands in their Supabase SQL editor
        
        print("\n📝 DATABASE SETUP INSTRUCTIONS")
        print("=" * 50)
        print("\nPlease execute the following SQL commands in your Supabase SQL Editor:")
        print("(Go to your Supabase dashboard → SQL Editor → New query)")
        print("\n-- 1. CREATE TABLES")
        print("""
CREATE TABLE IF NOT EXISTS lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""")
        
        print("\n-- 2. INSERT SAMPLE DATA")
        print("""
INSERT INTO lists (name) VALUES 
('My First List'),
('Work Tasks'),
('Personal Goals');

INSERT INTO todos (list_id, description, completed) 
SELECT 
    (SELECT id FROM lists LIMIT 1),
    description,
    false
FROM (VALUES 
    ('Set up PowerSync integration'),
    ('Test offline synchronization'),
    ('Build React UI')
) AS t(description);
""")
        
        print("\n-- 3. ENABLE ROW LEVEL SECURITY (RLS)")
        print("""
ALTER TABLE lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public access (for demo purposes)
DROP POLICY IF EXISTS lists_policy ON lists;
CREATE POLICY lists_policy ON lists FOR ALL USING (true);

DROP POLICY IF EXISTS todos_policy ON todos;
CREATE POLICY todos_policy ON todos FOR ALL USING (true);
""")
        
        print("\n-- 4. CREATE POWERSYNC REPLICATION USER AND PUBLICATION")
        print("-- (This requires database admin privileges - contact your Supabase project owner)")
        print("""
-- Create PowerSync role (requires superuser privileges)
-- Note: You may need to contact Supabase support for this step
CREATE ROLE powersync_role WITH REPLICATION BYPASSRLS LOGIN PASSWORD 'powersync_secure_123';
GRANT USAGE ON SCHEMA public TO powersync_role;
GRANT SELECT ON lists, todos TO powersync_role;

-- Create publication for PowerSync
CREATE PUBLICATION powersync FOR TABLE lists, todos;
""")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Copy and paste the SQL commands above into your Supabase SQL Editor")
        print("2. Execute each section one by one")
        print("3. Once tables are created, test the API endpoints")
        print("4. Set up PowerSync Cloud instance with these connection details:")
        print(f"   - Database URL: Extract from your Supabase settings")
        print(f"   - Tables: lists, todos")
        print(f"   - Publication: powersync")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return False

def test_supabase_client():
    """Test Supabase client connection and check for tables"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Test by fetching lists
        result = supabase.table("lists").select("*").limit(1).execute()
        print(f"✅ Found {len(result.data)} lists in database")
        
        # Test todos table
        todos_result = supabase.table("todos").select("*").limit(1).execute()
        print(f"✅ Found {len(todos_result.data)} todos in database")
        
        return True
        
    except Exception as e:
        print(f"❌ Database tables not ready: {e}")
        print("Please run the SQL commands in your Supabase dashboard first.")
        return False

if __name__ == "__main__":
    print("PowerSync + Supabase Setup Script")
    print("=================================")
    
    # Show setup instructions
    setup_database()
    
    # Test connection
    print("\n🧪 Testing Supabase client connection...")
    test_supabase_client()