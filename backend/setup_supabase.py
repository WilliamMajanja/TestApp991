#!/usr/bin/env python3
"""
Supabase Database Setup Script for PowerSync Integration
Creates tables, publications, and replication user for PowerSync
"""

import os
import psycopg2
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Supabase connection details
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Extract database connection info from Supabase URL
# Format: https://wdggeorpruibbnzmwgud.supabase.co
project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
DB_HOST = f"db.{project_ref}.supabase.co"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"

def setup_database():
    """Set up the database schema and PowerSync configuration"""
    
    print("🚀 Setting up Supabase database for PowerSync integration...")
    
    # First, get the database password
    print("\n⚠️  You need to provide your Supabase database password.")
    print("You can find this in your Supabase project settings under Database > Connection string")
    print("It's the password for the 'postgres' user.")
    
    db_password = input("Enter your Supabase postgres password: ").strip()
    
    if not db_password:
        print("❌ Password is required!")
        return False
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to Supabase database")
        
        # Create tables
        print("📝 Creating database schema...")
        
        # Create lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create todos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                list_id UUID REFERENCES lists(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        print("✅ Tables created successfully")
        
        # Create PowerSync role and user
        print("🔐 Setting up PowerSync replication user...")
        
        powersync_password = "powersync_secure_123"  # You can change this
        
        # Create role if it doesn't exist
        cursor.execute(f"""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'powersync_role') THEN
                    CREATE ROLE powersync_role WITH REPLICATION BYPASSRLS LOGIN PASSWORD '{powersync_password}';
                END IF;
            END
            $$;
        """)
        
        # Grant permissions
        cursor.execute("GRANT USAGE ON SCHEMA public TO powersync_role;")
        cursor.execute("GRANT SELECT ON lists, todos TO powersync_role;")
        
        print("✅ PowerSync user created with permissions")
        
        # Create publication
        print("📡 Setting up replication publication...")
        
        # Drop publication if exists, then create new one
        cursor.execute("DROP PUBLICATION IF EXISTS powersync;")
        cursor.execute("CREATE PUBLICATION powersync FOR TABLE lists, todos;")
        
        print("✅ Publication 'powersync' created")
        
        # Insert sample data
        print("📊 Inserting sample data...")
        
        cursor.execute("""
            INSERT INTO lists (name) VALUES 
            ('My First List'),
            ('Work Tasks'),
            ('Personal Goals')
            ON CONFLICT (id) DO NOTHING;
        """)
        
        # Get the first list ID for sample todos
        cursor.execute("SELECT id FROM lists LIMIT 1;")
        list_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO todos (list_id, description, completed) VALUES 
            (%s, 'Set up PowerSync integration', false),
            (%s, 'Test offline synchronization', false),
            (%s, 'Build React UI', false)
            ON CONFLICT (id) DO NOTHING;
        """, (list_id, list_id, list_id))
        
        print("✅ Sample data inserted")
        
        # Enable Row Level Security (RLS) - Optional for this demo
        cursor.execute("ALTER TABLE lists ENABLE ROW LEVEL SECURITY;")
        cursor.execute("ALTER TABLE todos ENABLE ROW LEVEL SECURITY;")
        
        # Create policies to allow public access for demo
        cursor.execute("DROP POLICY IF EXISTS lists_policy ON lists;")
        cursor.execute("CREATE POLICY lists_policy ON lists FOR ALL USING (true);")
        
        cursor.execute("DROP POLICY IF EXISTS todos_policy ON todos;")
        cursor.execute("CREATE POLICY todos_policy ON todos FOR ALL USING (true);")
        
        print("✅ Row Level Security configured")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Summary:")
        print(f"   • Tables created: lists, todos")
        print(f"   • PowerSync user: powersync_role")
        print(f"   • PowerSync password: {powersync_password}")
        print(f"   • Publication: powersync")
        print(f"   • Database connection string for PowerSync:")
        print(f"     postgresql://powersync_role:{powersync_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_supabase_client():
    """Test Supabase client connection"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        # Test by fetching lists
        result = supabase.table("lists").select("*").limit(1).execute()
        print(f"✅ Supabase client test successful. Found {len(result.data)} lists.")
        return True
        
    except Exception as e:
        print(f"❌ Supabase client test failed: {e}")
        return False

if __name__ == "__main__":
    print("PowerSync + Supabase Setup Script")
    print("=================================")
    
    if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY]):
        print("❌ Missing environment variables. Check your .env file.")
        exit(1)
    
    # Setup database
    if setup_database():
        print("\n🧪 Testing Supabase client connection...")
        test_supabase_client()
        print("\n✅ Setup complete! You can now configure PowerSync.")
    else:
        print("❌ Setup failed. Please check the errors above.")
        exit(1)