"""User authentication service for registered individuals and organizations"""
import streamlit as st
from database.connection import get_db_connection
from utils.security import verify_password
from typing import Optional, Dict, Any

class UserAuthService:
    """Handles authentication for registered users (individuals and organizations)"""
    
    def __init__(self):
        self.session_key_user = "user_authenticated"
        self.session_key_user_type = "user_type"  # 'individual' or 'organization'
        self.session_key_user_id = "user_id"
        self.session_key_user_data = "user_data"
    
    def authenticate_user(self, canonical_id: str, email: str) -> bool:
        """Authenticate user using canonical ID and email"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check individuals first
            cursor.execute("""
                SELECT canonical_id, first_name, last_name, email, phone, 
                       address, birth_date, status, created_at, approved_at
                FROM individuals 
                WHERE canonical_id = %s AND email = %s AND status = 'approved'
            """, (canonical_id, email))
            
            individual_result = cursor.fetchone()
            
            if individual_result:
                # Set session for individual
                st.session_state[self.session_key_user] = True
                st.session_state[self.session_key_user_type] = "individual"
                st.session_state[self.session_key_user_id] = canonical_id
                st.session_state[self.session_key_user_data] = {
                    'canonical_id': individual_result[0],
                    'first_name': individual_result[1],
                    'last_name': individual_result[2],
                    'email': individual_result[3],
                    'phone': individual_result[4],
                    'address': individual_result[5],
                    'birth_date': individual_result[6],
                    'status': individual_result[7],
                    'created_at': individual_result[8],
                    'approved_at': individual_result[9]
                }
                conn.close()
                return True
            
            # Check organizations
            cursor.execute("""
                SELECT canonical_id, organization_name, email, phone, address,
                       website, industry, status, created_at, approved_at
                FROM organizations 
                WHERE canonical_id = %s AND email = %s AND status = 'approved'
            """, (canonical_id, email))
            
            organization_result = cursor.fetchone()
            
            if organization_result:
                # Set session for organization
                st.session_state[self.session_key_user] = True
                st.session_state[self.session_key_user_type] = "organization"
                st.session_state[self.session_key_user_id] = canonical_id
                st.session_state[self.session_key_user_data] = {
                    'canonical_id': organization_result[0],
                    'organization_name': organization_result[1],
                    'email': organization_result[2],
                    'phone': organization_result[3],
                    'address': organization_result[4],
                    'website': organization_result[5],
                    'industry': organization_result[6],
                    'status': organization_result[7],
                    'created_at': organization_result[8],
                    'approved_at': organization_result[9]
                }
                conn.close()
                return True
            
            conn.close()
            return False
            
        except Exception as e:
            st.error(f"Authentication error: {e}")
            return False
    
    def is_user_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get(self.session_key_user, False)
    
    def get_user_type(self) -> Optional[str]:
        """Get authenticated user type"""
        return st.session_state.get(self.session_key_user_type)
    
    def get_user_id(self) -> Optional[str]:
        """Get authenticated user ID"""
        return st.session_state.get(self.session_key_user_id)
    
    def get_user_data(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user data"""
        return st.session_state.get(self.session_key_user_data)
    
    def logout_user(self):
        """Logout user"""
        st.session_state[self.session_key_user] = False
        st.session_state[self.session_key_user_type] = None
        st.session_state[self.session_key_user_id] = None
        st.session_state[self.session_key_user_data] = None
    
    def get_user_analytics(self, canonical_id: str, user_type: str) -> Dict[str, Any]:
        """Get analytics data for a user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            analytics = {
                'registration_date': None,
                'approval_date': None,
                'data_sources_connected': 0,
                'api_requests_count': 0,
                'last_activity': None,
                'profile_completeness': 0
            }
            
            if user_type == "individual":
                cursor.execute("""
                    SELECT created_at, approved_at, first_name, last_name, 
                           email, phone, address, birth_date
                    FROM individuals WHERE canonical_id = %s
                """, (canonical_id,))
                
                result = cursor.fetchone()
                if result:
                    analytics['registration_date'] = result[0]
                    analytics['approval_date'] = result[1]
                    
                    # Calculate profile completeness
                    fields = [result[2], result[3], result[4], result[5], result[6], result[7]]
                    filled_fields = sum(1 for field in fields if field)
                    analytics['profile_completeness'] = round((filled_fields / len(fields)) * 100)
            
            elif user_type == "organization":
                cursor.execute("""
                    SELECT created_at, approved_at, organization_name, email, 
                           phone, address, website, industry
                    FROM organizations WHERE canonical_id = %s
                """, (canonical_id,))
                
                result = cursor.fetchone()
                if result:
                    analytics['registration_date'] = result[0]
                    analytics['approval_date'] = result[1]
                    
                    # Calculate profile completeness
                    fields = [result[2], result[3], result[4], result[5], result[6], result[7]]
                    filled_fields = sum(1 for field in fields if field)
                    analytics['profile_completeness'] = round((filled_fields / len(fields)) * 100)
            
            # Get API usage statistics (if API keys table exists)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM api_keys 
                    WHERE owner_id = %s AND owner_type = %s
                """, (canonical_id, user_type))
                api_keys_count = cursor.fetchone()[0]
                analytics['api_keys_count'] = api_keys_count
            except:
                analytics['api_keys_count'] = 0
            
            conn.close()
            return analytics
            
        except Exception as e:
            st.error(f"Analytics error: {e}")
            return {}

# Global user auth service instance
user_auth = UserAuthService()