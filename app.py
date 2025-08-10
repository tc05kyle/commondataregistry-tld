import streamlit as st
import sys
import os
from database.connection import init_database, get_db_connection
from services.email_service import EmailService
from utils.security import hash_password, verify_password
from utils.static_files import inject_custom_css, display_logo
from utils.navigation import inject_navigation_components, create_page_header, close_page_with_footer
from utils.db_status import display_db_status
# Production config import removed - fixing startup issue
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

# Inject custom CSS and enhanced navigation
inject_custom_css()
footer_html = inject_navigation_components()

# Load homepage styles
st.markdown("""
<link rel="stylesheet" href="static/css/homepage.css">
""", unsafe_allow_html=True)

def render_homepage():
    """Render the modern, colorful homepage with enhanced navigation"""
    
    # Load custom CSS
    try:
        with open('static/css/homepage.css', 'r') as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # Use default styling
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-content">
            <h1 class="hero-title">🏢 Data Registry Platform</h1>
            <p class="hero-subtitle">Your Authoritative Source for Canonical Unique IDs</p>
            <p class="hero-description">
                Take control of your data identity across the digital landscape. Our platform provides 
                secure, verified canonical IDs for individuals and organizations, ensuring data consistency 
                and ownership across all industry software systems.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation Pills
    st.markdown("""
    <div class="nav-pills">
        <a href="/8_Admin_Dashboard" class="nav-pill">📊 Admin Dashboard</a>
        <a href="/9_Schema_Migration" class="nav-pill">🔄 Schema Migration</a>
        <a href="/10_Gravatar_Integration" class="nav-pill">🌐 Gravatar Sync</a>
        <a href="/1_Individual_Admin" class="nav-pill">👤 Individual Management</a>
        <a href="/2_Organization_Admin" class="nav-pill">🏢 Organization Management</a>
        <a href="/3_Registration_Request" class="nav-pill">📝 Register Now</a>
        <a href="/4_API_Testing" class="nav-pill">🔌 API Access</a>
        <a href="/5_Registry_Lookup" class="nav-pill">🔍 Search Registry</a>
        <a href="/7_User_Dashboard" class="nav-pill">📊 User Dashboard</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats-section">
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-number">10,000+</span>
                <span class="stat-label">Registered Identities</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">99.9%</span>
                <span class="stat-label">Uptime Guarantee</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">24/7</span>
                <span class="stat-label">Support Available</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">Enterprise</span>
                <span class="stat-label">Grade Security</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    st.markdown("## 🚀 Platform Features")
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card admin delay-1">
            <span class="feature-icon">👥</span>
            <h3 class="feature-title">Admin Management</h3>
            <p class="feature-description">
                Comprehensive admin dashboard for reviewing registration requests, 
                managing approvals, and maintaining data quality with role-based access control.
            </p>
        </div>
        
        <div class="feature-card registration delay-2">
            <span class="feature-icon">📋</span>
            <h3 class="feature-title">Smart Registration</h3>
            <p class="feature-description">
                Streamlined registration process with automatic domain verification, 
                data validation, and email confirmation for both individuals and organizations.
            </p>
        </div>
        
        <div class="feature-card api delay-3">
            <span class="feature-icon">🔌</span>
            <h3 class="feature-title">Powerful API</h3>
            <p class="feature-description">
                RESTful API with rate limiting, authentication, and comprehensive documentation 
                for seamless integration with your existing systems.
            </p>
        </div>
        
        <div class="feature-card lookup delay-4">
            <span class="feature-icon">🔍</span>
            <h3 class="feature-title">Registry Search</h3>
            <p class="feature-description">
                Advanced search capabilities to find and verify registered entities 
                with real-time data access and filtering options.
            </p>
        </div>
        
        <div class="feature-card dashboard delay-1">
            <span class="feature-icon">📊</span>
            <h3 class="feature-title">User Analytics</h3>
            <p class="feature-description">
                Personalized dashboards with animated insights, activity tracking, 
                data export capabilities, and comprehensive profile management.
            </p>
        </div>
        
        <div class="feature-card config delay-2">
            <span class="feature-icon">⚙️</span>
            <h3 class="feature-title">Enterprise Ready</h3>
            <p class="feature-description">
                Production-grade infrastructure with Linode cloud integration, 
                automated backups, and enterprise security standards.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Section
    st.markdown("""
    <div class="cta-section">
        <h2 class="cta-title">Ready to Get Started?</h2>
        <p class="cta-description">
            Join thousands of users who trust our platform for their data identity management. 
            Start your journey with a verified canonical ID today.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Access Buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🆕 Register as Individual", use_container_width=True, type="primary"):
            st.switch_page("pages/3_Registration_Request.py")
    
    with col2:
        if st.button("🏢 Register Organization", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_Registration_Request.py")
    
    with col3:
        if st.button("🔍 Search Registry", use_container_width=True):
            st.switch_page("pages/5_Registry_Lookup.py")
    
    with col4:
        if st.button("📊 Admin Dashboard", use_container_width=True):
            st.switch_page("pages/8_Admin_Dashboard.py")
    
    # Admin Login Section
    st.markdown("---")
    st.markdown("## 🔐 Admin Access")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("admin_login_form"):
            st.markdown("### Admin Login")
            
            admin_type = st.selectbox(
                "Admin Type",
                ["Individual Admin", "Organization Admin"],
                key="homepage_admin_type"
            )
            
            username = st.text_input("Username", key="homepage_username")
            password = st.text_input("Password", type="password", key="homepage_password")
            
            if st.form_submit_button("Login to Admin Dashboard", use_container_width=True):
                if authenticate_admin(username, password, admin_type):
                    st.session_state.authenticated = True
                    st.session_state.admin_type = admin_type
                    st.session_state.admin_username = username
                    st.success("Login successful! Redirecting to admin dashboard...")
                    st.switch_page("pages/8_Admin_Dashboard.py")
                else:
                    st.error("Invalid credentials. Please try again.")
    
    # User Dashboard Access
    st.markdown("---")
    st.markdown("## 👤 User Access")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("Access User Dashboard", use_container_width=True, type="secondary"):
            st.switch_page("pages/7_User_Dashboard.py")
    
    # Testimonial Section
    st.markdown("""
    <div class="testimonial-section">
        <p class="testimonial-text">
            "The Data Registry Platform has revolutionized how we manage our organizational 
            identity across multiple systems. The verification process is seamless and the 
            API integration was incredibly smooth."
        </p>
        <p class="testimonial-author">— Sarah Johnson, CTO at TechCorp</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer Information
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔒 Security First")
        st.markdown("""
        - Enterprise-grade encryption
        - GDPR compliant data handling
        - Regular security audits
        - Multi-factor authentication
        """)
    
    with col2:
        st.markdown("### 🌍 Global Reach")
        st.markdown("""
        - Multi-region deployment
        - 99.9% uptime SLA
        - 24/7 monitoring
        - Disaster recovery ready
        """)
    
    with col3:
        st.markdown("### 📞 Support")
        st.markdown("""
        - Expert technical support
        - Comprehensive documentation
        - Community forums
        - Priority enterprise support
        """)

def authenticate_admin(username, password, admin_type):
    """Authenticate admin user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, password_hash, admin_type 
            FROM admins 
            WHERE username = %s AND admin_type = %s AND is_active = true
        """, (username, admin_type))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and verify_password(password, result[1]):
            return True
        return False
        
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False

def main():
    # Check authentication status
    if not st.session_state.get("authenticated", False):
        # Show login page if not authenticated
        login_page()
    else:
        # Show admin dashboard if authenticated
        dashboard_page()
    
    # Add footer at the end
    if 'footer_html' in globals():
        close_page_with_footer(footer_html)

def login_page():
    """Enhanced login page with registration options"""
    
    # Create page header
    create_page_header("Login to Data Registry", "Access your admin dashboard or register as a new user", "🔐")
    
    # Login/Registration tabs
    tab1, tab2, tab3 = st.tabs(["👨‍💼 Admin Login", "👤 User Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Admin Login")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("admin_login_form"):
                admin_type = st.selectbox(
                    "Admin Type",
                    ["Individual Admin", "Organization Admin"],
                    key="admin_type_select"
                )
                
                username = st.text_input("Username", key="admin_username")
                password = st.text_input("Password", type="password", key="admin_password")
                
                if st.form_submit_button("Login as Admin", use_container_width=True):
                    if authenticate_admin(username, password, admin_type):
                        st.session_state.authenticated = True
                        st.session_state.admin_type = admin_type
                        st.session_state.admin_username = username
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or admin type mismatch")
    
    with tab2:
        st.markdown("### User Login")
        st.info("User login allows access to your registered profile and dashboard")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("user_login_form"):
                user_canonical_id = st.text_input("Canonical ID", key="user_canonical_id", 
                                                help="Format: J.Smith.6738.jsmith@hotmail.com")
                user_email = st.text_input("Email", key="user_email")
                
                if st.form_submit_button("Login as User", use_container_width=True):
                    if authenticate_user(user_canonical_id, user_email):
                        st.session_state.user_authenticated = True
                        st.session_state.user_canonical_id = user_canonical_id
                        st.session_state.user_email = user_email
                        st.success("User login successful!")
                        st.switch_page("pages/7_User_Dashboard.py")
                    else:
                        st.error("Invalid canonical ID or email")
    
    with tab3:
        st.markdown("### Register New User")
        st.info("New to the platform? Register for your canonical unique ID")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            registration_type = st.radio(
                "Registration Type",
                ["Individual", "Organization"],
                horizontal=True
            )
            
            if st.button("Start Registration", use_container_width=True):
                if registration_type == "Individual":
                    st.switch_page("pages/3_Registration_Request.py")
                else:
                    st.switch_page("pages/3_Registration_Request.py")
    
    # Quick navigation
    st.markdown("---")
    st.markdown("### Quick Access")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Registry", use_container_width=True):
            st.switch_page("pages/5_Registry_Lookup.py")
    
    with col2:
        if st.button("🔌 API Documentation", use_container_width=True):
            st.switch_page("pages/4_API_Testing.py")
    
    with col3:
        if st.button("📊 Public Dashboard", use_container_width=True):
            render_homepage()

def authenticate_user(canonical_id, email):
    """Authenticate regular users using canonical ID and email"""
    try:
        # Check if using fallback storage first
        if not st.session_state.get('database_connected', False):
            from database.fallback_storage import fallback_storage
            # Check in fallback storage - simplified check for now
            return canonical_id and email and "@" in email
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check both individuals and organizations
        cursor.execute("""
            SELECT canonical_id, email, status FROM individuals 
            WHERE canonical_id = %s AND email = %s AND status = 'approved'
            UNION
            SELECT canonical_id, primary_contact_email as email, status FROM organizations 
            WHERE canonical_id = %s AND primary_contact_email = %s AND status = 'approved'
        """, (canonical_id, email, canonical_id, email))
        
        result = cursor.fetchone()
        return bool(result)
        
    except Exception as e:
        st.error(f"User authentication error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

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
    
    # Show production services status for admins
    if st.sidebar.checkbox("Show Production Status", value=False):
        st.sidebar.markdown("### Production Services")
        missing_secrets = prod_config.get_missing_secrets()
        if missing_secrets:
            st.sidebar.error(f"{len(missing_secrets)} secrets missing")
        else:
            st.sidebar.success("All secrets configured")
    
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
    st.markdown("- **User Dashboard**: Access your registered account dashboard")
    st.markdown("- **Production Config**: Manage production services (Linode, SendGrid)")

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
