"""User analytics and data insights service"""
import streamlit as st
from database.connection import get_db_connection
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd

class UserAnalyticsService:
    """Provides analytics and insights for registered users"""
    
    def __init__(self):
        pass
    
    def get_user_dashboard_data(self, canonical_id: str, user_type: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            dashboard_data = {
                'profile_info': self._get_profile_info(cursor, canonical_id, user_type),
                'analytics': self._get_user_analytics(cursor, canonical_id, user_type),
                'activity_history': self._get_activity_history(cursor, canonical_id, user_type),
                'data_connections': self._get_data_connections(cursor, canonical_id, user_type),
                'recommendations': self._get_recommendations(cursor, canonical_id, user_type)
            }
            
            conn.close()
            return dashboard_data
            
        except Exception as e:
            st.error(f"Dashboard data error: {e}")
            return {}
    
    def _get_profile_info(self, cursor, canonical_id: str, user_type: str) -> Dict[str, Any]:
        """Get detailed profile information"""
        if user_type == "individual":
            cursor.execute("""
                SELECT canonical_id, first_name, last_name, email, phone, 
                       address, birth_date, status, created_at, approved_at
                FROM individuals WHERE canonical_id = %s
            """, (canonical_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'canonical_id': result[0],
                    'display_name': f"{result[1]} {result[2]}",
                    'first_name': result[1],
                    'last_name': result[2],
                    'email': result[3],
                    'phone': result[4],
                    'address': result[5],
                    'birth_date': result[6],
                    'status': result[7],
                    'created_at': result[8],
                    'approved_at': result[9],
                    'type': 'individual'
                }
        
        elif user_type == "organization":
            cursor.execute("""
                SELECT canonical_id, organization_name, email, phone, address,
                       website, industry, status, created_at, approved_at
                FROM organizations WHERE canonical_id = %s
            """, (canonical_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'canonical_id': result[0],
                    'display_name': result[1],
                    'organization_name': result[1],
                    'email': result[2],
                    'phone': result[3],
                    'address': result[4],
                    'website': result[5],
                    'industry': result[6],
                    'status': result[7],
                    'created_at': result[8],
                    'approved_at': result[9],
                    'type': 'organization'
                }
        
        return {}
    
    def _get_user_analytics(self, cursor, canonical_id: str, user_type: str) -> Dict[str, Any]:
        """Get user analytics and metrics"""
        analytics = {
            'registration_date': None,
            'approval_date': None,
            'days_registered': 0,
            'days_since_approval': 0,
            'profile_completeness': 0,
            'api_keys_count': 0,
            'data_integrations': 0,
            'activity_score': 0
        }
        
        try:
            # Get basic info
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
                    
                    # Calculate days
                    if result[0]:
                        analytics['days_registered'] = (datetime.now() - result[0]).days
                    if result[1]:
                        analytics['days_since_approval'] = (datetime.now() - result[1]).days
                    
                    # Profile completeness
                    fields = [result[2], result[3], result[4], result[5], result[6], result[7]]
                    filled_fields = sum(1 for field in fields if field and str(field).strip())
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
                    
                    # Calculate days
                    if result[0]:
                        analytics['days_registered'] = (datetime.now() - result[0]).days
                    if result[1]:
                        analytics['days_since_approval'] = (datetime.now() - result[1]).days
                    
                    # Profile completeness
                    fields = [result[2], result[3], result[4], result[5], result[6], result[7]]
                    filled_fields = sum(1 for field in fields if field and str(field).strip())
                    analytics['profile_completeness'] = round((filled_fields / len(fields)) * 100)
            
            # Get API keys count
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM api_keys 
                    WHERE owner_id = %s AND owner_type = %s AND is_active = TRUE
                """, (canonical_id, user_type))
                analytics['api_keys_count'] = cursor.fetchone()[0]
            except:
                analytics['api_keys_count'] = 0
            
            # Calculate activity score (0-100)
            score = 0
            score += min(analytics['profile_completeness'], 40)  # Up to 40 points for profile
            score += min(analytics['api_keys_count'] * 10, 20)   # Up to 20 points for API keys
            score += min(analytics['days_since_approval'] // 7 * 2, 20)  # Up to 20 points for longevity
            score += 20 if analytics['days_since_approval'] > 0 else 0  # 20 points for being approved
            
            analytics['activity_score'] = min(score, 100)
            
        except Exception as e:
            st.error(f"Analytics calculation error: {e}")
        
        return analytics
    
    def _get_activity_history(self, cursor, canonical_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Get user activity history"""
        history = []
        
        try:
            # Get registration and approval events
            if user_type == "individual":
                cursor.execute("""
                    SELECT created_at, approved_at FROM individuals 
                    WHERE canonical_id = %s
                """, (canonical_id,))
            else:
                cursor.execute("""
                    SELECT created_at, approved_at FROM organizations 
                    WHERE canonical_id = %s
                """, (canonical_id,))
            
            result = cursor.fetchone()
            if result:
                if result[0]:
                    history.append({
                        'date': result[0],
                        'event': 'Registration',
                        'description': f'{user_type.title()} account created',
                        'type': 'account'
                    })
                
                if result[1]:
                    history.append({
                        'date': result[1],
                        'event': 'Approval',
                        'description': 'Account approved by administrator',
                        'type': 'account'
                    })
            
            # Get API key creation events (if table exists)
            try:
                cursor.execute("""
                    SELECT created_at, key_name FROM api_keys 
                    WHERE owner_id = %s AND owner_type = %s
                    ORDER BY created_at DESC
                """, (canonical_id, user_type))
                
                api_results = cursor.fetchall()
                for api_result in api_results:
                    history.append({
                        'date': api_result[0],
                        'event': 'API Key Created',
                        'description': f'API key "{api_result[1]}" generated',
                        'type': 'api'
                    })
            except:
                pass  # API keys table might not exist
            
            # Sort by date descending
            history.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
            
        except Exception as e:
            st.error(f"Activity history error: {e}")
        
        return history
    
    def _get_data_connections(self, cursor, canonical_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Get data connections and integrations (placeholder for future)"""
        # This is a placeholder for future data integration features
        return [
            {
                'source': 'Registry Database',
                'status': 'connected',
                'last_sync': datetime.now(),
                'records_count': 1
            }
        ]
    
    def _get_recommendations(self, cursor, canonical_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Get personalized recommendations for the user"""
        recommendations = []
        
        try:
            # Get user's profile completeness
            analytics = self._get_user_analytics(cursor, canonical_id, user_type)
            
            # Recommend profile completion
            if analytics['profile_completeness'] < 100:
                recommendations.append({
                    'type': 'profile',
                    'title': 'Complete Your Profile',
                    'description': f'Your profile is {analytics["profile_completeness"]}% complete. Adding missing information helps improve data accuracy.',
                    'action': 'Update profile information',
                    'priority': 'high' if analytics['profile_completeness'] < 60 else 'medium'
                })
            
            # Recommend API key generation
            if analytics['api_keys_count'] == 0:
                recommendations.append({
                    'type': 'api',
                    'title': 'Generate API Access',
                    'description': 'Create API keys to access your data programmatically and integrate with other systems.',
                    'action': 'Generate API key',
                    'priority': 'medium'
                })
            
            # Recommend exploring features
            if analytics['days_since_approval'] < 7:
                recommendations.append({
                    'type': 'feature',
                    'title': 'Explore Platform Features',
                    'description': 'Discover how to search the registry, manage your data, and use available tools.',
                    'action': 'View feature guide',
                    'priority': 'low'
                })
            
            # Data backup recommendation
            recommendations.append({
                'type': 'backup',
                'title': 'Download Your Data',
                'description': 'Keep a local copy of your registered data for your records.',
                'action': 'Download data export',
                'priority': 'low'
            })
            
        except Exception as e:
            st.error(f"Recommendations error: {e}")
        
        return recommendations
    
    def get_user_data_export(self, canonical_id: str, user_type: str) -> Dict[str, Any]:
        """Generate exportable user data"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            export_data = {
                'export_metadata': {
                    'canonical_id': canonical_id,
                    'user_type': user_type,
                    'export_date': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            # Get profile data
            profile_info = self._get_profile_info(cursor, canonical_id, user_type)
            export_data['profile'] = profile_info
            
            # Get analytics
            analytics = self._get_user_analytics(cursor, canonical_id, user_type)
            export_data['analytics'] = analytics
            
            # Get activity history
            history = self._get_activity_history(cursor, canonical_id, user_type)
            export_data['activity_history'] = history
            
            conn.close()
            return export_data
            
        except Exception as e:
            st.error(f"Data export error: {e}")
            return {}

# Global user analytics service instance
user_analytics = UserAnalyticsService()