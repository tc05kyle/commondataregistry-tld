"""Canonical ID System - User-centric global identifier generation"""
import re
from typing import Optional, Tuple, Dict, Any
from database.connection import get_db_connection
import streamlit as st

class CanonicalIDService:
    """Service for generating and managing canonical IDs based on user identity"""
    
    def __init__(self):
        self.id_pattern = r'^[A-Z][A-Z0-9]{4,15}$'  # First initial + lastname + phone digits + email hash
    
    def generate_canonical_id(self, first_name: str, last_name: str, primary_phone: str, primary_email: str) -> str:
        """
        Generate canonical ID: FirstInitial + LastName + Last4OfPhone + EmailHash
        Example: JSmith1234A7F
        """
        try:
            # Clean and validate inputs
            first_initial = first_name.strip().upper()[0] if first_name.strip() else 'X'
            clean_last_name = re.sub(r'[^A-Za-z]', '', last_name.strip()).upper()
            
            # Get last 4 digits of phone
            phone_digits = re.sub(r'[^0-9]', '', primary_phone)
            last_4_phone = phone_digits[-4:] if len(phone_digits) >= 4 else phone_digits.zfill(4)
            
            # Create simple email hash (first 3 chars of domain)
            email_domain = primary_email.split('@')[1] if '@' in primary_email else 'unknown'
            email_hash = re.sub(r'[^A-Za-z]', '', email_domain)[:3].upper().ljust(3, 'X')
            
            # Combine components
            base_id = f"{first_initial}{clean_last_name}{last_4_phone}{email_hash}"
            
            # Ensure ID is unique by checking database
            canonical_id = self._ensure_unique_id(base_id)
            
            return canonical_id
            
        except Exception as e:
            st.error(f"Error generating canonical ID: {e}")
            return f"ERROR{hash(str(e)) % 10000:04d}"
    
    def _ensure_unique_id(self, base_id: str) -> str:
        """Ensure the generated ID is unique in the database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if base ID exists in either old or new tables
            cursor.execute("""
                SELECT canonical_id FROM users WHERE canonical_id = %s
                UNION 
                SELECT canonical_id FROM individuals WHERE canonical_id = %s
            """, (base_id, base_id))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return base_id
            
            # If exists, append numeric suffix
            counter = 1
            while counter < 100:  # Prevent infinite loop
                test_id = f"{base_id}{counter:02d}"
                cursor.execute("""
                    SELECT canonical_id FROM users WHERE canonical_id = %s
                    UNION 
                    SELECT canonical_id FROM individuals WHERE canonical_id = %s
                """, (test_id, test_id))
                if not cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return test_id
                counter += 1
            
            cursor.close()
            conn.close()
            
            # Fallback if too many duplicates
            import time
            return f"{base_id}{int(time.time()) % 1000:03d}"
            
        except Exception as e:
            # Fallback ID generation
            import time
            return f"{base_id}{int(time.time()) % 1000:03d}"
    
    def validate_canonical_id_format(self, canonical_id: str) -> bool:
        """Validate canonical ID format"""
        return bool(re.match(self.id_pattern, canonical_id))
    
    def parse_canonical_id(self, canonical_id: str) -> Dict[str, str]:
        """Parse canonical ID to extract components"""
        if not self.validate_canonical_id_format(canonical_id):
            return {}
        
        try:
            # Basic parsing - this is approximate since the ID is hashed
            first_initial = canonical_id[0]
            
            # Find where digits start (phone portion)
            digit_start = -1
            for i, char in enumerate(canonical_id[1:], 1):
                if char.isdigit():
                    digit_start = i
                    break
            
            if digit_start > 1:
                last_name_part = canonical_id[1:digit_start]
                phone_part = canonical_id[digit_start:digit_start+4]
                email_part = canonical_id[digit_start+4:digit_start+7]
                
                return {
                    'first_initial': first_initial,
                    'last_name_part': last_name_part,
                    'phone_digits': phone_part,
                    'email_hash': email_part
                }
        except:
            pass
        
        return {}

# Global canonical ID service instance
canonical_id_service = CanonicalIDService()