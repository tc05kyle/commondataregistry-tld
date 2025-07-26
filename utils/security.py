"""Security utilities"""
import hashlib
import secrets
import hmac
import re
from typing import Optional

def hash_password(password: str) -> str:
    """Hash password using PBKDF2"""
    salt = secrets.token_hex(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2_sha256$100000${salt}${pwdhash.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4:
            return False
        
        algorithm, iterations, salt, stored_hash = parts
        
        if algorithm != 'pbkdf2_sha256':
            return False
        
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), int(iterations))
        return hmac.compare_digest(stored_hash, pwdhash.hex())
        
    except Exception:
        return False

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', input_str)
    
    # Limit length
    sanitized = sanitized[:1000]
    
    return sanitized.strip()

def validate_canonical_id(canonical_id: str) -> tuple[bool, str]:
    """Validate canonical ID format"""
    if not canonical_id:
        return False, "Canonical ID cannot be empty"
    
    # Canonical ID should be alphanumeric with hyphens and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', canonical_id):
        return False, "Canonical ID can only contain letters, numbers, hyphens, and underscores"
    
    # Length constraints
    if len(canonical_id) < 3:
        return False, "Canonical ID must be at least 3 characters long"
    
    if len(canonical_id) > 50:
        return False, "Canonical ID cannot exceed 50 characters"
    
    # Cannot start or end with hyphen or underscore
    if canonical_id.startswith(('-', '_')) or canonical_id.endswith(('-', '_')):
        return False, "Canonical ID cannot start or end with hyphen or underscore"
    
    # Reserved words
    reserved_words = {'admin', 'api', 'www', 'root', 'system', 'null', 'undefined'}
    if canonical_id.lower() in reserved_words:
        return False, f"'{canonical_id}' is a reserved word and cannot be used"
    
    return True, "Valid canonical ID"

def validate_phone_number(phone: str) -> tuple[bool, str]:
    """Validate phone number format"""
    if not phone:
        return True, "Phone number is optional"
    
    # Remove common formatting characters
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Basic phone number validation
    if not re.match(r'^\+?1?\d{10,15}$', cleaned_phone):
        return False, "Invalid phone number format"
    
    return True, "Valid phone number"

def validate_website_url(url: str) -> tuple[bool, str]:
    """Validate website URL format"""
    if not url:
        return True, "Website URL is optional"
    
    # Basic URL validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url, re.IGNORECASE):
        return False, "Invalid website URL format"
    
    return True, "Valid website URL"

def check_sql_injection(input_str: str) -> bool:
    """Check for potential SQL injection patterns"""
    if not input_str:
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+set',
        r'exec\s*\(',
        r'<script',
        r'javascript:',
        r'--',
        r'/\*',
        r'\*/',
        r'xp_',
        r'sp_'
    ]
    
    input_lower = input_str.lower()
    
    for pattern in sql_patterns:
        if re.search(pattern, input_lower):
            return True
    
    return False

def check_xss_patterns(input_str: str) -> bool:
    """Check for potential XSS patterns"""
    if not input_str:
        return False
    
    # Common XSS patterns
    xss_patterns = [
        r'<script',
        r'javascript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'<applet'
    ]
    
    input_lower = input_str.lower()
    
    for pattern in xss_patterns:
        if re.search(pattern, input_lower):
            return True
    
    return False

def secure_compare(a: str, b: str) -> bool:
    """Secure string comparison to prevent timing attacks"""
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
