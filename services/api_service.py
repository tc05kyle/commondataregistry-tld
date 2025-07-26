"""API service for client applications"""
import hashlib
import time
import json
from typing import Dict, Any, Optional
import streamlit as st
from database.connection import get_db_connection, execute_query

class APIService:
    def __init__(self):
        self.rate_limits = {}  # In-memory rate limiting (use Redis in production)
    
    def generate_api_key(self, client_name: str) -> str:
        """Generate a new API key"""
        timestamp = str(int(time.time()))
        data = f"{client_name}_{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate API key and return client info"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key_id, client_name, client_email, is_active, rate_limit, expires_at
                FROM api_keys 
                WHERE api_key = %s AND is_active = TRUE
            """, (api_key,))
            
            result = cursor.fetchone()
            
            if result:
                # Update last_used timestamp
                cursor.execute("""
                    UPDATE api_keys 
                    SET last_used = CURRENT_TIMESTAMP 
                    WHERE api_key = %s
                """, (api_key,))
                conn.commit()
                
                return {
                    'key_id': result[0],
                    'client_name': result[1],
                    'client_email': result[2],
                    'is_active': result[3],
                    'rate_limit': result[4],
                    'expires_at': result[5]
                }
            
            return None
            
        except Exception as e:
            st.error(f"API key validation error: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def check_rate_limit(self, api_key: str, rate_limit: int) -> bool:
        """Check if API key has exceeded rate limit"""
        current_time = time.time()
        hour_start = int(current_time // 3600) * 3600
        
        if api_key not in self.rate_limits:
            self.rate_limits[api_key] = {}
        
        if hour_start not in self.rate_limits[api_key]:
            self.rate_limits[api_key] = {hour_start: 0}
        
        # Clean old entries
        self.rate_limits[api_key] = {
            k: v for k, v in self.rate_limits[api_key].items() 
            if k >= hour_start - 3600
        }
        
        current_count = self.rate_limits[api_key].get(hour_start, 0)
        
        if current_count >= rate_limit:
            return False
        
        self.rate_limits[api_key][hour_start] = current_count + 1
        return True
    
    def lookup_individual(self, api_key: str, canonical_id: str) -> Dict[str, Any]:
        """API endpoint to lookup individual by canonical ID"""
        # Validate API key
        client_info = self.validate_api_key(api_key)
        if not client_info:
            return {'error': 'Invalid API key', 'status': 401}
        
        # Check rate limit
        if not self.check_rate_limit(api_key, client_info['rate_limit']):
            return {'error': 'Rate limit exceeded', 'status': 429}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT canonical_id, first_name, last_name, email, domain, 
                       phone, status, created_at, updated_at
                FROM individuals 
                WHERE canonical_id = %s AND status = 'approved'
            """, (canonical_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'canonical_id': result[0],
                    'first_name': result[1],
                    'last_name': result[2],
                    'email': result[3],
                    'domain': result[4],
                    'phone': result[5],
                    'status': result[6],
                    'created_at': result[7].isoformat() if result[7] else None,
                    'updated_at': result[8].isoformat() if result[8] else None,
                    'status': 200
                }
            else:
                return {'error': 'Individual not found', 'status': 404}
                
        except Exception as e:
            return {'error': f'Database error: {str(e)}', 'status': 500}
        finally:
            if conn:
                conn.close()
    
    def lookup_organization(self, api_key: str, canonical_id: str) -> Dict[str, Any]:
        """API endpoint to lookup organization by canonical ID"""
        # Validate API key
        client_info = self.validate_api_key(api_key)
        if not client_info:
            return {'error': 'Invalid API key', 'status': 401}
        
        # Check rate limit
        if not self.check_rate_limit(api_key, client_info['rate_limit']):
            return {'error': 'Rate limit exceeded', 'status': 429}
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT canonical_id, organization_name, organization_type, 
                       primary_contact_email, domain, phone, address, website,
                       status, created_at, updated_at
                FROM organizations 
                WHERE canonical_id = %s AND status = 'approved'
            """, (canonical_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'canonical_id': result[0],
                    'organization_name': result[1],
                    'organization_type': result[2],
                    'primary_contact_email': result[3],
                    'domain': result[4],
                    'phone': result[5],
                    'address': result[6],
                    'website': result[7],
                    'status': result[8],
                    'created_at': result[9].isoformat() if result[9] else None,
                    'updated_at': result[10].isoformat() if result[10] else None,
                    'status': 200
                }
            else:
                return {'error': 'Organization not found', 'status': 404}
                
        except Exception as e:
            return {'error': f'Database error: {str(e)}', 'status': 500}
        finally:
            if conn:
                conn.close()
    
    def search_entities(self, api_key: str, query: str, entity_type: str = 'both') -> Dict[str, Any]:
        """API endpoint to search for entities"""
        # Validate API key
        client_info = self.validate_api_key(api_key)
        if not client_info:
            return {'error': 'Invalid API key', 'status': 401}
        
        # Check rate limit
        if not self.check_rate_limit(api_key, client_info['rate_limit']):
            return {'error': 'Rate limit exceeded', 'status': 429}
        
        try:
            results = {'individuals': [], 'organizations': []}
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Search individuals
            if entity_type in ['both', 'individual']:
                cursor.execute("""
                    SELECT canonical_id, first_name, last_name, email, domain
                    FROM individuals 
                    WHERE (first_name ILIKE %s OR last_name ILIKE %s 
                           OR email ILIKE %s OR canonical_id ILIKE %s)
                    AND status = 'approved'
                    LIMIT 50
                """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
                
                individuals = cursor.fetchall()
                results['individuals'] = [
                    {
                        'canonical_id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'email': row[3],
                        'domain': row[4]
                    }
                    for row in individuals
                ]
            
            # Search organizations
            if entity_type in ['both', 'organization']:
                cursor.execute("""
                    SELECT canonical_id, organization_name, organization_type, 
                           primary_contact_email, domain
                    FROM organizations 
                    WHERE (organization_name ILIKE %s OR primary_contact_email ILIKE %s 
                           OR canonical_id ILIKE %s)
                    AND status = 'approved'
                    LIMIT 50
                """, (f'%{query}%', f'%{query}%', f'%{query}%'))
                
                organizations = cursor.fetchall()
                results['organizations'] = [
                    {
                        'canonical_id': row[0],
                        'organization_name': row[1],
                        'organization_type': row[2],
                        'primary_contact_email': row[3],
                        'domain': row[4]
                    }
                    for row in organizations
                ]
            
            return {
                'results': results,
                'total_individuals': len(results['individuals']),
                'total_organizations': len(results['organizations']),
                'status': 200
            }
            
        except Exception as e:
            return {'error': f'Database error: {str(e)}', 'status': 500}
        finally:
            if conn:
                conn.close()
    
    def create_api_key(self, client_name: str, client_email: str, rate_limit: int = 1000) -> Dict[str, Any]:
        """Create a new API key for a client"""
        try:
            api_key = self.generate_api_key(client_name)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO api_keys (api_key, client_name, client_email, rate_limit)
                VALUES (%s, %s, %s, %s)
                RETURNING key_id
            """, (api_key, client_name, client_email, rate_limit))
            
            key_id = cursor.fetchone()[0]
            conn.commit()
            
            return {
                'key_id': key_id,
                'api_key': api_key,
                'client_name': client_name,
                'client_email': client_email,
                'rate_limit': rate_limit,
                'status': 201
            }
            
        except Exception as e:
            return {'error': f'API key creation failed: {str(e)}', 'status': 500}
        finally:
            if conn:
                conn.close()
