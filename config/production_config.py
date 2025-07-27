"""Production configuration management for Data Registry Platform"""
import os
import streamlit as st
from typing import Dict, Any, Optional
from services.linode_storage import linode_storage
from services.linode_database import linode_db
from services.email_service import EmailService

class ProductionConfig:
    """Manages production configuration and service integration"""
    
    def __init__(self):
        self.config = self._load_config()
        self.services_status = {}
        self._check_services()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load production configuration from environment variables"""
        return {
            # Linode Object Storage
            'linode_storage': {
                'bucket_name': os.getenv('LINODE_BUCKET_NAME'),
                'region': os.getenv('LINODE_REGION', 'us-east-1'),
                'access_key': os.getenv('LINODE_ACCESS_KEY'),
                'secret_key': os.getenv('LINODE_SECRET_KEY'),
                'enabled': all([
                    os.getenv('LINODE_BUCKET_NAME'),
                    os.getenv('LINODE_ACCESS_KEY'),
                    os.getenv('LINODE_SECRET_KEY')
                ])
            },
            
            # Linode Database
            'linode_database': {
                'host': os.getenv('LINODE_DB_HOST'),
                'port': os.getenv('LINODE_DB_PORT', '5432'),
                'database': os.getenv('LINODE_DB_NAME', 'dataregistry'),
                'user': os.getenv('LINODE_DB_USER'),
                'password': os.getenv('LINODE_DB_PASSWORD'),
                'ssl_mode': os.getenv('LINODE_DB_SSL_MODE', 'require'),
                'enabled': all([
                    os.getenv('LINODE_DB_HOST'),
                    os.getenv('LINODE_DB_USER'),
                    os.getenv('LINODE_DB_PASSWORD')
                ])
            },
            
            # SendGrid Email
            'sendgrid': {
                'api_key': os.getenv('SENDGRID_API_KEY'),
                'from_email': os.getenv('SENDGRID_FROM_EMAIL', 'noreply@dataregistry.com'),
                'from_name': os.getenv('SENDGRID_FROM_NAME', 'Data Registry Platform'),
                'template_approval': os.getenv('SENDGRID_TEMPLATE_APPROVAL'),
                'template_rejection': os.getenv('SENDGRID_TEMPLATE_REJECTION'),
                'enabled': bool(os.getenv('SENDGRID_API_KEY'))
            },
            
            # Application Settings
            'app': {
                'environment': os.getenv('APP_ENVIRONMENT', 'development'),
                'debug': os.getenv('APP_DEBUG', 'false').lower() == 'true',
                'domain': os.getenv('APP_DOMAIN', 'localhost:5000'),
                'secret_key': os.getenv('APP_SECRET_KEY'),
                'timezone': os.getenv('APP_TIMEZONE', 'UTC')
            }
        }
    
    def _check_services(self):
        """Check the status of all production services"""
        # Check Linode Object Storage
        if self.config['linode_storage']['enabled']:
            try:
                stats = linode_storage.get_storage_stats()
                self.services_status['linode_storage'] = {
                    'status': 'connected' if 'error' not in stats else 'error',
                    'details': stats
                }
            except Exception as e:
                self.services_status['linode_storage'] = {
                    'status': 'error',
                    'details': {'error': str(e)}
                }
        else:
            self.services_status['linode_storage'] = {
                'status': 'disabled',
                'details': {'error': 'Configuration incomplete'}
            }
        
        # Check Linode Database
        if self.config['linode_database']['enabled']:
            try:
                stats = linode_db.get_database_stats()
                self.services_status['linode_database'] = {
                    'status': 'connected' if 'error' not in stats else 'error',
                    'details': stats
                }
            except Exception as e:
                self.services_status['linode_database'] = {
                    'status': 'error',
                    'details': {'error': str(e)}
                }
        else:
            self.services_status['linode_database'] = {
                'status': 'disabled',
                'details': {'error': 'Configuration incomplete'}
            }
        
        # Check SendGrid
        if self.config['sendgrid']['enabled']:
            try:
                email_service = EmailService()
                self.services_status['sendgrid'] = {
                    'status': 'configured' if email_service.sg else 'error',
                    'details': {'from_email': self.config['sendgrid']['from_email']}
                }
            except Exception as e:
                self.services_status['sendgrid'] = {
                    'status': 'error',
                    'details': {'error': str(e)}
                }
        else:
            self.services_status['sendgrid'] = {
                'status': 'disabled',
                'details': {'error': 'API key not configured'}
            }
    
    def get_missing_secrets(self) -> List[str]:
        """Get list of missing required secrets"""
        missing_secrets = []
        
        # Required for Linode Object Storage
        if not self.config['linode_storage']['enabled']:
            linode_storage_secrets = ['LINODE_BUCKET_NAME', 'LINODE_ACCESS_KEY', 'LINODE_SECRET_KEY']
            missing_secrets.extend([s for s in linode_storage_secrets if not os.getenv(s)])
        
        # Required for Linode Database
        if not self.config['linode_database']['enabled']:
            linode_db_secrets = ['LINODE_DB_HOST', 'LINODE_DB_USER', 'LINODE_DB_PASSWORD']
            missing_secrets.extend([s for s in linode_db_secrets if not os.getenv(s)])
        
        # Required for SendGrid
        if not self.config['sendgrid']['enabled']:
            missing_secrets.append('SENDGRID_API_KEY')
        
        return list(set(missing_secrets))  # Remove duplicates
    
    def display_production_status(self):
        """Display production services status in Streamlit"""
        st.markdown("### 🏭 Production Services Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Linode Object Storage**")
            storage_status = self.services_status.get('linode_storage', {})
            if storage_status.get('status') == 'connected':
                st.success("✅ Connected")
                details = storage_status.get('details', {})
                if 'total_files' in details:
                    st.metric("Files", details['total_files'])
                    st.metric("Storage", f"{details.get('total_size_mb', 0)} MB")
            elif storage_status.get('status') == 'disabled':
                st.warning("⚠️ Not Configured")
            else:
                st.error("❌ Error")
        
        with col2:
            st.markdown("**Linode Database**")
            db_status = self.services_status.get('linode_database', {})
            if db_status.get('status') == 'connected':
                st.success("✅ Connected")
                details = db_status.get('details', {})
                if 'admins_count' in details:
                    st.metric("Admins", details['admins_count'])
                    st.metric("Users", details.get('individuals_count', 0) + details.get('organizations_count', 0))
            elif db_status.get('status') == 'disabled':
                st.warning("⚠️ Not Configured")
            else:
                st.error("❌ Error")
        
        with col3:
            st.markdown("**SendGrid Email**")
            email_status = self.services_status.get('sendgrid', {})
            if email_status.get('status') == 'configured':
                st.success("✅ Configured")
                details = email_status.get('details', {})
                st.caption(f"From: {details.get('from_email', 'Unknown')}")
            elif email_status.get('status') == 'disabled':
                st.warning("⚠️ Not Configured")
            else:
                st.error("❌ Error")
        
        # Show missing secrets if any
        missing_secrets = self.get_missing_secrets()
        if missing_secrets:
            st.error(f"Missing required secrets: {', '.join(missing_secrets)}")
            st.info("Please configure these environment variables for full production functionality.")
    
    def setup_production_deployment(self) -> Dict[str, bool]:
        """Setup production deployment"""
        results = {}
        
        # Initialize Linode Database
        if self.config['linode_database']['enabled']:
            results['database_init'] = linode_db.initialize_schema()
        else:
            results['database_init'] = False
        
        # Upload static files to Linode Object Storage
        if self.config['linode_storage']['enabled']:
            uploaded_files = linode_storage.upload_static_files()
            results['static_files_upload'] = len(uploaded_files) > 0
            
            # Store static file URLs in session state for use in templates
            st.session_state.static_file_urls = uploaded_files
        else:
            results['static_files_upload'] = False
        
        # Test email service
        if self.config['sendgrid']['enabled']:
            email_service = EmailService()
            results['email_test'] = email_service.sg is not None
        else:
            results['email_test'] = False
        
        return results
    
    def get_database_preference(self) -> str:
        """Get preferred database based on availability"""
        if self.config['linode_database']['enabled'] and self.services_status.get('linode_database', {}).get('status') == 'connected':
            return 'linode'
        elif st.session_state.get('database_connected', False):
            return 'postgresql'
        else:
            return 'fallback'
    
    def get_static_url(self, file_path: str) -> str:
        """Get static file URL (Linode Object Storage or local)"""
        if self.config['linode_storage']['enabled']:
            static_urls = st.session_state.get('static_file_urls', {})
            return static_urls.get(file_path, f"/static/{file_path}")
        else:
            return f"/static/{file_path}"

# Global production config instance
prod_config = ProductionConfig()