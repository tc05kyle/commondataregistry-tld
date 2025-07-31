"""Gravatar Integration Service for Profile Synchronization"""
import hashlib
import requests
import streamlit as st
from typing import Optional, Dict, Any, List
from database.connection import get_db_connection
import json
import os
from datetime import datetime

class GravatarService:
    """Service for integrating with Gravatar API to sync user profiles"""
    
    def __init__(self):
        self.base_url = "https://api.gravatar.com/v3"
        self.api_key = os.getenv('GRAVATAR_API_KEY')
        self.session = requests.Session()
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'User-Agent': 'DataRegistryPlatform/1.0'
            })
    
    def get_email_hash(self, email: str) -> str:
        """Convert email to SHA256 hash for Gravatar API"""
        # Gravatar requires email to be trimmed and lowercased before hashing
        clean_email = email.strip().lower()
        return hashlib.sha256(clean_email.encode('utf-8')).hexdigest()
    
    def get_profile(self, email: str) -> Optional[Dict[str, Any]]:
        """Get Gravatar profile data for an email address"""
        try:
            email_hash = self.get_email_hash(email)
            url = f"{self.base_url}/profiles/{email_hash}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # No Gravatar profile found
                return None
            else:
                st.warning(f"Gravatar API returned status {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching Gravatar profile: {e}")
            return None
    
    def get_avatar_url(self, email: str, size: int = 200, default: str = 'mp') -> str:
        """Get Gravatar avatar URL for an email"""
        email_hash = self.get_email_hash(email)
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"
    
    def sync_user_profile(self, canonical_id: str, email: str) -> Dict[str, Any]:
        """Sync user profile with Gravatar data"""
        try:
            # Get Gravatar profile
            gravatar_profile = self.get_profile(email)
            
            if not gravatar_profile:
                return {
                    'success': False,
                    'message': 'No Gravatar profile found for this email',
                    'gravatar_data': None
                }
            
            # Extract useful data from Gravatar profile
            sync_data = self._extract_sync_data(gravatar_profile)
            
            # Update local database with Gravatar data
            success = self._update_local_profile(canonical_id, sync_data)
            
            if success:
                # Log the sync activity
                self._log_sync_activity(canonical_id, email, sync_data)
                
                return {
                    'success': True,
                    'message': 'Profile successfully synced with Gravatar',
                    'gravatar_data': sync_data,
                    'avatar_url': self.get_avatar_url(email)
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update local profile with Gravatar data',
                    'gravatar_data': sync_data
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error during profile sync: {e}',
                'gravatar_data': None
            }
    
    def _extract_sync_data(self, gravatar_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data from Gravatar profile for local sync"""
        sync_data = {}
        
        # Basic profile info
        if 'display_name' in gravatar_profile:
            sync_data['display_name'] = gravatar_profile['display_name']
        
        if 'about_me' in gravatar_profile:
            sync_data['bio'] = gravatar_profile['about_me']
        
        if 'location' in gravatar_profile:
            sync_data['location'] = gravatar_profile['location']
        
        if 'profile_url' in gravatar_profile:
            sync_data['gravatar_url'] = gravatar_profile['profile_url']
        
        # Contact information
        if 'contact_info' in gravatar_profile:
            contact = gravatar_profile['contact_info']
            if 'home_phone' in contact:
                sync_data['home_phone'] = contact['home_phone']
            if 'work_phone' in contact:
                sync_data['work_phone'] = contact['work_phone']
        
        # Social accounts
        if 'accounts' in gravatar_profile:
            social_accounts = []
            for account in gravatar_profile['accounts']:
                social_accounts.append({
                    'service': account.get('service_label', account.get('service_type')),
                    'username': account.get('service_username'),
                    'url': account.get('service_url'),
                    'verified': account.get('verified', False)
                })
            sync_data['social_accounts'] = social_accounts
        
        # Languages and preferences
        if 'languages' in gravatar_profile:
            sync_data['languages'] = gravatar_profile['languages']
        
        if 'timezone' in gravatar_profile:
            sync_data['timezone'] = gravatar_profile['timezone']
        
        # Interests and skills
        if 'interests' in gravatar_profile:
            sync_data['interests'] = gravatar_profile['interests']
        
        # Avatar information
        if 'avatar_url' in gravatar_profile:
            sync_data['avatar_url'] = gravatar_profile['avatar_url']
        elif 'avatars' in gravatar_profile and gravatar_profile['avatars']:
            # Get the largest available avatar
            avatars = gravatar_profile['avatars']
            if avatars:
                sync_data['avatar_url'] = avatars[0].get('url')
        
        return sync_data
    
    def _update_local_profile(self, canonical_id: str, sync_data: Dict[str, Any]) -> bool:
        """Update local user profile with Gravatar data"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if using new or old schema
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'")
            has_new_schema = cursor.fetchone() is not None
            
            if has_new_schema:
                # Update users table with Gravatar data
                update_fields = []
                update_values = []
                
                # Create or update metadata JSON
                cursor.execute("SELECT metadata FROM users WHERE canonical_id = %s", (canonical_id,))
                result = cursor.fetchone()
                
                if result:
                    existing_metadata = result[0] or {}
                    existing_metadata['gravatar_sync'] = {
                        'last_sync': datetime.now().isoformat(),
                        'data': sync_data
                    }
                    
                    cursor.execute("""
                        UPDATE users 
                        SET metadata = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE canonical_id = %s
                    """, (json.dumps(existing_metadata), canonical_id))
                
            else:
                # Update individuals table with Gravatar data
                cursor.execute("SELECT metadata FROM individuals WHERE canonical_id = %s", (canonical_id,))
                result = cursor.fetchone()
                
                if result:
                    existing_metadata = result[0] or {}
                    existing_metadata['gravatar_sync'] = {
                        'last_sync': datetime.now().isoformat(),
                        'data': sync_data
                    }
                    
                    cursor.execute("""
                        UPDATE individuals 
                        SET metadata = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE canonical_id = %s
                    """, (json.dumps(existing_metadata), canonical_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error updating local profile: {e}")
            return False
    
    def _log_sync_activity(self, canonical_id: str, email: str, sync_data: Dict[str, Any]):
        """Log Gravatar sync activity"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check which audit table to use
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'new_audit_log'")
            has_new_audit = cursor.fetchone() is not None
            
            audit_table = 'new_audit_log' if has_new_audit else 'audit_log'
            
            if has_new_audit:
                cursor.execute(f"""
                    INSERT INTO {audit_table} (entity_type, entity_id, action, old_values, new_values)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    'user',
                    canonical_id,
                    'gravatar_sync',
                    json.dumps({'email': email}),
                    json.dumps(sync_data)
                ))
            else:
                cursor.execute(f"""
                    INSERT INTO {audit_table} (entity_type, entity_id, action, details)
                    VALUES (%s, %s, %s, %s)
                """, (
                    'individual',
                    canonical_id,
                    'gravatar_sync',
                    json.dumps({'email': email, 'sync_data': sync_data})
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            # Don't fail the sync if logging fails
            st.warning(f"Failed to log sync activity: {e}")
    
    def get_sync_status(self, canonical_id: str) -> Dict[str, Any]:
        """Get Gravatar sync status for a user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check new schema first
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'")
            has_new_schema = cursor.fetchone() is not None
            
            if has_new_schema:
                cursor.execute("SELECT metadata FROM users WHERE canonical_id = %s", (canonical_id,))
            else:
                cursor.execute("SELECT metadata FROM individuals WHERE canonical_id = %s", (canonical_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                metadata = result[0]
                gravatar_sync = metadata.get('gravatar_sync')
                
                if gravatar_sync:
                    return {
                        'has_sync': True,
                        'last_sync': gravatar_sync.get('last_sync'),
                        'sync_data': gravatar_sync.get('data', {}),
                        'avatar_url': gravatar_sync.get('data', {}).get('avatar_url')
                    }
            
            return {
                'has_sync': False,
                'last_sync': None,
                'sync_data': {},
                'avatar_url': None
            }
            
        except Exception as e:
            st.error(f"Error checking sync status: {e}")
            return {'has_sync': False, 'error': str(e)}
    
    def bulk_sync_users(self, limit: int = 50) -> Dict[str, Any]:
        """Bulk sync multiple users with Gravatar"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get users who haven't been synced recently
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'")
            has_new_schema = cursor.fetchone() is not None
            
            if has_new_schema:
                # Get users from new schema
                cursor.execute("""
                    SELECT u.canonical_id, ue.email 
                    FROM users u
                    JOIN user_emails ue ON u.user_id = ue.user_id
                    WHERE ue.is_primary = TRUE
                    AND u.status = 'approved'
                    AND (u.metadata->>'gravatar_sync' IS NULL 
                         OR (u.metadata->'gravatar_sync'->>'last_sync')::timestamp < NOW() - INTERVAL '7 days')
                    LIMIT %s
                """, (limit,))
            else:
                # Get users from old schema
                cursor.execute("""
                    SELECT canonical_id, email 
                    FROM individuals
                    WHERE status = 'approved'
                    AND (metadata->>'gravatar_sync' IS NULL 
                         OR (metadata->'gravatar_sync'->>'last_sync')::timestamp < NOW() - INTERVAL '7 days')
                    LIMIT %s
                """, (limit,))
            
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            
            sync_results = {
                'total_processed': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'no_gravatar_profile': 0,
                'results': []
            }
            
            for canonical_id, email in users:
                result = self.sync_user_profile(canonical_id, email)
                sync_results['total_processed'] += 1
                
                if result['success']:
                    sync_results['successful_syncs'] += 1
                elif 'No Gravatar profile found' in result['message']:
                    sync_results['no_gravatar_profile'] += 1
                else:
                    sync_results['failed_syncs'] += 1
                
                sync_results['results'].append({
                    'canonical_id': canonical_id,
                    'email': email,
                    'success': result['success'],
                    'message': result['message']
                })
            
            return sync_results
            
        except Exception as e:
            return {
                'error': f'Bulk sync failed: {e}',
                'total_processed': 0,
                'successful_syncs': 0,
                'failed_syncs': 0
            }
    
    def is_configured(self) -> bool:
        """Check if Gravatar API is properly configured"""
        return self.api_key is not None
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Gravatar API"""
        try:
            # Test with a known email (Gravatar founder)
            test_email = "beau@automattic.com"
            result = self.get_profile(test_email)
            
            return {
                'success': True,
                'message': 'Successfully connected to Gravatar API',
                'api_configured': self.is_configured(),
                'test_profile_found': result is not None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to connect to Gravatar API: {e}',
                'api_configured': self.is_configured()
            }

# Global Gravatar service instance
gravatar_service = GravatarService()