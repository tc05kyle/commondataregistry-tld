"""Production database setup for Replit deployment"""
import os
import psycopg2
import streamlit as st
from database.models import CREATE_TABLES_SQL
from utils.security import hash_password

def setup_production_database():
    """Set up production database with proper error handling and persistence"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get database URL from environment
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                st.error("DATABASE_URL environment variable not found")
                return False
            
            # Connect to database
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Check if tables exist
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'admins'
                """)
                
                if cursor.fetchone()[0] == 0:
                    # Create tables
                    cursor.execute(CREATE_TABLES_SQL)
                    st.info("Database tables created successfully")
                    
                    # Insert default admin users
                    individual_admin_hash = hash_password("admin123")
                    organization_admin_hash = hash_password("admin123")
                    
                    cursor.execute("""
                        INSERT INTO admins (username, password_hash, admin_type, email, is_active) 
                        VALUES 
                            (%s, %s, 'Individual Admin', 'individual.admin@dataregistry.com', TRUE),
                            (%s, %s, 'Organization Admin', 'organization.admin@dataregistry.com', TRUE)
                        ON CONFLICT (username) DO NOTHING
                    """, ('individual_admin', individual_admin_hash, 'organization_admin', organization_admin_hash))
                    
                    st.success("Default admin users created")
                else:
                    st.info("Database tables already exist")
                
                # Verify the setup
                cursor.execute("SELECT COUNT(*) FROM admins")
                admin_count = cursor.fetchone()[0]
                st.info(f"Database setup complete. Admin users: {admin_count}")
                
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            retry_count += 1
            if "endpoint has been disabled" in str(e).lower():
                st.warning(f"Database endpoint disabled. Attempt {retry_count}/{max_retries}")
                if retry_count < max_retries:
                    st.info("Attempting to create new database connection...")
                    # Try to create a new database
                    try:
                        from replit import Database
                        db = Database()
                        st.info("Using Replit Database as fallback")
                        return setup_replit_database()
                    except ImportError:
                        continue
                else:
                    st.error("Maximum retries reached. Database setup failed.")
                    return False
            else:
                st.error(f"Database connection error: {e}")
                return False
        except Exception as e:
            st.error(f"Unexpected error during database setup: {e}")
            return False
    
    return False

def setup_replit_database():
    """Setup using Replit's built-in database as fallback"""
    try:
        from replit import Database
        db = Database()
        
        # Initialize admin users in Replit DB
        individual_admin_hash = hash_password("admin123")
        organization_admin_hash = hash_password("admin123")
        
        db["admin_individual_admin"] = {
            "username": "individual_admin",
            "password_hash": individual_admin_hash,
            "admin_type": "Individual Admin",
            "email": "individual.admin@dataregistry.com",
            "is_active": True
        }
        
        db["admin_organization_admin"] = {
            "username": "organization_admin", 
            "password_hash": organization_admin_hash,
            "admin_type": "Organization Admin",
            "email": "organization.admin@dataregistry.com",
            "is_active": True
        }
        
        # Initialize counters
        db["individual_counter"] = 0
        db["organization_counter"] = 0
        db["request_counter"] = 0
        
        st.success("Replit Database initialized successfully")
        return True
        
    except ImportError:
        st.error("Replit Database not available")
        return False
    except Exception as e:
        st.error(f"Replit Database setup error: {e}")
        return False

def get_database_status():
    """Check database status and return connection info"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url, connect_timeout=5)
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
            conn.close()
            return {
                "status": "connected",
                "type": "PostgreSQL",
                "version": version[:50] + "..." if len(version) > 50 else version
            }
    except Exception as e:
        try:
            from replit import Database
            db = Database()
            return {
                "status": "connected",
                "type": "Replit Database",
                "version": "Built-in Key-Value Store"
            }
        except ImportError:
            return {
                "status": "disconnected",
                "type": "None",
                "error": str(e)
            }

def migrate_to_replit_db():
    """Migrate existing data to Replit Database if PostgreSQL fails"""
    try:
        from replit import Database
        from database.fallback_storage import fallback_storage
        
        db = Database()
        
        # Migrate admin data
        for username, admin_data in fallback_storage.admins.items():
            db[f"admin_{username}"] = admin_data
        
        # Migrate individual data
        for req_id, individual_data in fallback_storage.individuals.items():
            db[f"individual_{req_id}"] = individual_data
        
        # Migrate organization data
        for req_id, organization_data in fallback_storage.organizations.items():
            db[f"organization_{req_id}"] = organization_data
        
        st.success("Data migrated to Replit Database successfully")
        return True
        
    except Exception as e:
        st.error(f"Migration failed: {e}")
        return False