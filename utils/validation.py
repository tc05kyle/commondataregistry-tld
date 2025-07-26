"""Data validation utilities"""
import re
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import streamlit as st

class IndividualRegistration(BaseModel):
    """Pydantic model for individual registration validation"""
    canonical_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str = None
    
    @validator('canonical_id')
    def validate_canonical_id(cls, v):
        if not v:
            raise ValueError('Canonical ID is required')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Canonical ID must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Canonical ID can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError('Name fields cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        if len(v.strip()) > 50:
            raise ValueError('Name cannot exceed 50 characters')
        if not re.match(r'^[a-zA-Z\s\'-]+$', v.strip()):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None or v == '':
            return None
        # Remove formatting characters
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?1?\d{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned

class OrganizationRegistration(BaseModel):
    """Pydantic model for organization registration validation"""
    canonical_id: str
    organization_name: str
    organization_type: str
    primary_contact_email: EmailStr
    phone: str = None
    address: str = None
    website: str = None
    
    @validator('canonical_id')
    def validate_canonical_id(cls, v):
        if not v:
            raise ValueError('Canonical ID is required')
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Canonical ID must be between 3 and 50 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Canonical ID can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('organization_name')
    def validate_organization_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Organization name is required')
        if len(v.strip()) < 2:
            raise ValueError('Organization name must be at least 2 characters long')
        if len(v.strip()) > 200:
            raise ValueError('Organization name cannot exceed 200 characters')
        return v.strip()
    
    @validator('organization_type')
    def validate_organization_type(cls, v):
        valid_types = [
            'Corporation', 'LLC', 'Partnership', 'Non-Profit', 'Government',
            'Educational Institution', 'Healthcare Provider', 'Financial Services',
            'Technology Company', 'Consulting Firm', 'CPA Firm', 'Law Firm',
            'Real Estate', 'Manufacturing', 'Retail', 'Other'
        ]
        if v not in valid_types:
            raise ValueError(f'Organization type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None or v == '':
            return None
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?1?\d{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned
    
    @validator('website')
    def validate_website(cls, v):
        if v is None or v == '':
            return None
        if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v, re.IGNORECASE):
            raise ValueError('Invalid website URL format')
        return v

class ValidationService:
    """Service for data validation"""
    
    def __init__(self):
        self.organization_types = [
            'Corporation', 'LLC', 'Partnership', 'Non-Profit', 'Government',
            'Educational Institution', 'Healthcare Provider', 'Financial Services',
            'Technology Company', 'Consulting Firm', 'CPA Firm', 'Law Firm',
            'Real Estate', 'Manufacturing', 'Retail', 'Other'
        ]
    
    def validate_individual_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate individual registration data"""
        errors = []
        
        try:
            individual = IndividualRegistration(**data)
            return True, []
        except Exception as e:
            errors.append(str(e))
            return False, errors
    
    def validate_organization_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate organization registration data"""
        errors = []
        
        try:
            organization = OrganizationRegistration(**data)
            return True, []
        except Exception as e:
            errors.append(str(e))
            return False, errors
    
    def check_canonical_id_uniqueness(self, canonical_id: str, entity_type: str) -> bool:
        """Check if canonical ID is unique across both individuals and organizations"""
        from database.connection import get_db_connection
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check individuals table
            cursor.execute("""
                SELECT COUNT(*) FROM individuals 
                WHERE canonical_id = %s AND status != 'rejected'
            """, (canonical_id,))
            
            individual_count = cursor.fetchone()[0]
            
            # Check organizations table
            cursor.execute("""
                SELECT COUNT(*) FROM organizations 
                WHERE canonical_id = %s AND status != 'rejected'
            """, (canonical_id,))
            
            organization_count = cursor.fetchone()[0]
            
            # Canonical ID must be unique across all entities
            return (individual_count + organization_count) == 0
            
        except Exception as e:
            st.error(f"Database error checking uniqueness: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def validate_and_sanitize_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize form data"""
        from utils.security import sanitize_input, check_sql_injection, check_xss_patterns
        
        sanitized_data = {}
        
        for key, value in form_data.items():
            if isinstance(value, str):
                # Check for malicious patterns
                if check_sql_injection(value) or check_xss_patterns(value):
                    raise ValueError(f"Invalid characters detected in {key}")
                
                # Sanitize the input
                sanitized_data[key] = sanitize_input(value)
            else:
                sanitized_data[key] = value
        
        return sanitized_data
    
    def validate_bulk_data(self, data_list: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """Validate bulk data for import"""
        results = {
            'valid_records': [],
            'invalid_records': [],
            'duplicate_canonical_ids': [],
            'total_processed': len(data_list)
        }
        
        seen_canonical_ids = set()
        
        for idx, record in enumerate(data_list):
            record_errors = []
            
            # Check for duplicate canonical IDs within the batch
            canonical_id = record.get('canonical_id', '')
            if canonical_id in seen_canonical_ids:
                record_errors.append(f"Duplicate canonical ID in batch: {canonical_id}")
                results['duplicate_canonical_ids'].append(canonical_id)
            else:
                seen_canonical_ids.add(canonical_id)
            
            # Validate the record
            if entity_type == 'individual':
                is_valid, validation_errors = self.validate_individual_data(record)
            else:
                is_valid, validation_errors = self.validate_organization_data(record)
            
            if validation_errors:
                record_errors.extend(validation_errors)
            
            # Check canonical ID uniqueness in database
            if canonical_id and not self.check_canonical_id_uniqueness(canonical_id, entity_type):
                record_errors.append(f"Canonical ID already exists: {canonical_id}")
            
            if record_errors:
                results['invalid_records'].append({
                    'row': idx + 1,
                    'data': record,
                    'errors': record_errors
                })
            else:
                results['valid_records'].append(record)
        
        return results
    
    def get_organization_types(self) -> List[str]:
        """Get list of valid organization types"""
        return self.organization_types
    
    def normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number format"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Add +1 if it's a 10-digit US number
        if len(cleaned) == 10 and cleaned.isdigit():
            cleaned = '+1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            cleaned = '+' + cleaned
        
        return cleaned
    
    def normalize_email(self, email: str) -> str:
        """Normalize email address"""
        if not email:
            return ""
        
        return email.lower().strip()
    
    def normalize_canonical_id(self, canonical_id: str) -> str:
        """Normalize canonical ID"""
        if not canonical_id:
            return ""
        
        # Convert to lowercase and replace spaces with hyphens
        normalized = canonical_id.lower().strip()
        normalized = re.sub(r'\s+', '-', normalized)
        
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-_')
        
        return normalized
