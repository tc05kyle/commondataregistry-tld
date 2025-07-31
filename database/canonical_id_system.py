"""Canonical ID System - User-centric global identifier generation"""
import re
from typing import Optional, Tuple, Dict, Any
from database.connection import get_db_connection
import streamlit as st

class CanonicalIDService:
    """Service for generating and managing canonical IDs based on user identity"""
    
    def __init__(self):
        self.id_pattern = r'^[A-Z]\.[A-Z]+\.[0-9]{4}\.[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(\.[0-9]{2})?$'  # FirstInitial.LastName.Phone.Email[.Counter]
    
    def generate_canonical_id(self, first_name: str, last_name: str, primary_phone: str, primary_email: str) -> str:
        """
        Generate canonical ID: FirstInitial.LastName.Last4OfPhone.FullEmail
        Example: J.Smith.6738.jsmith@hotmail.com
        """
        try:
            # Clean and validate inputs
            first_initial = first_name.strip().upper()[0] if first_name.strip() else 'X'
            clean_last_name = re.sub(r'[^A-Za-z]', '', last_name.strip()).upper()
            
            # Get last 4 digits of phone
            phone_digits = re.sub(r'[^0-9]', '', primary_phone)
            last_4_phone = phone_digits[-4:] if len(phone_digits) >= 4 else phone_digits.zfill(4)
            
            # Use full email address as the 4th segment
            clean_email = primary_email.strip().lower()
            
            # Combine components with periods (IP-like format with full email)
            base_id = f"{first_initial}.{clean_last_name}.{last_4_phone}.{clean_email}"
            
            # Ensure ID is unique by checking database
            canonical_id = self._ensure_unique_id(base_id)
            
            return canonical_id
            
        except Exception as e:
            st.error(f"Error generating canonical ID: {e}")
            return f"ERROR.{hash(str(e)) % 1000:03d}.0000.error@unknown.com"
    
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
            
            # If exists, append numeric suffix with period
            counter = 1
            while counter < 100:  # Prevent infinite loop
                test_id = f"{base_id}.{counter:02d}"
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
            return f"{base_id}.{int(time.time()) % 1000:03d}"
            
        except Exception as e:
            # Fallback ID generation
            import time
            return f"{base_id}.{int(time.time()) % 1000:03d}"
    
    def validate_canonical_id_format(self, canonical_id: str) -> bool:
        """Validate canonical ID format"""
        return bool(re.match(self.id_pattern, canonical_id))
    
    def parse_canonical_id(self, canonical_id: str) -> Dict[str, str]:
        """Parse canonical ID to extract components from dot-separated format"""
        if not self.validate_canonical_id_format(canonical_id):
            return {}
        
        try:
            # Split by periods for IP-like format: J.Smith.1234.DOM or J.Smith.1234.DOM.01
            parts = canonical_id.split('.')
            
            if len(parts) >= 4:
                # Handle case where email might contain dots (need to rejoin email parts)
                if len(parts) > 4 and '@' in '.'.join(parts[3:]):
                    # Find where the email ends and counter begins
                    email_parts = []
                    counter = None
                    
                    for i, part in enumerate(parts[3:], 3):
                        if '@' in part or (i > 3 and '@' in '.'.join(email_parts)):
                            email_parts.append(part)
                        elif part.isdigit() and len(part) == 2:
                            # This is likely the counter
                            counter = part
                            break
                        else:
                            email_parts.append(part)
                    
                    full_email = '.'.join(email_parts)
                    
                    return {
                        'first_initial': parts[0],
                        'last_name_part': parts[1],
                        'phone_digits': parts[2],
                        'email': full_email,
                        'counter': counter
                    }
                else:
                    return {
                        'first_initial': parts[0],
                        'last_name_part': parts[1],
                        'phone_digits': parts[2],
                        'email': parts[3],
                        'counter': parts[4] if len(parts) > 4 else None
                    }
        except:
            pass
        
        return {}

# Global canonical ID service instance
canonical_id_service = CanonicalIDService()