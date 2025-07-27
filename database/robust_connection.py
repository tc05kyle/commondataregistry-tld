"""Robust database connection with multiple fallback strategies"""
import os
import psycopg2
import time
import streamlit as st
from typing import Optional, Dict, Any
import logging

class DatabaseManager:
    """Manages database connections with robust fallback strategies"""
    
    def __init__(self):
        self.connection = None
        self.connection_type = None
        self.last_connection_attempt = 0
        self.connection_retry_delay = 5  # seconds
        self.max_retries = 3
        
    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Get a database connection with automatic retry and fallback"""
        current_time = time.time()
        
        # Check if we should retry connection
        if (self.connection is None and 
            current_time - self.last_connection_attempt > self.connection_retry_delay):
            
            self.last_connection_attempt = current_time
            self._attempt_connection()
        
        return self.connection
    
    def _attempt_connection(self):
        """Attempt to establish database connection"""
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            self._log_connection_status("No DATABASE_URL found")
            return
        
        for attempt in range(self.max_retries):
            try:
                # Create new connection
                conn = psycopg2.connect(
                    database_url,
                    connect_timeout=10,
                    sslmode='require'
                )
                
                # Test the connection
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                
                self.connection = conn
                self.connection_type = "PostgreSQL"
                self._log_connection_status(f"Connected successfully (attempt {attempt + 1})")
                return
                
            except psycopg2.OperationalError as e:
                if "endpoint has been disabled" in str(e).lower():
                    self._log_connection_status(f"Database endpoint disabled (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)  # Brief delay before retry
                        continue
                    else:
                        self._log_connection_status("All connection attempts failed - using fallback mode")
                        break
                else:
                    self._log_connection_status(f"Connection error: {str(e)[:100]}...")
                    break
            except Exception as e:
                self._log_connection_status(f"Unexpected error: {str(e)[:100]}...")
                break
    
    def _log_connection_status(self, message: str):
        """Log connection status messages"""
        # Use Streamlit's session state to track messages
        if 'db_messages' not in st.session_state:
            st.session_state.db_messages = []
        
        st.session_state.db_messages.append(message)
        # Keep only last 5 messages
        if len(st.session_state.db_messages) > 5:
            st.session_state.db_messages = st.session_state.db_messages[-5:]
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a query with automatic connection management"""
        conn = self.get_connection()
        
        if not conn:
            raise Exception("No database connection available")
        
        try:
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
            conn.rollback()
            # Reset connection on error
            self.connection = None
            raise Exception(f"Database query failed: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current database status"""
        if self.connection:
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                return {
                    'connected': True,
                    'type': self.connection_type,
                    'version': version[:50] + '...' if len(version) > 50 else version
                }
            except Exception:
                self.connection = None
                return {'connected': False, 'type': 'None', 'error': 'Connection test failed'}
        else:
            return {'connected': False, 'type': 'None', 'error': 'No active connection'}
    
    def close(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            self.connection = None

# Global database manager instance
db_manager = DatabaseManager()