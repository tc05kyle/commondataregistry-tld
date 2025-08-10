"""Admin Dashboard - System Overview and Status"""
import streamlit as st
import psycopg2
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from database.connection import get_db_connection
from utils.static_files import inject_custom_css
from utils.navigation import inject_navigation_components, create_page_header, close_page_with_footer, render_contextual_sidebar
from services.email_service import EmailService
import os

# Page configuration
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide"
)

inject_custom_css()
footer_html = inject_navigation_components()

def check_admin_access():
    """Check if user has admin access"""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.error("Please login as an admin to access this dashboard")
        st.stop()
    
    if st.session_state.admin_type not in ["Individual Admin", "Organization Admin"]:
        st.error("Admin access required")
        st.stop()

def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total registrations
        cursor.execute("SELECT COUNT(*) FROM individuals")
        stats['total_individuals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations")
        stats['total_organizations'] = cursor.fetchone()[0]
        
        # Pending registrations
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE status = 'pending'")
        stats['pending_individuals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations WHERE status = 'pending'")
        stats['pending_organizations'] = cursor.fetchone()[0]
        
        # Approved registrations
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE status = 'approved'")
        stats['approved_individuals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations WHERE status = 'approved'")
        stats['approved_organizations'] = cursor.fetchone()[0]
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute("SELECT COUNT(*) FROM individuals WHERE created_at >= %s", (thirty_days_ago,))
        stats['recent_individuals'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations WHERE created_at >= %s", (thirty_days_ago,))
        stats['recent_organizations'] = cursor.fetchone()[0]
        
        # Active API keys
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE is_active = true")
        stats['active_api_keys'] = cursor.fetchone()[0]
        
        # Admin users
        cursor.execute("SELECT COUNT(*) FROM admins WHERE is_active = true")
        stats['active_admins'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        st.error(f"Error fetching system statistics: {e}")
        return {}

def get_registration_trends():
    """Get registration trends over time"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get daily registrations for the last 30 days
        query = """
        SELECT 
            DATE(created_at) as date,
            'individuals' as type,
            COUNT(*) as count
        FROM individuals 
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        UNION ALL
        SELECT 
            DATE(created_at) as date,
            'organizations' as type,
            COUNT(*) as count
        FROM organizations 
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute(query, (thirty_days_ago, thirty_days_ago))
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return data
        
    except Exception as e:
        st.error(f"Error fetching registration trends: {e}")
        return []

def get_status_distribution():
    """Get distribution of registration statuses"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Individual status distribution
        cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM individuals 
        GROUP BY status
        """)
        individual_status = cursor.fetchall()
        
        # Organization status distribution
        cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM organizations 
        GROUP BY status
        """)
        org_status = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return individual_status, org_status
        
    except Exception as e:
        st.error(f"Error fetching status distribution: {e}")
        return [], []

def check_system_health():
    """Check various system health indicators"""
    health_status = {
        'database': True,
        'email_service': True,
        'api_service': True,
        'storage': True
    }
    
    health_messages = {}
    
    # Database check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        health_messages['database'] = "Database connection successful"
    except Exception as e:
        health_status['database'] = False
        health_messages['database'] = f"Database error: {str(e)[:50]}..."
    
    # Email service check
    try:
        email_service = EmailService()
        if os.getenv('SENDGRID_API_KEY'):
            health_messages['email_service'] = "SendGrid API key configured"
        else:
            health_status['email_service'] = False
            health_messages['email_service'] = "SendGrid API key not configured"
    except Exception as e:
        health_status['email_service'] = False
        health_messages['email_service'] = f"Email service error: {str(e)[:50]}..."
    
    # API service check
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM api_keys")
        api_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        health_messages['api_service'] = f"API service operational ({api_count} keys)"
    except Exception as e:
        health_status['api_service'] = False
        health_messages['api_service'] = f"API service error: {str(e)[:50]}..."
    
    # Storage check (basic file system check)
    try:
        test_file = "temp_health_check.txt"
        with open(test_file, 'w') as f:
            f.write("health check")
        os.remove(test_file)
        health_messages['storage'] = "File system accessible"
    except Exception as e:
        health_status['storage'] = False
        health_messages['storage'] = f"Storage error: {str(e)[:50]}..."
    
    return health_status, health_messages

def main():
    check_admin_access()
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>📊 Admin Dashboard</h1>
        <p>System Overview and Health Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load custom CSS for dashboard
    st.markdown("""
    <style>
    .metric-container {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .health-good {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .health-bad {
        background: linear-gradient(135deg, #dc3545, #e83e8c);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .dashboard-section {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # System Health Status
    st.markdown("## 🏥 System Health")
    health_status, health_messages = check_system_health()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_class = "health-good" if health_status['database'] else "health-bad"
        st.markdown(f"""
        <div class="{status_class}">
            <h4>🗄️ Database</h4>
            <p>{health_messages['database']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status_class = "health-good" if health_status['email_service'] else "health-bad"
        st.markdown(f"""
        <div class="{status_class}">
            <h4>📧 Email Service</h4>
            <p>{health_messages['email_service']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        status_class = "health-good" if health_status['api_service'] else "health-bad"
        st.markdown(f"""
        <div class="{status_class}">
            <h4>🔌 API Service</h4>
            <p>{health_messages['api_service']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status_class = "health-good" if health_status['storage'] else "health-bad"
        st.markdown(f"""
        <div class="{status_class}">
            <h4>💾 Storage</h4>
            <p>{health_messages['storage']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key Metrics
    st.markdown("## 📈 Key Metrics")
    stats = get_system_stats()
    
    if stats:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{stats.get('total_individuals', 0)}</div>
                <div class="metric-label">Total Individuals</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{stats.get('total_organizations', 0)}</div>
                <div class="metric-label">Total Organizations</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_pending = stats.get('pending_individuals', 0) + stats.get('pending_organizations', 0)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{total_pending}</div>
                <div class="metric-label">Pending Requests</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_approved = stats.get('approved_individuals', 0) + stats.get('approved_organizations', 0)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{total_approved}</div>
                <div class="metric-label">Approved</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{stats.get('active_api_keys', 0)}</div>
                <div class="metric-label">Active API Keys</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-number">{stats.get('active_admins', 0)}</div>
                <div class="metric-label">Active Admins</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Charts and Analytics
    st.markdown("## 📊 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Registration trends
        st.markdown("### Registration Trends (Last 30 Days)")
        trend_data = get_registration_trends()
        
        if trend_data:
            df = pd.DataFrame(trend_data, columns=['date', 'type', 'count'])
            
            fig = px.line(df, x='date', y='count', color='type',
                         title="Daily Registrations",
                         color_discrete_map={
                             'individuals': '#667eea',
                             'organizations': '#f093fb'
                         })
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#2d3748'),
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No registration data available for the last 30 days")
    
    with col2:
        # Status distribution
        st.markdown("### Status Distribution")
        individual_status, org_status = get_status_distribution()
        
        if individual_status or org_status:
            # Combine data for pie chart
            all_status = {}
            for status, count in individual_status:
                all_status[f"Individual {status}"] = count
            for status, count in org_status:
                all_status[f"Organization {status}"] = count
            
            if all_status:
                labels = list(all_status.keys())
                values = list(all_status.values())
                
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    marker=dict(colors=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'])
                )
                fig.update_layout(
                    title="Registration Status Breakdown",
                    font=dict(color='#2d3748'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=16
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available")
    
    # Recent Activity
    st.markdown("## 🕒 Recent Activity")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent registrations
        cursor.execute("""
        SELECT 
            'Individual' as type,
            canonical_id,
            first_name || ' ' || last_name as name,
            email,
            status,
            created_at
        FROM individuals 
        WHERE created_at >= %s
        UNION ALL
        SELECT 
            'Organization' as type,
            canonical_id,
            organization_name as name,
            primary_contact_email as email,
            status,
            created_at
        FROM organizations 
        WHERE created_at >= %s
        ORDER BY created_at DESC
        LIMIT 10
        """, (datetime.now() - timedelta(days=7), datetime.now() - timedelta(days=7)))
        
        recent_activity = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if recent_activity:
            df = pd.DataFrame(recent_activity, columns=[
                'Type', 'Canonical ID', 'Name', 'Email', 'Status', 'Created'
            ])
            
            # Style the dataframe
            def color_status(val):
                if val == 'approved':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'pending':
                    return 'background-color: #fff3cd; color: #856404'
                elif val == 'rejected':
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            styled_df = df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No recent activity in the last 7 days")
    
    except Exception as e:
        st.error(f"Error fetching recent activity: {e}")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 View Pending Requests", use_container_width=True):
            if st.session_state.admin_type == "Individual Admin":
                st.switch_page("pages/1_Individual_Admin.py")
            else:
                st.switch_page("pages/2_Organization_Admin.py")
    
    with col2:
        if st.button("📝 Registration Form", use_container_width=True):
            st.switch_page("pages/3_Registration_Request.py")
    
    with col3:
        if st.button("🔌 API Management", use_container_width=True):
            st.switch_page("pages/4_API_Testing.py")
    
    with col4:
        if st.button("🔍 Registry Search", use_container_width=True):
            st.switch_page("pages/5_Registry_Lookup.py")
    
    # System Information
    st.markdown("## ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Environment:**
        - Platform: Streamlit Cloud
        - Database: PostgreSQL
        - Email: SendGrid
        - Storage: Linode Object Storage
        """)
    
    with col2:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"""
        **Current Status:**
        - Last Updated: {current_time}
        - Admin User: {st.session_state.get('admin_username', 'Unknown')}
        - Admin Type: {st.session_state.get('admin_type', 'Unknown')}
        - Session Active: ✅
        """)

def main():
    """Main admin dashboard function"""
    check_admin_access()
    
    # Render contextual sidebar for admin dashboard
    render_contextual_sidebar('admin')
    
    display_admin_dashboard()
    
    # Add footer at the end
    close_page_with_footer(footer_html)

if __name__ == "__main__":
    main()