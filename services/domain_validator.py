"""Domain validation service"""
import re
import socket
import validators
import requests
from typing import Tuple, Optional
import streamlit as st

class DomainValidator:
    def __init__(self):
        self.valid_domains = set()
        self.invalid_domains = set()
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        return validators.email(email)
    
    def extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not self.validate_email_format(email):
            return None
        
        try:
            return email.split('@')[1].lower()
        except IndexError:
            return None
    
    def validate_domain_dns(self, domain: str) -> bool:
        """Validate domain through DNS lookup"""
        try:
            # Check if domain has MX record
            socket.getaddrinfo(domain, None)
            return True
        except socket.gaierror:
            return False
    
    def validate_domain_mx(self, domain: str) -> bool:
        """Validate domain has MX record"""
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except:
            # Fall back to basic DNS validation if dnspython not available
            return self.validate_domain_dns(domain)
    
    def is_business_domain(self, domain: str) -> Tuple[bool, str]:
        """Check if domain appears to be a business domain"""
        # Common free email providers
        free_providers = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com', 'mail.com',
            'yandex.com', 'zoho.com', 'gmx.com'
        }
        
        domain_lower = domain.lower()
        
        if domain_lower in free_providers:
            return False, f"Free email provider: {domain}"
        
        # Check domain length and structure
        if len(domain_lower) < 4:
            return False, "Domain too short"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\d{4,}',  # Many consecutive numbers
            r'temp',    # Temporary
            r'test',    # Test domains
            r'fake',    # Fake domains
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain_lower):
                return False, f"Suspicious domain pattern: {pattern}"
        
        return True, "Valid business domain"
    
    def validate_email_domain(self, email: str) -> Tuple[bool, str, dict]:
        """Comprehensive email domain validation"""
        validation_result = {
            'email': email,
            'domain': None,
            'format_valid': False,
            'dns_valid': False,
            'mx_valid': False,
            'business_domain': False,
            'validation_details': []
        }
        
        # Step 1: Validate email format
        if not self.validate_email_format(email):
            validation_result['validation_details'].append("Invalid email format")
            return False, "Invalid email format", validation_result
        
        validation_result['format_valid'] = True
        
        # Step 2: Extract domain
        domain = self.extract_domain(email)
        if not domain:
            validation_result['validation_details'].append("Could not extract domain")
            return False, "Could not extract domain", validation_result
        
        validation_result['domain'] = domain
        
        # Step 3: DNS validation
        if domain in self.valid_domains:
            validation_result['dns_valid'] = True
        elif domain in self.invalid_domains:
            validation_result['dns_valid'] = False
            validation_result['validation_details'].append("Domain failed DNS validation (cached)")
        else:
            dns_valid = self.validate_domain_dns(domain)
            validation_result['dns_valid'] = dns_valid
            
            if dns_valid:
                self.valid_domains.add(domain)
            else:
                self.invalid_domains.add(domain)
                validation_result['validation_details'].append("Domain failed DNS validation")
        
        # Step 4: MX record validation
        if validation_result['dns_valid']:
            mx_valid = self.validate_domain_mx(domain)
            validation_result['mx_valid'] = mx_valid
            if not mx_valid:
                validation_result['validation_details'].append("Domain has no MX record")
        
        # Step 5: Business domain validation
        is_business, business_reason = self.is_business_domain(domain)
        validation_result['business_domain'] = is_business
        validation_result['validation_details'].append(business_reason)
        
        # Overall validation
        if validation_result['format_valid'] and validation_result['dns_valid'] and validation_result['business_domain']:
            return True, "Email domain validated successfully", validation_result
        else:
            failed_checks = []
            if not validation_result['format_valid']:
                failed_checks.append("format")
            if not validation_result['dns_valid']:
                failed_checks.append("DNS")
            if not validation_result['business_domain']:
                failed_checks.append("business domain")
            
            return False, f"Validation failed: {', '.join(failed_checks)}", validation_result
    
    def validate_multiple_emails(self, emails: list) -> dict:
        """Validate multiple email addresses"""
        results = {}
        
        for email in emails:
            is_valid, message, details = self.validate_email_domain(email)
            results[email] = {
                'valid': is_valid,
                'message': message,
                'details': details
            }
        
        return results
    
    def get_domain_info(self, domain: str) -> dict:
        """Get additional domain information"""
        info = {
            'domain': domain,
            'registrar': None,
            'creation_date': None,
            'expiration_date': None,
            'nameservers': [],
            'whois_available': False
        }
        
        try:
            # This would require a WHOIS library in a real implementation
            # For now, we'll just return basic info
            info['whois_available'] = True
        except:
            pass
        
        return info
