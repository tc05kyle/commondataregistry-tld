# Data Registry Platform

## Overview

This is a Streamlit-based Data Registry Platform that manages canonical unique IDs for individuals and organizations. The platform provides a complete admin dashboard system with role-based access control, email notifications, and API services for client applications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit multi-page application
- **Structure**: Main app.py with separate page files in `/pages/` directory
- **UI Components**: Form-based interfaces with tabs for different functionalities
- **Authentication**: Session-based authentication with role-based access control

### Backend Architecture
- **Language**: Python
- **Database**: PostgreSQL with direct psycopg2 connections
- **Architecture Pattern**: Service-oriented with clear separation of concerns
- **Services**: Email service (SendGrid), API service, domain validation, and data validation

### Data Storage
- **Primary Database**: PostgreSQL
- **Connection Management**: Environment variable-based configuration with fallback options
- **Schema**: Relational database with tables for admins, individuals, organizations, and API keys

## Key Components

### Core Application Files
- **app.py**: Main application entry point with authentication and routing
- **Database Layer**: Connection management and model definitions
- **Services Layer**: Email, API, domain validation, and business logic
- **Utils Layer**: Security, validation, and utility functions

### Page Components
1. **Individual Admin Dashboard** (`pages/1_Individual_Admin.py`)
2. **Organization Admin Dashboard** (`pages/2_Organization_Admin.py`)
3. **Registration Request** (`pages/3_Registration_Request.py`)
4. **API Testing** (`pages/4_API_Testing.py`)
5. **Registry Lookup** (`pages/5_Registry_Lookup.py`)

### Service Components
- **Email Service**: SendGrid integration for notification emails
- **API Service**: Rate-limited API key management and validation
- **Domain Validator**: DNS and MX record validation for business domains
- **Validation Service**: Pydantic-based data validation

## Data Flow

### Registration Process
1. User submits registration request via web form
2. Data validation and domain verification
3. Admin review and approval/rejection
4. Email notification to user
5. Canonical ID assignment upon approval

### Admin Workflow
1. Authentication via admin login
2. Role-based dashboard access
3. Review pending registrations
4. Approve/reject with email notifications
5. Audit trail logging

### API Integration
1. API key generation and management
2. Rate limiting and authentication
3. Registry lookup and search capabilities
4. JSON response formatting

## External Dependencies

### Email Service
- **Provider**: SendGrid
- **Configuration**: API key via environment variables
- **Purpose**: Automated notifications for registration status

### Database
- **Type**: PostgreSQL
- **Connection**: Environment variable configuration
- **Fallback**: Local development settings

### Validation Libraries
- **Pydantic**: Data validation and serialization
- **Validators**: Email and URL validation
- **DNS Resolution**: Domain validation

## Deployment Strategy

### Environment Configuration
- Database connection via `DATABASE_URL` or individual PostgreSQL environment variables
- SendGrid API key configuration
- Streamlit cloud deployment ready

### Security Measures
- PBKDF2 password hashing with salts
- Input sanitization and validation
- SQL injection prevention through parameterized queries
- Secure token generation for API keys

### Database Initialization
- Automatic table creation on startup
- Default admin user seeding
- Error handling for connection failures

The application follows a clean architecture pattern with clear separation between presentation, business logic, and data layers. The system is designed for scalability with proper error handling, logging, and security measures in place.