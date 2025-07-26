"""Database models and schema definitions"""

CREATE_TABLES_SQL = """
-- Create admins table
CREATE TABLE IF NOT EXISTS admins (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    admin_type VARCHAR(50) NOT NULL CHECK (admin_type IN ('Individual Admin', 'Organization Admin')),
    email VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create individuals table
CREATE TABLE IF NOT EXISTS individuals (
    individual_id SERIAL PRIMARY KEY,
    canonical_id VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    approved_by INTEGER REFERENCES admins(admin_id),
    rejection_reason TEXT,
    verification_token VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    organization_id SERIAL PRIMARY KEY,
    canonical_id VARCHAR(100) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(100) NOT NULL,
    primary_contact_email VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    website VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_date TIMESTAMP,
    approved_by INTEGER REFERENCES admins(admin_id),
    rejection_reason TEXT,
    verification_token VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    admin_id INTEGER REFERENCES admins(admin_id),
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create API keys table for client applications
CREATE TABLE IF NOT EXISTS api_keys (
    key_id SERIAL PRIMARY KEY,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create domain validation table
CREATE TABLE IF NOT EXISTS domain_validations (
    validation_id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'failed')),
    validation_method VARCHAR(50),
    validation_token VARCHAR(255),
    validated_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_individuals_canonical_id ON individuals(canonical_id);
CREATE INDEX IF NOT EXISTS idx_individuals_email ON individuals(email);
CREATE INDEX IF NOT EXISTS idx_individuals_status ON individuals(status);
CREATE INDEX IF NOT EXISTS idx_organizations_canonical_id ON organizations(canonical_id);
CREATE INDEX IF NOT EXISTS idx_organizations_email ON organizations(primary_contact_email);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);
CREATE INDEX IF NOT EXISTS idx_domain_validations_domain ON domain_validations(domain);
"""

INSERT_DEFAULT_ADMINS_SQL = """
-- Insert default admin users (only if they don't exist)
INSERT INTO admins (username, password_hash, admin_type, email) 
VALUES 
    ('individual_admin', 'pbkdf2_sha256$260000$default$hash', 'Individual Admin', 'individual.admin@dataregistry.com'),
    ('organization_admin', 'pbkdf2_sha256$260000$default$hash', 'Organization Admin', 'organization.admin@dataregistry.com')
ON CONFLICT (username) DO NOTHING;
"""

def get_individual_by_id(individual_id):
    """Get individual by ID"""
    return f"""
    SELECT * FROM individuals WHERE individual_id = {individual_id}
    """

def get_organization_by_id(organization_id):
    """Get organization by ID"""
    return f"""
    SELECT * FROM organizations WHERE organization_id = {organization_id}
    """

def get_pending_individuals():
    """Get all pending individual registrations"""
    return """
    SELECT * FROM individuals 
    WHERE status = 'pending' 
    ORDER BY request_date ASC
    """

def get_pending_organizations():
    """Get all pending organization registrations"""
    return """
    SELECT * FROM organizations 
    WHERE status = 'pending' 
    ORDER BY request_date ASC
    """

def search_individuals(search_term):
    """Search individuals by name, email, or canonical ID"""
    return f"""
    SELECT * FROM individuals 
    WHERE (first_name ILIKE '%{search_term}%' 
           OR last_name ILIKE '%{search_term}%' 
           OR email ILIKE '%{search_term}%' 
           OR canonical_id ILIKE '%{search_term}%')
    AND status = 'approved'
    ORDER BY first_name, last_name
    """

def search_organizations(search_term):
    """Search organizations by name, email, or canonical ID"""
    return f"""
    SELECT * FROM organizations 
    WHERE (organization_name ILIKE '%{search_term}%' 
           OR primary_contact_email ILIKE '%{search_term}%' 
           OR canonical_id ILIKE '%{search_term}%')
    AND status = 'approved'
    ORDER BY organization_name
    """
