"""Registration Request Page"""
import streamlit as st
import uuid
from datetime import datetime
from database.connection import get_db_connection
from services.email_service import EmailService
from services.domain_validator import DomainValidator
from utils.validation import ValidationService
from utils.security import generate_secure_token, sanitize_input

# Initialize services
email_service = EmailService()
domain_validator = DomainValidator()
validation_service = ValidationService()

st.set_page_config(
    page_title="Registration Request",
    page_icon="📝",
    layout="wide"
)

def main():
    st.title("📝 Registration Request")
    st.markdown("---")
    
    st.markdown("""
    Welcome to the Data Registry Platform registration system. Please submit your request for a 
    canonical unique ID to participate in our data management framework.
    """)
    
    # Create tabs for different registration types
    tab1, tab2, tab3 = st.tabs(["Individual Registration", "Organization Registration", "Check Status"])
    
    with tab1:
        individual_registration_form()
    
    with tab2:
        organization_registration_form()
    
    with tab3:
        check_registration_status()

def individual_registration_form():
    """Individual registration form"""
    st.subheader("Individual Registration")
    
    st.markdown("""
    Register as an individual to obtain a canonical unique ID for your personal data management.
    """)
    
    with st.form("individual_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            canonical_id = st.text_input(
                "Preferred Canonical ID*",
                placeholder="e.g., john-doe-001",
                help="Choose a unique identifier (letters, numbers, hyphens, underscores only)"
            )
            
            first_name = st.text_input(
                "First Name*",
                placeholder="John"
            )
            
            email = st.text_input(
                "Email Address*",
                placeholder="john.doe@company.com"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name*",
                placeholder="Doe"
            )
            
            phone = st.text_input(
                "Phone Number",
                placeholder="+1-555-123-4567"
            )
        
        # Terms and conditions
        st.markdown("### Terms and Conditions")
        agree_terms = st.checkbox(
            "I agree to the terms and conditions of the Data Registry Platform",
            help="You must agree to the terms to proceed with registration"
        )
        
        # Submit button
        if st.form_submit_button("Submit Individual Registration"):
            if not agree_terms:
                st.error("You must agree to the terms and conditions to proceed.")
                return
            
            # Collect form data
            form_data = {
                'canonical_id': canonical_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone if phone else None
            }
            
            # Process the registration
            process_individual_registration(form_data)

def organization_registration_form():
    """Organization registration form"""
    st.subheader("Organization Registration")
    
    st.markdown("""
    Register your organization to obtain a canonical unique ID for your business data management.
    """)
    
    with st.form("organization_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            canonical_id = st.text_input(
                "Preferred Canonical ID*",
                placeholder="e.g., acme-corp-001",
                help="Choose a unique identifier (letters, numbers, hyphens, underscores only)"
            )
            
            organization_name = st.text_input(
                "Organization Name*",
                placeholder="ACME Corporation"
            )
            
            organization_type = st.selectbox(
                "Organization Type*",
                options=validation_service.get_organization_types(),
                index=0
            )
            
            primary_contact_email = st.text_input(
                "Primary Contact Email*",
                placeholder="contact@acme.com"
            )
        
        with col2:
            phone = st.text_input(
                "Phone Number",
                placeholder="+1-555-123-4567"
            )
            
            website = st.text_input(
                "Website",
                placeholder="https://acme.com"
            )
            
            address = st.text_area(
                "Address",
                placeholder="123 Main St, City, State 12345",
                height=100
            )
        
        # Terms and conditions
        st.markdown("### Terms and Conditions")
        agree_terms = st.checkbox(
            "I agree to the terms and conditions of the Data Registry Platform",
            help="You must agree to the terms to proceed with registration"
        )
        
        # Submit button
        if st.form_submit_button("Submit Organization Registration"):
            if not agree_terms:
                st.error("You must agree to the terms and conditions to proceed.")
                return
            
            # Collect form data
            form_data = {
                'canonical_id': canonical_id,
                'organization_name': organization_name,
                'organization_type': organization_type,
                'primary_contact_email': primary_contact_email,
                'phone': phone if phone else None,
                'website': website if website else None,
                'address': address if address else None
            }
            
            # Process the registration
            process_organization_registration(form_data)

