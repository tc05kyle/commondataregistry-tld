import streamlit as st
import sys
import os
from database.connection import init_database, get_db_connection
from services.email_service import EmailService
from utils.security import hash_password, verify_password
from utils.static_files import inject_custom_css, display_logo
from utils.db_status import display_db_status
import hashlib

# Initialize database on startup
if 'database_initialized' not in st.session_state:
    try:
        init_database()
        st.session_state.database_connected = True
        st.session_state.database_initialized = True
    except Exception as e:
        st.session_state.database_connected = False
        st.session_state.database_initialized = True
        # Initialize fallback storage
        from database.fallback_storage import fallback_storage
        fallback_storage.initialize()

# Initialize email service
email_service = EmailService()

st.set_page_config(
    page_title="Data Registry Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS and setup static files
inject_custom_css()

def main():
    # Display logo and title
    display_logo()
    st.markdown("---")
    
    # Authentication check
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.admin_type = None
    
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

def login_page():
    st.subheader("Admin Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            admin_type = st.selectbox(
                "Admin Type",
                ["Individual Admin", "Organization Admin"],
                key="admin_type_select"
            )
            
            username = st.text_input("Username", key="username")
            password = st.text_input("Password", type="password", key="password")
            
            if st.form_submit_button("Login"):
                if authenticate_admin(username, password, admin_type):
                    st.session_state.authenticated = True
                    st.session_state.admin_type = admin_type
                    st.session_state.admin_username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials or admin type mismatch")

def authenticate_admin(username, password, admin_type):
    """Authenticate admin users using database or fallback storage"""
    # Check if using fallback storage
    if getattr(st.session_state, 'use_fallback_storage', True) or not st.session_state.get('database_connected', False):
        from database.fallback_storage import fallback_storage
        admin = fallback_storage.get_admin(username)
        if admin and admin['admin_type'] == admin_type and admin['is_active']:
            return verify_password(password, admin['password_hash'])
        return False
    
    # Use database authentication
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT admin_id, admin_type, password_hash, is_active
            FROM admins 
            WHERE username = %s AND admin_type = %s
        """, (username, admin_type))
        
        result = cursor.fetchone()
        
        if result and result[3]:  # is_active
            stored_hash = result[2]
            if verify_password(password, stored_hash):
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def dashboard_page():
    st.sidebar.success(f"Logged in as: {st.session_state.admin_type}")
    st.sidebar.markdown(f"**User:** {st.session_state.admin_username}")
    
    # Display database status
    display_db_status()
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.admin_type = None
        st.session_state.admin_username = None
        st.rerun()
    
    st.markdown("## Welcome to the Data Registry Platform")
    st.markdown("### System Overview")
    
    # Display system statistics
    display_system_stats()
    
    st.markdown("### Navigation")
    st.markdown("Use the sidebar to navigate between different sections:")
    
    if st.session_state.admin_type == "Individual Admin":
        st.markdown("- **Individual Admin**: Manage individual registrations")
    else:
        st.markdown("- **Organization Admin**: Manage organization registrations")
    
    st.markdown("- **Registration Request**: Submit new registration requests")
    st.markdown("- **API Testing**: Test API endpoints")
    st.markdown("- **Registry Lookup**: Search and lookup registered IDs")

def display_system_stats():
    """Display system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE status = 'approved'")
        approved_individuals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations WHERE status = 'approved'")
        approved_organizations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE status = 'pending'")
        pending_individuals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations WHERE status = 'pending'")
        pending_organizations = cursor.fetchone()[0]
        
        # Display stats in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Approved Individuals", approved_individuals)
        
        with col2:
            st.metric("Approved Organizations", approved_organizations)
        
        with col3:
            st.metric("Pending Individuals", pending_individuals)
        
        with col4:
            st.metric("Pending Organizations", pending_organizations)
        
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
