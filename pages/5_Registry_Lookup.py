"""Registry Lookup Page"""
import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import get_db_connection
from services.domain_validator import DomainValidator
from utils.validation import ValidationService

# Initialize services
domain_validator = DomainValidator()
validation_service = ValidationService()

st.set_page_config(
    page_title="Registry Lookup",
    page_icon="🔍",
    layout="wide"
)

def main():
    st.title("🔍 Registry Lookup")
    st.markdown("---")
    
    st.markdown("""
    Search and lookup canonical unique IDs in the Data Registry Platform. 
    This public registry contains approved individuals and organizations.
    """)
    
    # Create tabs for different lookup types
    tab1, tab2, tab3, tab4 = st.tabs(["Search All", "Individual Lookup", "Organization Lookup", "Browse Registry"])
    
    with tab1:
        search_all_tab()
    
    with tab2:
        individual_lookup_tab()
    
    with tab3:
        organization_lookup_tab()
    
    with tab4:
        browse_registry_tab()

def search_all_tab():
    """Search across all entities"""
    st.subheader("Search All Entities")
    
    st.markdown("""
    Search for individuals and organizations by name, email, canonical ID, or domain.
    """)
    
    # Search form
    with st.form("search_all"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Enter name, email, canonical ID, or domain...",
                help="Search across all approved individuals and organizations"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            search_button = st.form_submit_button("🔍 Search", use_container_width=True)
    
    if search_button and search_query:
        perform_search(search_query)
    elif search_button and not search_query:
        st.error("Please enter a search query.")

def perform_search(search_query):
    """Perform search across all entities"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search individuals
        cursor.execute("""
            SELECT 'Individual' as entity_type, canonical_id, first_name, last_name, 
                   email, domain, phone, created_at, approved_date
            FROM individuals 
            WHERE status = 'approved' AND (
                first_name ILIKE %s OR last_name ILIKE %s OR 
                email ILIKE %s OR canonical_id ILIKE %s OR 
                domain ILIKE %s
            )
            ORDER BY first_name, last_name
            LIMIT 50
        """, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', 
              f'%{search_query}%', f'%{search_query}%'))
        
        individual_results = cursor.fetchall()
        
        # Search organizations
        cursor.execute("""
            SELECT 'Organization' as entity_type, canonical_id, organization_name, organization_type,
                   primary_contact_email, domain, phone, created_at, approved_date
            FROM organizations 
            WHERE status = 'approved' AND (
                organization_name ILIKE %s OR primary_contact_email ILIKE %s OR 
                canonical_id ILIKE %s OR domain ILIKE %s OR organization_type ILIKE %s
            )
            ORDER BY organization_name
            LIMIT 50
        """, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', 
              f'%{search_query}%', f'%{search_query}%'))
        
        organization_results = cursor.fetchall()
        
        # Display results
        total_results = len(individual_results) + len(organization_results)
        
        if total_results == 0:
            st.info(f"No results found for '{search_query}'.")
            return
        
        st.success(f"Found {total_results} results for '{search_query}'")
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Results", total_results)
        
        with col2:
            st.metric("Individuals", len(individual_results))
        
        with col3:
            st.metric("Organizations", len(organization_results))
        
        # Display individual results
        if individual_results:
            st.markdown("### 👤 Individual Results")
            
            for result in individual_results:
                entity_type, canonical_id, first_name, last_name, email, domain, phone, created_at, approved_date = result
                
                with st.expander(f"👤 {first_name} {last_name} ({canonical_id})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Canonical ID:** {canonical_id}")
                        st.write(f"**Name:** {first_name} {last_name}")
                        st.write(f"**Email:** {email}")
                        st.write(f"**Domain:** {domain}")
                    
                    with col2:
                        st.write(f"**Phone:** {phone if phone else 'Not provided'}")
                        st.write(f"**Registered:** {created_at}")
                        st.write(f"**Approved:** {approved_date}")
                        
                        # Copy canonical ID button
                        if st.button(f"Copy ID", key=f"copy_ind_{canonical_id}"):
                            st.code(canonical_id)
                            st.success("Canonical ID copied to display!")
        
        # Display organization results
        if organization_results:
            st.markdown("### 🏢 Organization Results")
            
            for result in organization_results:
                entity_type, canonical_id, org_name, org_type, email, domain, phone, created_at, approved_date = result
                
                with st.expander(f"🏢 {org_name} ({canonical_id})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Canonical ID:** {canonical_id}")
                        st.write(f"**Organization:** {org_name}")
                        st.write(f"**Type:** {org_type}")
                        st.write(f"**Email:** {email}")
                        st.write(f"**Domain:** {domain}")
                    
                    with col2:
                        st.write(f"**Phone:** {phone if phone else 'Not provided'}")
                        st.write(f"**Registered:** {created_at}")
                        st.write(f"**Approved:** {approved_date}")
                        
                        # Copy canonical ID button
                        if st.button(f"Copy ID", key=f"copy_org_{canonical_id}"):
                            st.code(canonical_id)
                            st.success("Canonical ID copied to display!")
        
        # Export results
        if total_results > 0:
            st.markdown("### Export Results")
            
            # Prepare data for export
            export_data = []
            
            for result in individual_results:
                entity_type, canonical_id, first_name, last_name, email, domain, phone, created_at, approved_date = result
                export_data.append({
                    'Entity Type': 'Individual',
                    'Canonical ID': canonical_id,
                    'Name': f"{first_name} {last_name}",
                    'Organization': '',
                    'Type': '',
                    'Email': email,
                    'Domain': domain,
                    'Phone': phone or '',
                    'Created': created_at,
                    'Approved': approved_date
                })
            
            for result in organization_results:
                entity_type, canonical_id, org_name, org_type, email, domain, phone, created_at, approved_date = result
                export_data.append({
                    'Entity Type': 'Organization',
                    'Canonical ID': canonical_id,
                    'Name': '',
                    'Organization': org_name,
                    'Type': org_type,
                    'Email': email,
                    'Domain': domain,
                    'Phone': phone or '',
                    'Created': created_at,
                    'Approved': approved_date
                })
            
            if export_data:
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Search Results (CSV)",
                    data=csv,
                    file_name=f"registry_search_{search_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"Search error: {e}")
    finally:
        if conn:
            conn.close()

def individual_lookup_tab():
    """Individual-specific lookup"""
    st.subheader("Individual Lookup")
    
    st.markdown("""
    Search specifically for approved individuals by canonical ID, name, or email.
    """)
    
    # Lookup form
    with st.form("individual_lookup"):
        col1, col2 = st.columns(2)
        
        with col1:
            lookup_type = st.selectbox(
                "Lookup by:",
                options=["Canonical ID", "Name", "Email", "Domain"],
                index=0
            )
        
        with col2:
            lookup_value = st.text_input(
                f"Enter {lookup_type}:",
                placeholder=f"e.g., {'john-doe-001' if lookup_type == 'Canonical ID' else 'John Doe' if lookup_type == 'Name' else 'john@company.com' if lookup_type == 'Email' else 'company.com'}"
            )
        
        if st.form_submit_button("🔍 Lookup Individual"):
            if lookup_value:
                lookup_individual(lookup_type, lookup_value)
            else:
                st.error("Please enter a value to lookup.")

def lookup_individual(lookup_type, lookup_value):
    """Lookup individual by specified criteria"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on lookup type
        if lookup_type == "Canonical ID":
            query = """
                SELECT canonical_id, first_name, last_name, email, domain, phone, 
                       created_at, approved_date
                FROM individuals 
                WHERE status = 'approved' AND canonical_id = %s
            """
            params = (lookup_value,)
        
        elif lookup_type == "Name":
            query = """
                SELECT canonical_id, first_name, last_name, email, domain, phone, 
                       created_at, approved_date
                FROM individuals 
                WHERE status = 'approved' AND (
                    first_name ILIKE %s OR last_name ILIKE %s OR 
                    CONCAT(first_name, ' ', last_name) ILIKE %s
                )
                ORDER BY first_name, last_name
            """
            params = (f'%{lookup_value}%', f'%{lookup_value}%', f'%{lookup_value}%')
        
        elif lookup_type == "Email":
            query = """
                SELECT canonical_id, first_name, last_name, email, domain, phone, 
                       created_at, approved_date
                FROM individuals 
                WHERE status = 'approved' AND email ILIKE %s
            """
            params = (f'%{lookup_value}%',)
        
        else:  # Domain
            query = """
                SELECT canonical_id, first_name, last_name, email, domain, phone, 
                       created_at, approved_date
                FROM individuals 
                WHERE status = 'approved' AND domain ILIKE %s
                ORDER BY first_name, last_name
            """
            params = (f'%{lookup_value}%',)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            st.info(f"No individuals found for {lookup_type.lower()}: '{lookup_value}'")
            return
        
        st.success(f"Found {len(results)} individual(s)")
        
        # Display results
        for result in results:
            canonical_id, first_name, last_name, email, domain, phone, created_at, approved_date = result
            
            with st.expander(f"👤 {first_name} {last_name} ({canonical_id})", expanded=len(results) == 1):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Canonical ID:** {canonical_id}")
                    st.write(f"**Full Name:** {first_name} {last_name}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Domain:** {domain}")
                
                with col2:
                    st.write(f"**Phone:** {phone if phone else 'Not provided'}")
                    st.write(f"**Registered:** {created_at}")
                    st.write(f"**Approved:** {approved_date}")
                
                # Action buttons
                col3, col4 = st.columns(2)
                
                with col3:
                    if st.button(f"Copy Canonical ID", key=f"copy_individual_{canonical_id}"):
                        st.code(canonical_id)
                        st.success("Canonical ID copied to display!")
                
                with col4:
                    # Domain info
                    if st.button(f"Domain Info", key=f"domain_info_{canonical_id}"):
                        domain_info = domain_validator.get_domain_info(domain)
                        st.json(domain_info)
    
    except Exception as e:
        st.error(f"Lookup error: {e}")
    finally:
        if conn:
            conn.close()

def organization_lookup_tab():
    """Organization-specific lookup"""
    st.subheader("Organization Lookup")
    
    st.markdown("""
    Search specifically for approved organizations by canonical ID, name, type, or email.
    """)
    
    # Lookup form
    with st.form("organization_lookup"):
        col1, col2 = st.columns(2)
        
        with col1:
            lookup_type = st.selectbox(
                "Lookup by:",
                options=["Canonical ID", "Organization Name", "Organization Type", "Email", "Domain"],
                index=0
            )
        
        with col2:
            if lookup_type == "Organization Type":
                lookup_value = st.selectbox(
                    "Select Organization Type:",
                    options=validation_service.get_organization_types()
                )
            else:
                lookup_value = st.text_input(
                    f"Enter {lookup_type}:",
                    placeholder=f"e.g., {'acme-corp-001' if lookup_type == 'Canonical ID' else 'ACME Corp' if lookup_type == 'Organization Name' else 'contact@acme.com' if lookup_type == 'Email' else 'acme.com'}"
                )
        
        if st.form_submit_button("🔍 Lookup Organization"):
            if lookup_value:
                lookup_organization(lookup_type, lookup_value)
            else:
                st.error("Please enter a value to lookup.")

def lookup_organization(lookup_type, lookup_value):
    """Lookup organization by specified criteria"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on lookup type
        if lookup_type == "Canonical ID":
            query = """
                SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                       domain, phone, address, website, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved' AND canonical_id = %s
            """
            params = (lookup_value,)
        
        elif lookup_type == "Organization Name":
            query = """
                SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                       domain, phone, address, website, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved' AND organization_name ILIKE %s
                ORDER BY organization_name
            """
            params = (f'%{lookup_value}%',)
        
        elif lookup_type == "Organization Type":
            query = """
                SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                       domain, phone, address, website, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved' AND organization_type = %s
                ORDER BY organization_name
            """
            params = (lookup_value,)
        
        elif lookup_type == "Email":
            query = """
                SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                       domain, phone, address, website, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved' AND primary_contact_email ILIKE %s
            """
            params = (f'%{lookup_value}%',)
        
        else:  # Domain
            query = """
                SELECT canonical_id, organization_name, organization_type, primary_contact_email, 
                       domain, phone, address, website, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved' AND domain ILIKE %s
                ORDER BY organization_name
            """
            params = (f'%{lookup_value}%',)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            st.info(f"No organizations found for {lookup_type.lower()}: '{lookup_value}'")
            return
        
        st.success(f"Found {len(results)} organization(s)")
        
        # Display results
        for result in results:
            canonical_id, org_name, org_type, email, domain, phone, address, website, created_at, approved_date = result
            
            with st.expander(f"🏢 {org_name} ({canonical_id})", expanded=len(results) == 1):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Canonical ID:** {canonical_id}")
                    st.write(f"**Organization:** {org_name}")
                    st.write(f"**Type:** {org_type}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Domain:** {domain}")
                
                with col2:
                    st.write(f"**Phone:** {phone if phone else 'Not provided'}")
                    st.write(f"**Website:** {website if website else 'Not provided'}")
                    st.write(f"**Address:** {address if address else 'Not provided'}")
                    st.write(f"**Registered:** {created_at}")
                    st.write(f"**Approved:** {approved_date}")
                
                # Action buttons
                col3, col4 = st.columns(2)
                
                with col3:
                    if st.button(f"Copy Canonical ID", key=f"copy_org_{canonical_id}"):
                        st.code(canonical_id)
                        st.success("Canonical ID copied to display!")
                
                with col4:
                    # Domain info
                    if st.button(f"Domain Info", key=f"domain_info_org_{canonical_id}"):
                        domain_info = domain_validator.get_domain_info(domain)
                        st.json(domain_info)
    
    except Exception as e:
        st.error(f"Lookup error: {e}")
    finally:
        if conn:
            conn.close()

def browse_registry_tab():
    """Browse the complete registry"""
    st.subheader("Browse Registry")
    
    st.markdown("""
    Browse the complete registry of approved individuals and organizations.
    """)
    
    # Filter options
    with st.form("browse_filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            entity_filter = st.selectbox(
                "Entity Type:",
                options=["All", "Individuals", "Organizations"],
                index=0
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by:",
                options=["Name", "Canonical ID", "Approval Date", "Domain"],
                index=0
            )
        
        with col3:
            limit = st.number_input(
                "Results Limit:",
                min_value=10,
                max_value=500,
                value=100,
                step=10
            )
        
        if st.form_submit_button("🔍 Browse Registry"):
            browse_registry(entity_filter, sort_by, limit)

def browse_registry(entity_filter, sort_by, limit):
    """Browse registry with filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = []
        
        # Get individuals
        if entity_filter in ["All", "Individuals"]:
            order_clause = {
                "Name": "ORDER BY first_name, last_name",
                "Canonical ID": "ORDER BY canonical_id",
                "Approval Date": "ORDER BY approved_date DESC",
                "Domain": "ORDER BY domain"
            }[sort_by]
            
            cursor.execute(f"""
                SELECT 'Individual' as entity_type, canonical_id, first_name, last_name, 
                       email, domain, phone, created_at, approved_date
                FROM individuals 
                WHERE status = 'approved'
                {order_clause}
                LIMIT %s
            """, (limit if entity_filter == "Individuals" else limit // 2,))
            
            individual_results = cursor.fetchall()
            results.extend(individual_results)
        
        # Get organizations
        if entity_filter in ["All", "Organizations"]:
            order_clause = {
                "Name": "ORDER BY organization_name",
                "Canonical ID": "ORDER BY canonical_id",
                "Approval Date": "ORDER BY approved_date DESC",
                "Domain": "ORDER BY domain"
            }[sort_by]
            
            cursor.execute(f"""
                SELECT 'Organization' as entity_type, canonical_id, organization_name, organization_type,
                       primary_contact_email, domain, phone, created_at, approved_date
                FROM organizations 
                WHERE status = 'approved'
                {order_clause}
                LIMIT %s
            """, (limit if entity_filter == "Organizations" else limit // 2,))
            
            organization_results = cursor.fetchall()
            results.extend(organization_results)
        
        if not results:
            st.info("No entities found in the registry.")
            return
        
        # Display summary
        individual_count = len([r for r in results if r[0] == 'Individual'])
        organization_count = len([r for r in results if r[0] == 'Organization'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Shown", len(results))
        
        with col2:
            st.metric("Individuals", individual_count)
        
        with col3:
            st.metric("Organizations", organization_count)
        
        # Display results in a table format
        st.markdown("### Registry Entries")
        
        # Create DataFrame for display
        display_data = []
        
        for result in results:
            if result[0] == 'Individual':
                entity_type, canonical_id, first_name, last_name, email, domain, phone, created_at, approved_date = result
                display_data.append({
                    'Type': '👤 Individual',
                    'Canonical ID': canonical_id,
                    'Name': f"{first_name} {last_name}",
                    'Organization': '',
                    'Email': email,
                    'Domain': domain,
                    'Phone': phone or '',
                    'Approved': approved_date.strftime('%Y-%m-%d') if approved_date else ''
                })
            else:
                entity_type, canonical_id, org_name, org_type, email, domain, phone, created_at, approved_date = result
                display_data.append({
                    'Type': '🏢 Organization',
                    'Canonical ID': canonical_id,
                    'Name': '',
                    'Organization': f"{org_name} ({org_type})",
                    'Email': email,
                    'Domain': domain,
                    'Phone': phone or '',
                    'Approved': approved_date.strftime('%Y-%m-%d') if approved_date else ''
                })
        
        # Display as dataframe
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("Export Registry Data"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Registry Data (CSV)",
                data=csv,
                file_name=f"registry_browse_{entity_filter.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Browse error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
