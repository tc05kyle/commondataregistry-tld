"""In-memory fallback storage for when database is unavailable"""
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from utils.security import hash_password

class FallbackStorage:
    """In-memory storage system for when database is unavailable"""
    
    def __init__(self):
        self.admins = {}
        self.individuals = {}
        self.organizations = {}
        self.registration_requests = {}
        self.api_keys = {}
        self._initialized = False
        
    def initialize(self):
        """Initialize with default admin users"""
        if not self._initialized:
            # Create default admin users
            self.admins['individual_admin'] = {
                'username': 'individual_admin',
                'password_hash': hash_password('admin123'),
                'admin_type': 'Individual Admin',
                'email': 'individual.admin@dataregistry.com',
                'is_active': True,
                'created_at': datetime.now()
            }
            
            self.admins['organization_admin'] = {
                'username': 'organization_admin',
                'password_hash': hash_password('admin123'),
                'admin_type': 'Organization Admin',
                'email': 'organization.admin@dataregistry.com',
                'is_active': True,
                'created_at': datetime.now()
            }
            
            self._initialized = True
    
    def get_admin(self, username: str) -> Optional[Dict]:
        """Get admin by username"""
        return self.admins.get(username)
    
    def add_registration_request(self, request_data: Dict) -> str:
        """Add a registration request and return its ID"""
        request_id = hashlib.md5(f"{request_data['email']}{datetime.now()}".encode()).hexdigest()[:12]
        request_data['id'] = request_id
        request_data['status'] = 'Pending'
        request_data['created_at'] = datetime.now()
        
        if request_data['registration_type'] == 'Individual':
            self.individuals[request_id] = request_data
        else:
            self.organizations[request_id] = request_data
            
        return request_id
    
    def get_pending_requests(self, request_type: str) -> List[Dict]:
        """Get pending registration requests"""
        if request_type == 'Individual':
            return [req for req in self.individuals.values() if req['status'] == 'Pending']
        else:
            return [req for req in self.organizations.values() if req['status'] == 'Pending']
    
    def update_request_status(self, request_id: str, status: str, admin_notes: str = None) -> bool:
        """Update request status"""
        # Check individuals first
        if request_id in self.individuals:
            self.individuals[request_id]['status'] = status
            if admin_notes:
                self.individuals[request_id]['admin_notes'] = admin_notes
            return True
        
        # Check organizations
        if request_id in self.organizations:
            self.organizations[request_id]['status'] = status
            if admin_notes:
                self.organizations[request_id]['admin_notes'] = admin_notes
            return True
            
        return False
    
    def get_request_by_email(self, email: str) -> Optional[Dict]:
        """Get request by email address"""
        # Check individuals
        for req in self.individuals.values():
            if req['email'] == email:
                return req
        
        # Check organizations
        for req in self.organizations.values():
            if req['email'] == email:
                return req
                
        return None
    
    def search_registry(self, query: str, registry_type: str = None) -> List[Dict]:
        """Search the registry"""
        results = []
        query_lower = query.lower()
        
        # Search individuals if no type specified or if type is individual
        if not registry_type or registry_type == 'individual':
            for individual in self.individuals.values():
                if individual['status'] == 'Approved':
                    if (query_lower in individual.get('first_name', '').lower() or
                        query_lower in individual.get('last_name', '').lower() or
                        query_lower in individual.get('email', '').lower()):
                        results.append(individual)
        
        # Search organizations if no type specified or if type is organization
        if not registry_type or registry_type == 'organization':
            for org in self.organizations.values():
                if org['status'] == 'Approved':
                    if (query_lower in org.get('organization_name', '').lower() or
                        query_lower in org.get('email', '').lower()):
                        results.append(org)
                        
        return results

# Global fallback storage instance
fallback_storage = FallbackStorage()