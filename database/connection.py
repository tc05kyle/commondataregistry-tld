"""Database connection and initialization"""
import psycopg2
import os
import streamlit as st
from database.models import CREATE_TABLES_SQL, INSERT_DEFAULT_ADMINS_SQL
from database.fallback_storage import fallback_storage
from database.robust_connection import db_manager
from utils.security import hash_password

def get_db_connection():
    """Get database connection using robust connection manager"""
    return db_manager.get_connection()

def init_database():
    """Initialize database tables and default data, with fallback to in-memory storage"""
    try:
        # Use the robust database manager
        individual_admin_hash = hash_password("admin123")
        organization_admin_hash = hash_password("admin123")
        
        # Create tables
        db_manager.execute_query(CREATE_TABLES_SQL)
        
        # Insert default admins with hashed passwords
        db_manager.execute_query("""
            INSERT INTO admins (username, password_hash, admin_type, email, is_active) 
            VALUES 
                (%s, %s, 'Individual Admin', 'individual.admin@dataregistry.com', TRUE),
                (%s, %s, 'Organization Admin', 'organization.admin@dataregistry.com', TRUE)
            ON CONFLICT (username) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                email = EXCLUDED.email
        """, ('individual_admin', individual_admin_hash, 'organization_admin', organization_admin_hash))
        
        st.session_state.use_fallback_storage = False
        st.success("Database initialized successfully")
        
    except Exception as e:
        # Initialize fallback storage instead
        fallback_storage.initialize()
        st.session_state.use_fallback_storage = True
        st.warning("Database connection failed. Using in-memory storage mode.")
        st.info("Data will not persist between sessions in this mode.")

def execute_query(query, params=None, fetch=False):
    """Execute a database query with error handling"""
    try:
        return db_manager.execute_query(query, params, fetch)
    except Exception as e:
        st.error(f"Database query error: {e}")
        raise

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
