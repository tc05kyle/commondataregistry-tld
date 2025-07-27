"""Production Configuration Management Page"""
import streamlit as st
import os
from config.production_config import prod_config
from services.linode_storage import linode_storage
from services.linode_database import linode_db
from utils.static_files import inject_custom_css, display_logo

# Inject custom CSS
inject_custom_css()

# Display logo
display_logo()

st.title("🏭 Production Configuration")
st.markdown("---")

# Check authentication
if not st.session_state.get("authenticated", False):
    st.error("Please login to access this page")
    st.stop()

# Only allow admins to access this page
if st.session_state.get("admin_type") not in ["Individual Admin", "Organization Admin"]:
    st.error("Access denied. Admin privileges required.")
    st.stop()

def main():
    """Main production configuration page"""
    
    # Display current production status
    prod_config.display_production_status()
    
    st.markdown("---")
    
    # Configuration Actions
    st.markdown("### 🔧 Configuration Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Service Status", help="Check all services and update status"):
            prod_config._check_services()
            st.success("Service status refreshed")
            st.rerun()
        
        if st.button("🚀 Setup Production Deployment", help="Initialize all production services"):
            with st.spinner("Setting up production deployment..."):
                results = prod_config.setup_production_deployment()
                
                st.markdown("#### Setup Results:")
                for service, success in results.items():
                    if success:
                        st.success(f"✅ {service.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ {service.replace('_', ' ').title()}")
    
    with col2:
        if st.button("📊 View Storage Stats", help="View Linode Object Storage statistics"):
            if prod_config.config['linode_storage']['enabled']:
                stats = linode_storage.get_storage_stats()
                if 'error' not in stats:
                    st.json(stats)
                else:
                    st.error(f"Storage stats error: {stats['error']}")
            else:
                st.warning("Linode Object Storage not configured")
        
        if st.button("🗄️ View Database Stats", help="View Linode Database statistics"):
            if prod_config.config['linode_database']['enabled']:
                stats = linode_db.get_database_stats()
                if 'error' not in stats:
                    st.json(stats)
                else:
                    st.error(f"Database stats error: {stats['error']}")
            else:
                st.warning("Linode Database not configured")
    
    st.markdown("---")
    
    # Secret Configuration Status
    st.markdown("### 🔐 Secret Configuration")
    
    missing_secrets = prod_config.get_missing_secrets()
    
    if missing_secrets:
        st.error(f"Missing {len(missing_secrets)} required secrets")
        
        with st.expander("Missing Secrets Details", expanded=True):
            for secret in missing_secrets:
                st.markdown(f"- `{secret}`")
        
        st.info("Please configure these environment variables in the Replit Secrets tab.")
        
        if st.button("📋 Show Configuration Guide"):
            with open("config/secrets_guide.md", "r") as f:
                guide_content = f.read()
            st.markdown(guide_content)
    else:
        st.success("✅ All required secrets are configured")
    
    st.markdown("---")
    
    # Service Details
    st.markdown("### 📋 Service Details")
    
    tab1, tab2, tab3 = st.tabs(["Linode Storage", "Linode Database", "SendGrid Email"])
    
    with tab1:
        st.markdown("#### Linode Object Storage Configuration")
        storage_config = prod_config.config['linode_storage']
        
        if storage_config['enabled']:
            st.success("✅ Enabled")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Bucket:** {storage_config['bucket_name']}")
                st.info(f"**Region:** {storage_config['region']}")
            with col2:
                st.info(f"**Access Key:** {storage_config['access_key'][:8]}..." if storage_config['access_key'] else "Not set")
                st.info(f"**Secret Key:** {'Set' if storage_config['secret_key'] else 'Not set'}")
            
            # File upload test
            uploaded_file = st.file_uploader("Test File Upload", type=['png', 'jpg', 'pdf', 'txt'])
            if uploaded_file and st.button("Upload Test File"):
                with st.spinner("Uploading..."):
                    # Save uploaded file temporarily
                    temp_path = f"/tmp/{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Upload to Linode
                    url = linode_storage.upload_file(temp_path, f"test/{uploaded_file.name}", public=True)
                    if url:
                        st.success(f"File uploaded successfully: {url}")
                    else:
                        st.error("Upload failed")
                    
                    # Clean up
                    import os
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        else:
            st.warning("⚠️ Not configured")
            st.info("Configure LINODE_BUCKET_NAME, LINODE_ACCESS_KEY, and LINODE_SECRET_KEY")
    
    with tab2:
        st.markdown("#### Linode Database Configuration")
        db_config = prod_config.config['linode_database']
        
        if db_config['enabled']:
            st.success("✅ Enabled")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Host:** {db_config['host']}")
                st.info(f"**Database:** {db_config['database']}")
            with col2:
                st.info(f"**User:** {db_config['user']}")
                st.info(f"**SSL Mode:** {db_config['ssl_mode']}")
            
            # Database operations
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Initialize Schema"):
                    with st.spinner("Initializing database schema..."):
                        success = linode_db.initialize_schema()
                        if success:
                            st.success("Schema initialized successfully")
                        else:
                            st.error("Schema initialization failed")
            
            with col2:
                if st.button("Backup Data"):
                    with st.spinner("Creating backup..."):
                        backup = linode_db.backup_data()
                        if 'error' not in backup:
                            st.success("Backup created successfully")
                            st.download_button(
                                "Download Backup",
                                data=str(backup),
                                file_name=f"backup_{backup.get('backup_timestamp', 'unknown')}.json",
                                mime="application/json"
                            )
                        else:
                            st.error(f"Backup failed: {backup['error']}")
        else:
            st.warning("⚠️ Not configured")
            st.info("Configure LINODE_DB_HOST, LINODE_DB_USER, and LINODE_DB_PASSWORD")
    
    with tab3:
        st.markdown("#### SendGrid Email Configuration")
        email_config = prod_config.config['sendgrid']
        
        if email_config['enabled']:
            st.success("✅ Enabled")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**From Email:** {email_config['from_email']}")
                st.info(f"**From Name:** {email_config['from_name']}")
            with col2:
                st.info(f"**API Key:** {email_config['api_key'][:8]}..." if email_config['api_key'] else "Not set")
                st.info(f"**Templates:** {'Configured' if email_config['template_approval'] else 'Not configured'}")
            
            # Test email
            st.markdown("##### Test Email")
            test_email = st.text_input("Test Email Address")
            if test_email and st.button("Send Test Email"):
                from services.email_service import EmailService
                email_service = EmailService()
                
                success = email_service.send_email(
                    test_email,
                    "Data Registry Platform - Test Email",
                    html_content="""
                    <h2>Test Email</h2>
                    <p>This is a test email from the Data Registry Platform.</p>
                    <p>If you received this email, the SendGrid configuration is working correctly.</p>
                    """
                )
                
                if success:
                    st.success("Test email sent successfully")
                else:
                    st.error("Test email failed")
        else:
            st.warning("⚠️ Not configured")
            st.info("Configure SENDGRID_API_KEY")

if __name__ == "__main__":
    main()