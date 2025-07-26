"""Organization Admin Dashboard"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import get_db_connection, get_pending_registrations, approve_registration, reject_registration, log_audit_action
from services.email_service import EmailService
from utils.validation import ValidationService

# Initialize services
email_service = EmailService()
validation_service = ValidationService()

st.set_page_config(
    page_title="Organization Admin Dashboard",
    page_icon="🏢",
    layout="wide"
)

def check_admin_access():
    """Check if user has organization admin access"""
    if not st.session_state.get('authenticated'):
        st.error("Please log in to access this page.")
        st.stop()
    
    if st.session_state.get('admin_type') != 'Organization Admin':
        st.error("Access denied. This page is for Organization Admins only.")
        st.stop()

def main():
    check_admin_access()
    
    st.title("🏢 Organization Admin Dashboard")
    st.markdown("---")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Pending Requests", "Approved Organizations", "Rejected Requests", "Bulk Actions"])
    
    with tab1:
        pending_requests_tab()
    
    with tab2:
        approved_organizations_tab()
    
    with tab3:
        rejected_requests_tab()
    
    with tab4:
        bulk_actions_tab()

def pending_requests_tab():
    """Display pending organization registration requests"""
    st.subheader("Pending Organization Registrations")
    
    try:
        pending_requests = get_pending_registrations('organization')
        
        if not pending_requests:
            st.info("No pending organization registration requests.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(pending_requests, columns=[
            'ID', 'Canonical ID', 'Organization Name', 'Organization Type', 'Primary Contact Email',
            'Domain', 'Phone', 'Address', 'Website', 'Status', 'Request Date', 'Approved Date',
            'Approved By', 'Rejection Reason', 'Verification Token', 'Is Verified', 'Metadata',
            'Created At', 'Updated At'
        ])
        
        # Display summary
        st.metric("Pending Requests", len(df))
        
        # Display requests
        for idx, request in df.iterrows():
            with st.expander(f"Request #{request['ID']} - {request['Organization Name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Canonical ID:** {request['Canonical ID']}")
                    st.write(f"**Organization:** {request['Organization Name']}")
                    st.write(f"**Type:** {request['Organization Type']}")
                    st.write(f"**Email:** {request['Primary Contact Email']}")
                    st.write(f"**Domain:** {request['Domain']}")
                    st.write(f"**Phone:** {request['Phone'] or 'Not provided'}")
                
                with col2:
                    st.write(f"**Website:** {request['Website'] or 'Not provided'}")
                    st.write(f"**Address:** {request['Address'] or 'Not provided'}")
                    st.write(f"**Request Date:** {request['Request Date']}")
                    st.write(f"**Verification Status:** {'Verified' if request['Is Verified'] else 'Pending'}")
                
                # Action buttons
                col3, col4 = st.columns(2)
                
                with col3:
                    if st.button(f"Approve", key=f"approve_{request['ID']}"):
                        approve_organization_request(request['ID'], request)
                
                with col4:
                    if st.button(f"Reject", key=f"reject_{request['ID']}"):
                        show_reject_form(request['ID'], request)
        
        # Bulk actions
        st.subheader("Bulk Actions")
        
        selected_requests = st.multiselect(
            "Select requests for bulk actions:",
            options=df['ID'].tolist(),
            format_func=lambda x: f"#{x} - {df[df['ID'] == x]['Organization Name'].iloc[0]}"
        )
        
        if selected_requests:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Bulk Approve Selected"):
                    bulk_approve_requests(selected_requests, df)
            
            with col2:
                if st.button("Bulk Reject Selected"):
                    st.session_state['bulk_reject_ids'] = selected_requests
                    st.session_state['show_bulk_reject_form'] = True
        
        # Show bulk reject form if needed
        if st.session_state.get('show_bulk_reject_form'):
            show_bulk_reject_form()
    
    except Exception as e:
        st.error(f"Error loading pending requests: {e}")

def approve_organization_request(request_id, request_data):
    """Approve an organization registration request"""
    try:
        # Get admin ID
        admin_id = get_admin_id()
        
        # Approve the request
        approve_registration('organization', request_id, admin_id)
        
        # Log the action
        log_audit_action('organization', request_id, 'approved', admin_id, 
                        {'canonical_id': request_data['Canonical ID']})
        
        # Send approval email
        email_service.send_approval_notification(
            request_data['Primary Contact Email'],
            'Organization',
            request_data['Canonical ID']
        )
        
        st.success(f"Organization registration approved for {request_data['Organization Name']}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error approving request: {e}")

def show_reject_form(request_id, request_data):
    """Show form to reject a request with reason"""
    with st.form(f"reject_form_{request_id}"):
        st.subheader(f"Reject Request - {request_data['Organization Name']}")
        
        reason = st.text_area(
            "Rejection Reason:",
            placeholder="Please provide a detailed reason for rejection...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Confirm Rejection"):
                if reason.strip():
                    reject_organization_request(request_id, request_data, reason)
                else:
                    st.error("Please provide a reason for rejection.")
        
        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()

def reject_organization_request(request_id, request_data, reason):
    """Reject an organization registration request"""
    try:
        # Get admin ID
        admin_id = get_admin_id()
        
        # Reject the request
        reject_registration('organization', request_id, admin_id, reason)
        
        # Log the action
        log_audit_action('organization', request_id, 'rejected', admin_id, 
                        {'canonical_id': request_data['Canonical ID'], 'reason': reason})
        
        # Send rejection email
        email_service.send_rejection_notification(
            request_data['Primary Contact Email'],
            'Organization',
            reason
        )
        
        st.success(f"Organization registration rejected for {request_data['Organization Name']}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error rejecting request: {e}")

def bulk_approve_requests(request_ids, df):
    """Bulk approve multiple requests"""
    try:
        admin_id = get_admin_id()
        approved_count = 0
        
        for request_id in request_ids:
            request_data = df[df['ID'] == request_id].iloc[0]
            
            # Approve the request
            approve_registration('organization', request_id, admin_id)
            
            # Log the action
            log_audit_action('organization', request_id, 'bulk_approved', admin_id, 
                            {'canonical_id': request_data['Canonical ID']})
            
            # Send approval email
            email_service.send_approval_notification(
                request_data['Primary Contact Email'],
                'Organization',
                request_data['Canonical ID']
            )
            
            approved_count += 1
        
        st.success(f"Successfully approved {approved_count} organization registrations")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error in bulk approval: {e}")

def show_bulk_reject_form():
    """Show form for bulk rejection"""
    with st.form("bulk_reject_form"):
        st.subheader("Bulk Reject Requests")
        
        reason = st.text_area(
            "Rejection Reason for all selected requests:",
            placeholder="Please provide a detailed reason for rejection...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Confirm Bulk Rejection"):
                if reason.strip():
                    bulk_reject_requests(st.session_state['bulk_reject_ids'], reason)
                else:
                    st.error("Please provide a reason for rejection.")
        
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state['show_bulk_reject_form'] = False
                st.rerun()

def bulk_reject_requests(request_ids, reason):
    """Bulk reject multiple requests"""
    try:
        admin_id = get_admin_id()
        rejected_count = 0
        
        # Get request data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for request_id in request_ids:
            cursor.execute("""
                SELECT primary_contact_email, organization_name, canonical_id 
                FROM organizations WHERE organization_id = %s
            """, (request_id,))
            
            result = cursor.fetchone()
            if result:
                email, org_name, canonical_id = result
                
                # Reject the request
                reject_registration('organization', request_id, admin_id, reason)
                
                # Log the action
                log_audit_action('organization', request_id, 'bulk_rejected', admin_id, 
                                {'canonical_id': canonical_id, 'reason': reason})
                
                # Send rejection email
                email_service.send_rejection_notification(email, 'Organization', reason)
                
                rejected_count += 1
        
        st.success(f"Successfully rejected {rejected_count} organization registrations")
        st.session_state['show_bulk_reject_form'] = False
        st.rerun()
        
    except Exception as e:
        st.error(f"Error in bulk rejection: {e}")
    finally:
        if conn:
            conn.close()

def approved_organizations_tab():
    """Display approved organizations"""
    st.subheader("Approved Organizations")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT organization_id, canonical_id, organization_name, organization_type, 
                   primary_contact_email, domain, phone, address, website, 
                   approved_date, created_at
            FROM organizations 
            WHERE status = 'approved'
            ORDER BY approved_date DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            st.info("No approved organizations found.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=[
            'ID', 'Canonical ID', 'Organization Name', 'Organization Type', 'Primary Contact Email',
            'Domain', 'Phone', 'Address', 'Website', 'Approved Date', 'Created At'
        ])
        
        st.metric("Total Approved", len(df))
        
        # Search functionality
        search_term = st.text_input("Search approved organizations:", placeholder="Search by name, email, or canonical ID")
        
        if search_term:
            mask = (
                df['Organization Name'].str.contains(search_term, case=False, na=False) |
                df['Primary Contact Email'].str.contains(search_term, case=False, na=False) |
                df['Canonical ID'].str.contains(search_term, case=False, na=False) |
                df['Organization Type'].str.contains(search_term, case=False, na=False)
            )
            df = df[mask]
        
        # Display results
        for idx, row in df.iterrows():
            with st.expander(f"{row['Organization Name']} ({row['Canonical ID']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Canonical ID:** {row['Canonical ID']}")
                    st.write(f"**Organization:** {row['Organization Name']}")
                    st.write(f"**Type:** {row['Organization Type']}")
                    st.write(f"**Email:** {row['Primary Contact Email']}")
                    st.write(f"**Domain:** {row['Domain']}")
                
                with col2:
                    st.write(f"**Phone:** {row['Phone'] or 'Not provided'}")
                    st.write(f"**Website:** {row['Website'] or 'Not provided'}")
                    st.write(f"**Address:** {row['Address'] or 'Not provided'}")
                    st.write(f"**Approved Date:** {row['Approved Date']}")
        
        # Export functionality
        if st.button("Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"approved_organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    except Exception as e:
        st.error(f"Error loading approved organizations: {e}")
    finally:
        if conn:
            conn.close()

def rejected_requests_tab():
    """Display rejected requests"""
    st.subheader("Rejected Organization Requests")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT organization_id, canonical_id, organization_name, organization_type,
                   primary_contact_email, rejection_reason, request_date, updated_at
            FROM organizations 
            WHERE status = 'rejected'
            ORDER BY updated_at DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            st.info("No rejected requests found.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=[
            'ID', 'Canonical ID', 'Organization Name', 'Organization Type', 'Primary Contact Email',
            'Rejection Reason', 'Request Date', 'Rejection Date'
        ])
        
        st.metric("Total Rejected", len(df))
        
        # Display results
        for idx, row in df.iterrows():
            with st.expander(f"Rejected #{row['ID']} - {row['Organization Name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Canonical ID:** {row['Canonical ID']}")
                    st.write(f"**Organization:** {row['Organization Name']}")
                    st.write(f"**Type:** {row['Organization Type']}")
                    st.write(f"**Email:** {row['Primary Contact Email']}")
                
                with col2:
                    st.write(f"**Request Date:** {row['Request Date']}")
                    st.write(f"**Rejection Date:** {row['Rejection Date']}")
                
                st.write(f"**Rejection Reason:** {row['Rejection Reason']}")
        
    except Exception as e:
        st.error(f"Error loading rejected requests: {e}")
    finally:
        if conn:
            conn.close()

def bulk_actions_tab():
    """Bulk actions and data management"""
    st.subheader("Bulk Actions & Data Management")
    
    # File upload for bulk operations
    uploaded_file = st.file_uploader(
        "Upload CSV file for bulk organization registration:",
        type=['csv'],
        help="Upload a CSV file with columns: canonical_id, organization_name, organization_type, primary_contact_email, phone, address, website"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.subheader("Preview of uploaded data:")
            st.dataframe(df.head(10))
            
            # Validate the data
            required_columns = ['canonical_id', 'organization_name', 'organization_type', 'primary_contact_email']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {missing_columns}")
                return
            
            # Validate each record
            data_list = df.to_dict('records')
            validation_results = validation_service.validate_bulk_data(data_list, 'organization')
            
            st.subheader("Validation Results:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Valid Records", len(validation_results['valid_records']))
            
            with col2:
                st.metric("Invalid Records", len(validation_results['invalid_records']))
            
            with col3:
                st.metric("Duplicates", len(validation_results['duplicate_canonical_ids']))
            
            # Show invalid records
            if validation_results['invalid_records']:
                st.subheader("Invalid Records:")
                for record in validation_results['invalid_records']:
                    with st.expander(f"Row {record['row']} - Errors: {len(record['errors'])}"):
                        st.write("**Data:**", record['data'])
                        st.write("**Errors:**")
                        for error in record['errors']:
                            st.write(f"- {error}")
            
            # Process valid records
            if validation_results['valid_records']:
                if st.button("Process Valid Records"):
                    process_bulk_organizations(validation_results['valid_records'])
        
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
    
    # Data export options
    st.subheader("Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export All Approved Organizations"):
            export_approved_organizations()
    
    with col2:
        if st.button("Export Pending Requests"):
            export_pending_requests()

def process_bulk_organizations(valid_records):
    """Process bulk organization registrations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = get_admin_id()
        
        processed_count = 0
        
        for record in valid_records:
            # Insert the record
            cursor.execute("""
                INSERT INTO organizations 
                (canonical_id, organization_name, organization_type, primary_contact_email, 
                 domain, phone, address, website, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (
                record['canonical_id'],
                record['organization_name'],
                record['organization_type'],
                record['primary_contact_email'],
                record['primary_contact_email'].split('@')[1],
                record.get('phone'),
                record.get('address'),
                record.get('website')
            ))
            
            # Log the action
            organization_id = cursor.lastrowid
            log_audit_action('organization', organization_id, 'bulk_imported', admin_id, record)
            
            processed_count += 1
        
        conn.commit()
        st.success(f"Successfully processed {processed_count} organization registrations")
        
    except Exception as e:
        st.error(f"Error processing bulk registrations: {e}")
    finally:
        if conn:
            conn.close()

def export_approved_organizations():
    """Export approved organizations to CSV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                   domain, phone, address, website, approved_date, created_at
            FROM organizations 
            WHERE status = 'approved'
            ORDER BY approved_date DESC
        """)
        
        results = cursor.fetchall()
        
        if results:
            df = pd.DataFrame(results, columns=[
                'Canonical ID', 'Organization Name', 'Organization Type', 'Primary Contact Email',
                'Domain', 'Phone', 'Address', 'Website', 'Approved Date', 'Created At'
            ])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Approved Organizations CSV",
                data=csv,
                file_name=f"approved_organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No approved organizations to export.")
            
    except Exception as e:
        st.error(f"Error exporting data: {e}")
    finally:
        if conn:
            conn.close()

def export_pending_requests():
    """Export pending requests to CSV"""
    try:
        pending_requests = get_pending_registrations('organization')
        
        if pending_requests:
            df = pd.DataFrame(pending_requests, columns=[
                'ID', 'Canonical ID', 'Organization Name', 'Organization Type', 'Primary Contact Email',
                'Domain', 'Phone', 'Address', 'Website', 'Status', 'Request Date', 'Approved Date',
                'Approved By', 'Rejection Reason', 'Verification Token', 'Is Verified', 'Metadata',
                'Created At', 'Updated At'
            ])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Pending Requests CSV",
                data=csv,
                file_name=f"pending_organizations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No pending requests to export.")
            
    except Exception as e:
        st.error(f"Error exporting data: {e}")

def get_admin_id():
    """Get admin ID from session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT admin_id FROM admins 
            WHERE username = %s AND admin_type = 'Organization Admin'
        """, (st.session_state.admin_username,))
        
        result = cursor.fetchone()
        return result[0] if result else None
        
    except Exception as e:
        st.error(f"Error getting admin ID: {e}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
