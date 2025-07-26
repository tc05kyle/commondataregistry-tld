"""Database connection and initialization"""
import psycopg2
import os
import streamlit as st
from database.models import CREATE_TABLES_SQL, INSERT_DEFAULT_ADMINS_SQL
from database.fallback_storage import fallback_storage
from utils.security import hash_password

def get_db_connection():
    """Get database connection using environment variables with fallback"""
    try:
        # Try using DATABASE_URL first (for services like Heroku)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            conn = psycopg2.connect(database_url)
            # Test the connection
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
            return conn
    except Exception as e:
        st.warning(f"DATABASE_URL connection failed: {e}")
        
    try:
        # Fall back to individual environment variables
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            database=os.getenv('PGDATABASE', 'dataregistry'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', 'password'),
            port=os.getenv('PGPORT', '5432')
        )
        # Test the connection
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        return conn
    except Exception as e:
        st.error(f"Database connection failed with both methods: {e}")
        st.info("The database may need to be re-enabled. Please contact support if this issue persists.")
        raise

def init_database():
    """Initialize database tables and default data, with fallback to in-memory storage"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute(CREATE_TABLES_SQL)
        
        # Insert default admin users with proper password hashing
        # Hash default passwords
        individual_admin_hash = hash_password("admin123")
        organization_admin_hash = hash_password("admin123")
        
        # Insert default admins with hashed passwords
        cursor.execute("""
            INSERT INTO admins (username, password_hash, admin_type, email) 
            VALUES 
                (%s, %s, 'Individual Admin', 'individual.admin@dataregistry.com'),
                (%s, %s, 'Organization Admin', 'organization.admin@dataregistry.com')
            ON CONFLICT (username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                email = EXCLUDED.email
        """, ('individual_admin', individual_admin_hash, 'organization_admin', organization_admin_hash))
        
        conn.commit()
        st.session_state.use_fallback_storage = False
        
    except Exception as e:
        # Initialize fallback storage instead
        fallback_storage.initialize()
        st.session_state.use_fallback_storage = True
        st.error(f"Database initialization error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def execute_query(query, params=None, fetch=False):
    """Execute a database query with error handling"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        st.error(f"Database query error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_pending_registrations(entity_type):
    """Get pending registrations for a specific entity type"""
    table_name = entity_type.lower() + 's'
    query = f"""
        SELECT * FROM {table_name} 
        WHERE status = 'pending' 
        ORDER BY request_date ASC
    """
    return execute_query(query, fetch=True)

def approve_registration(entity_type, entity_id, admin_id):
    """Approve a registration"""
    table_name = entity_type.lower() + 's'
    query = f"""
        UPDATE {table_name} 
        SET status = 'approved', 
            approved_date = CURRENT_TIMESTAMP,
            approved_by = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE {entity_type.lower()}_id = %s
    """
    return execute_query(query, (admin_id, entity_id))

def reject_registration(entity_type, entity_id, admin_id, reason):
    """Reject a registration with reason"""
    table_name = entity_type.lower() + 's'
    query = f"""
        UPDATE {table_name} 
        SET status = 'rejected', 
            rejection_reason = %s,
            approved_by = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE {entity_type.lower()}_id = %s
    """
    return execute_query(query, (reason, admin_id, entity_id))

def log_audit_action(entity_type, entity_id, action, admin_id, details=None):
    """Log an audit action"""
    query = """
        INSERT INTO audit_log (entity_type, entity_id, action, admin_id, details)
        VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(query, (entity_type, entity_id, action, admin_id, details))
