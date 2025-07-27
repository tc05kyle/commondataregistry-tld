"""Linode Database integration for production data storage"""
import psycopg2
import os
import streamlit as st
from typing import Optional, Dict, Any, List
import time
from contextlib import contextmanager

class LinodeDatabase:
    """Manages Linode Database connections and operations"""
    
    def __init__(self):
        self.connection_pool = []
        self.max_connections = 5
        self.connection_params = self._get_connection_params()
        self.is_available = self._test_connection()
    
    def _get_connection_params(self) -> Dict[str, str]:
        """Get Linode database connection parameters"""
        return {
            'host': os.getenv('LINODE_DB_HOST'),
            'port': os.getenv('LINODE_DB_PORT', '5432'),
            'database': os.getenv('LINODE_DB_NAME', 'dataregistry'),
            'user': os.getenv('LINODE_DB_USER'),
            'password': os.getenv('LINODE_DB_PASSWORD'),
            'sslmode': os.getenv('LINODE_DB_SSL_MODE', 'require')
        }
    
    def _test_connection(self) -> bool:
        """Test the Linode database connection"""
        params = self.connection_params
        
        # Check if all required parameters are present
        required_params = ['host', 'user', 'password', 'database']
        missing_params = [p for p in required_params if not params.get(p)]
        
        if missing_params:
            st.warning(f"Linode Database: Missing parameters: {', '.join(missing_params)}")
            return False
        
        try:
            conn = psycopg2.connect(**params)
            with conn.cursor() as cursor:
                cursor.execute('SELECT version()')
                version = cursor.fetchone()[0]
            conn.close()
            
            st.success(f"Connected to Linode Database: {version[:50]}...")
            return True
            
        except psycopg2.Error as e:
            st.error(f"Linode Database connection failed: {e}")
            return False
        except Exception as e:
            st.error(f"Unexpected error connecting to Linode Database: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            if not self.is_available:
                raise Exception("Linode Database not available")
            
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False) -> Any:
        """Execute a query on Linode Database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if fetch:
                        result = cursor.fetchall()
                        conn.commit()
                        return result
                    else:
                        conn.commit()
                        return cursor.rowcount
                        
        except psycopg2.Error as e:
            st.error(f"Linode Database query error: {e}")
            raise
        except Exception as e:
            st.error(f"Unexpected database error: {e}")
            raise
    
    def initialize_schema(self) -> bool:
        """Initialize the database schema"""
        if not self.is_available:
            return False
        
        try:
            from database.models import CREATE_TABLES_SQL
            from utils.security import hash_password
            
            # Create tables
            self.execute_query(CREATE_TABLES_SQL)
            
            # Insert default admin users
            individual_admin_hash = hash_password("admin123")
            organization_admin_hash = hash_password("admin123")
            
            self.execute_query("""
                INSERT INTO admins (username, password_hash, admin_type, email, is_active) 
                VALUES 
                    (%s, %s, 'Individual Admin', 'individual.admin@dataregistry.com', TRUE),
                    (%s, %s, 'Organization Admin', 'organization.admin@dataregistry.com', TRUE)
                ON CONFLICT (username) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    email = EXCLUDED.email
            """, ('individual_admin', individual_admin_hash, 'organization_admin', organization_admin_hash))
            
            st.success("Linode Database schema initialized successfully")
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize Linode Database schema: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.is_available:
            return {'error': 'Database not available'}
        
        try:
            stats = {}
            
            # Get table counts
            tables = ['admins', 'individuals', 'organizations', 'api_keys']
            for table in tables:
                try:
                    result = self.execute_query(f"SELECT COUNT(*) FROM {table}", fetch=True)
                    stats[f"{table}_count"] = result[0][0] if result else 0
                except:
                    stats[f"{table}_count"] = 0
            
            # Get database size
            try:
                result = self.execute_query(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))",
                    fetch=True
                )
                stats['database_size'] = result[0][0] if result else 'Unknown'
            except:
                stats['database_size'] = 'Unknown'
            
            # Get connection info
            stats['host'] = self.connection_params['host']
            stats['database'] = self.connection_params['database']
            stats['ssl_mode'] = self.connection_params['sslmode']
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def backup_data(self) -> Dict[str, Any]:
        """Create a backup of critical data"""
        if not self.is_available:
            return {'error': 'Database not available'}
        
        try:
            backup_data = {}
            
            # Backup admins
            result = self.execute_query(
                "SELECT username, password_hash, admin_type, email, is_active FROM admins",
                fetch=True
            )
            backup_data['admins'] = result
            
            # Backup individuals
            result = self.execute_query(
                "SELECT * FROM individuals WHERE status = 'Approved'",
                fetch=True
            )
            backup_data['individuals'] = result
            
            # Backup organizations
            result = self.execute_query(
                "SELECT * FROM organizations WHERE status = 'Approved'",
                fetch=True
            )
            backup_data['organizations'] = result
            
            backup_data['backup_timestamp'] = time.time()
            return backup_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def migrate_from_fallback(self, fallback_data: Dict[str, Any]) -> bool:
        """Migrate data from fallback storage to Linode Database"""
        if not self.is_available:
            return False
        
        try:
            # Migrate individuals
            for individual_id, data in fallback_data.get('individuals', {}).items():
                if data['status'] == 'Approved':
                    self.execute_query("""
                        INSERT INTO individuals 
                        (canonical_id, first_name, last_name, email, phone, address, 
                         birth_date, status, created_at, approved_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                    """, (
                        data.get('canonical_id'),
                        data.get('first_name'),
                        data.get('last_name'),
                        data.get('email'),
                        data.get('phone'),
                        data.get('address'),
                        data.get('birth_date'),
                        data.get('status'),
                        data.get('created_at'),
                        data.get('approved_at')
                    ))
            
            # Migrate organizations
            for org_id, data in fallback_data.get('organizations', {}).items():
                if data['status'] == 'Approved':
                    self.execute_query("""
                        INSERT INTO organizations 
                        (canonical_id, organization_name, email, phone, address,
                         website, industry, status, created_at, approved_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                    """, (
                        data.get('canonical_id'),
                        data.get('organization_name'),
                        data.get('email'),
                        data.get('phone'),
                        data.get('address'),
                        data.get('website'),
                        data.get('industry'),
                        data.get('status'),
                        data.get('created_at'),
                        data.get('approved_at')
                    ))
            
            st.success("Data migrated to Linode Database successfully")
            return True
            
        except Exception as e:
            st.error(f"Migration to Linode Database failed: {e}")
            return False

# Global instance
linode_db = LinodeDatabase()