def process_individual_registration(form_data):
    """Process individual registration request"""
    try:
        # Validate and sanitize form data
        sanitized_data = validation_service.validate_and_sanitize_form_data(form_data)
        
        # Validate individual data
        is_valid, validation_errors = validation_service.validate_individual_data(sanitized_data)
        
        if not is_valid:
            st.error("Validation failed:")
            for error in validation_errors:
                st.error(f"- {error}")
            return
        
        # Check canonical ID uniqueness
        if not validation_service.check_canonical_id_uniqueness(sanitized_data['canonical_id'], 'individual'):
            st.error("The canonical ID you chose is already taken. Please choose a different one.")
            return
        
        # Validate email domain
        is_domain_valid, domain_message, domain_details = domain_validator.validate_email_domain(sanitized_data['email'])
        
        if not is_domain_valid:
            st.error(f"Email domain validation failed: {domain_message}")
            st.error("Please use a valid business email address.")
            return
        
        # Generate verification token
        verification_token = generate_secure_token()
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO individuals 
            (canonical_id, first_name, last_name, email, domain, phone, 
             verification_token, status, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            RETURNING individual_id
        """, (
            sanitized_data['canonical_id'],
            sanitized_data['first_name'],
            sanitized_data['last_name'],
            sanitized_data['email'],
            sanitized_data['email'].split('@')[1],
            sanitized_data['phone'],
            verification_token,
            {
                'registration_source': 'web_form',
                'domain_validation': domain_details,
                'submission_ip': 'web_interface'
            }
        ))
        
        individual_id = cursor.fetchone()[0]
        conn.commit()
        
        # Send verification email
        email_service.send_verification_email(
            sanitized_data['email'],
            verification_token,
            'Individual'
        )
        
        # Notify admin
        try:
            admin_email = get_admin_email('Individual Admin')
            if admin_email:
                email_service.send_admin_notification(
                    admin_email,
                    'Individual',
                    f"{sanitized_data['first_name']} {sanitized_data['last_name']}"
                )
        except Exception as e:
            st.warning(f"Admin notification failed: {e}")
        
        st.success(f"""
        ✅ **Registration Request Submitted Successfully!**
        
        Your individual registration request has been submitted and is now pending approval.
        
        **Next Steps:**
        1. Check your email for a verification link
        2. Click the verification link to confirm your email address
        3. Wait for admin approval (you'll receive an email notification)
        
        **Your Request Details:**
        - Canonical ID: {sanitized_data['canonical_id']}
        - Email: {sanitized_data['email']}
        - Request ID: {individual_id}
        """)
        
    except Exception as e:
        st.error(f"Registration failed: {e}")
    finally:
        if conn:
            conn.close()

def process_organization_registration(form_data):
    """Process organization registration request"""
    try:
        # Validate and sanitize form data
        sanitized_data = validation_service.validate_and_sanitize_form_data(form_data)
        
        # Validate organization data
        is_valid, validation_errors = validation_service.validate_organization_data(sanitized_data)
        
        if not is_valid:
            st.error("Validation failed:")
            for error in validation_errors:
                st.error(f"- {error}")
            return
        
        # Check canonical ID uniqueness
        if not validation_service.check_canonical_id_uniqueness(sanitized_data['canonical_id'], 'organization'):
            st.error("The canonical ID you chose is already taken. Please choose a different one.")
            return
        
        # Validate email domain
        is_domain_valid, domain_message, domain_details = domain_validator.validate_email_domain(sanitized_data['primary_contact_email'])
        
        if not is_domain_valid:
            st.error(f"Email domain validation failed: {domain_message}")
            st.error("Please use a valid business email address.")
            return
        
        # Generate verification token
        verification_token = generate_secure_token()
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO organizations 
            (canonical_id, organization_name, organization_type, primary_contact_email, 
             domain, phone, address, website, verification_token, status, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            RETURNING organization_id
        """, (
            sanitized_data['canonical_id'],
            sanitized_data['organization_name'],
            sanitized_data['organization_type'],
            sanitized_data['primary_contact_email'],
            sanitized_data['primary_contact_email'].split('@')[1],
            sanitized_data['phone'],
            sanitized_data['address'],
            sanitized_data['website'],
            verification_token,
            {
                'registration_source': 'web_form',
                'domain_validation': domain_details,
                'submission_ip': 'web_interface'
            }
        ))
        
        organization_id = cursor.fetchone()[0]
        conn.commit()
        
        # Send verification email
        email_service.send_verification_email(
            sanitized_data['primary_contact_email'],
            verification_token,
            'Organization'
        )
        
        # Notify admin
        try:
            admin_email = get_admin_email('Organization Admin')
            if admin_email:
                email_service.send_admin_notification(
                    admin_email,
                    'Organization',
                    sanitized_data['organization_name']
                )
        except Exception as e:
            st.warning(f"Admin notification failed: {e}")
        
        st.success(f"""
        ✅ **Registration Request Submitted Successfully!**
        
        Your organization registration request has been submitted and is now pending approval.
        
        **Next Steps:**
        1. Check your email for a verification link
        2. Click the verification link to confirm your email address
        3. Wait for admin approval (you'll receive an email notification)
        
        **Your Request Details:**
        - Canonical ID: {sanitized_data['canonical_id']}
        - Organization: {sanitized_data['organization_name']}
        - Email: {sanitized_data['primary_contact_email']}
        - Request ID: {organization_id}
        """)
        
    except Exception as e:
        st.error(f"Registration failed: {e}")
    finally:
        if conn:
            conn.close()

def check_registration_status():
    """Check registration status"""
    st.subheader("Check Registration Status")
    
    st.markdown("""
    Enter your canonical ID or email address to check the status of your registration request.
    """)
    
    with st.form("status_check"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_type = st.selectbox(
                "Search by:",
                options=["Canonical ID", "Email Address"],
                index=0
            )
        
        with col2:
            search_value = st.text_input(
                f"Enter {search_type}:",
                placeholder="e.g., john-doe-001 or john.doe@company.com"
            )
        
        if st.form_submit_button("Check Status"):
            if search_value:
                check_status(search_type, search_value)
            else:
                st.error("Please enter a value to search.")

def check_status(search_type, search_value):
    """Check the status of a registration"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in both individuals and organizations
        results = []
        
        # Search individuals
        if search_type == "Canonical ID":
            cursor.execute("""
                SELECT 'Individual' as type, canonical_id, first_name, last_name, 
                       email, status, request_date, approved_date, rejection_reason
                FROM individuals 
                WHERE canonical_id = %s
            """, (search_value,))
        else:
            cursor.execute("""
                SELECT 'Individual' as type, canonical_id, first_name, last_name, 
                       email, status, request_date, approved_date, rejection_reason
                FROM individuals 
                WHERE email = %s
            """, (search_value,))
        
        individual_results = cursor.fetchall()
        results.extend(individual_results)
        
        # Search organizations
        if search_type == "Canonical ID":
            cursor.execute("""
                SELECT 'Organization' as type, canonical_id, organization_name, '', 
                       primary_contact_email, status, request_date, approved_date, rejection_reason
                FROM organizations 
                WHERE canonical_id = %s
            """, (search_value,))
        else:
            cursor.execute("""
                SELECT 'Organization' as type, canonical_id, organization_name, '', 
                       primary_contact_email, status, request_date, approved_date, rejection_reason
                FROM organizations 
                WHERE primary_contact_email = %s
            """, (search_value,))
        
        organization_results = cursor.fetchall()
        results.extend(organization_results)
        
        if not results:
            st.info("No registration found with the provided information.")
            return
        
        # Display results
        for result in results:
            entity_type, canonical_id, name1, name2, email, status, request_date, approved_date, rejection_reason = result
            
            # Create status display
            status_color = {
                'pending': '🟡',
                'approved': '🟢',
                'rejected': '🔴'
            }.get(status, '⚪')
            
            entity_name = f"{name1} {name2}".strip() if name2 else name1
            
            st.markdown(f"""
            ### {status_color} {entity_type} Registration Status
            
            **Entity:** {entity_name}  
            **Canonical ID:** {canonical_id}  
            **Email:** {email}  
            **Status:** {status.upper()}  
            **Request Date:** {request_date}  
            """)
            
            if status == 'approved' and approved_date:
                st.markdown(f"**Approved Date:** {approved_date}")
                st.success("Your registration has been approved! You can now use your canonical ID to access our services.")
            
            elif status == 'rejected' and rejection_reason:
                st.markdown(f"**Rejection Reason:** {rejection_reason}")
                st.error("Your registration was rejected. Please review the reason and submit a new request if appropriate.")
            
            elif status == 'pending':
                st.info("Your registration is still pending admin approval. You will receive an email notification once it's processed.")
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"Error checking status: {e}")
    finally:
        if conn:
            conn.close()

def get_admin_email(admin_type):
    """Get admin email for notifications"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT email FROM admins 
            WHERE admin_type = %s AND is_active = TRUE
            LIMIT 1
        """, (admin_type,))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        st.error(f"Error getting admin email: {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
