-- New User-Centric Database Schema
-- This schema redesigns the data model to be user-centric with canonical IDs

-- Drop existing tables (for migration)
-- DROP TABLE IF EXISTS individuals CASCADE;
-- DROP TABLE IF EXISTS organizations CASCADE;

-- Core Users table - The primary identity table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    canonical_id VARCHAR(100) UNIQUE NOT NULL, -- Generated: FirstInitial + LastName + Last4Phone + EmailHash
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_date TIMESTAMP,
    approved_by INTEGER REFERENCES admins(admin_id),
    rejection_reason TEXT,
    metadata JSONB
);

-- User Emails table - Multiple emails per user, one primary
CREATE TABLE IF NOT EXISTS user_emails (
    email_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL, -- Extracted from email for domain verification
    is_primary BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, email),
    -- Ensure only one primary email per user
    CONSTRAINT unique_primary_email_per_user EXCLUDE (user_id WITH =) WHERE (is_primary = TRUE)
);

-- User Phones table - Multiple phone numbers per user, one primary
CREATE TABLE IF NOT EXISTS user_phones (
    phone_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    phone_type VARCHAR(50) DEFAULT 'mobile' CHECK (phone_type IN ('mobile', 'home', 'work', 'other')),
    is_primary BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, phone),
    -- Ensure only one primary phone per user
    CONSTRAINT unique_primary_phone_per_user EXCLUDE (user_id WITH =) WHERE (is_primary = TRUE)
);

-- Organizations table - Redesigned to link to users
CREATE TABLE IF NOT EXISTS organizations (
    organization_id SERIAL PRIMARY KEY,
    organization_canonical_id VARCHAR(100) UNIQUE NOT NULL, -- ORG- prefix + organization identifier
    organization_name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(100) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_date TIMESTAMP,
    approved_by INTEGER REFERENCES admins(admin_id),
    rejection_reason TEXT,
    metadata JSONB
);

-- User-Organization relationships - Many-to-many with roles
CREATE TABLE IF NOT EXISTS user_organizations (
    relationship_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(organization_id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL, -- 'owner', 'admin', 'employee', 'contractor', etc.
    is_primary_contact BOOLEAN DEFAULT FALSE,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organization_id, role),
    -- Ensure only one primary contact per organization
    CONSTRAINT unique_primary_contact_per_org EXCLUDE (organization_id WITH =) WHERE (is_primary_contact = TRUE)
);

-- Organization Emails table - Organizations can have multiple emails
CREATE TABLE IF NOT EXISTS organization_emails (
    org_email_id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(organization_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) DEFAULT 'general' CHECK (email_type IN ('general', 'support', 'sales', 'legal', 'hr')),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, email),
    -- Ensure only one primary email per organization
    CONSTRAINT unique_primary_org_email EXCLUDE (organization_id WITH =) WHERE (is_primary = TRUE)
);

-- Organization Phones table - Organizations can have multiple phones
CREATE TABLE IF NOT EXISTS organization_phones (
    org_phone_id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(organization_id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    phone_type VARCHAR(50) DEFAULT 'main' CHECK (phone_type IN ('main', 'support', 'sales', 'fax')),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, phone),
    -- Ensure only one primary phone per organization
    CONSTRAINT unique_primary_org_phone EXCLUDE (organization_id WITH =) WHERE (is_primary = TRUE)
);

-- User Addresses table - Users can have multiple addresses
CREATE TABLE IF NOT EXISTS user_addresses (
    address_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    address_type VARCHAR(50) DEFAULT 'home' CHECK (address_type IN ('home', 'work', 'billing', 'shipping', 'other')),
    street_address TEXT,
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'US',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Ensure only one primary address per user
    CONSTRAINT unique_primary_address_per_user EXCLUDE (user_id WITH =) WHERE (is_primary = TRUE)
);

-- Data Sources table - Track external systems connected to users
CREATE TABLE IF NOT EXISTS user_data_sources (
    source_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL, -- 'Salesforce', 'HubSpot', etc.
    source_type VARCHAR(100) NOT NULL, -- 'CRM', 'ERP', 'HR', etc.
    external_id VARCHAR(255), -- User's ID in the external system
    connection_status VARCHAR(50) DEFAULT 'connected' CHECK (connection_status IN ('connected', 'disconnected', 'error')),
    last_sync TIMESTAMP,
    sync_frequency VARCHAR(50) DEFAULT 'daily',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, source_name, external_id)
);

-- Audit log for the new schema
CREATE TABLE IF NOT EXISTS new_audit_log (
    log_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- 'user', 'organization', 'email', 'phone', etc.
    entity_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL, -- 'created', 'updated', 'deleted', 'verified', etc.
    user_id INTEGER REFERENCES users(user_id), -- Who made the change (if user-initiated)
    admin_id INTEGER REFERENCES admins(admin_id), -- Who made the change (if admin-initiated)
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_canonical_id ON users(canonical_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_user_emails_primary ON user_emails(user_id, is_primary);
CREATE INDEX IF NOT EXISTS idx_user_phones_primary ON user_phones(user_id, is_primary);
CREATE INDEX IF NOT EXISTS idx_user_organizations_user ON user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_org ON user_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_data_sources_user ON user_data_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON new_audit_log(entity_type, entity_id);

-- Views for easier querying
CREATE OR REPLACE VIEW user_primary_contact AS
SELECT 
    u.user_id,
    u.canonical_id,
    u.first_name,
    u.last_name,
    u.birth_date,
    ue.email as primary_email,
    ue.domain as primary_domain,
    up.phone as primary_phone,
    ua.street_address,
    ua.city,
    ua.state_province,
    ua.postal_code,
    ua.country,
    u.status,
    u.created_at,
    u.approved_date
FROM users u
LEFT JOIN user_emails ue ON u.user_id = ue.user_id AND ue.is_primary = TRUE
LEFT JOIN user_phones up ON u.user_id = up.user_id AND up.is_primary = TRUE
LEFT JOIN user_addresses ua ON u.user_id = ua.user_id AND ua.is_primary = TRUE;

CREATE OR REPLACE VIEW organization_primary_contact AS
SELECT 
    o.organization_id,
    o.organization_canonical_id,
    o.organization_name,
    o.organization_type,
    o.industry,
    o.website,
    oe.email as primary_email,
    op.phone as primary_phone,
    o.address,
    o.status,
    o.created_at,
    o.approved_date,
    u.canonical_id as primary_contact_user_id,
    u.first_name || ' ' || u.last_name as primary_contact_name
FROM organizations o
LEFT JOIN organization_emails oe ON o.organization_id = oe.organization_id AND oe.is_primary = TRUE
LEFT JOIN organization_phones op ON o.organization_id = op.organization_id AND op.is_primary = TRUE
LEFT JOIN user_organizations uo ON o.organization_id = uo.organization_id AND uo.is_primary_contact = TRUE
LEFT JOIN users u ON uo.user_id = u.user_id;