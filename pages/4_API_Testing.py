"""API Testing Dashboard"""
import streamlit as st
import json
from datetime import datetime
from database.connection import get_db_connection
from services.api_service import APIService
from utils.validation import ValidationService

# Initialize services
api_service = APIService()
validation_service = ValidationService()

st.set_page_config(
    page_title="API Testing Dashboard",
    page_icon="🔧",
    layout="wide"
)

def check_admin_access():
    """Check if user has admin access"""
    if not st.session_state.get('authenticated'):
        st.error("Please log in to access this page.")
        st.stop()
    
    if st.session_state.get('admin_type') not in ['Individual Admin', 'Organization Admin']:
        st.error("Access denied. This page is for admins only.")
        st.stop()

def main():
    check_admin_access()
    
    st.title("🔧 API Testing Dashboard")
    st.markdown("---")
    
    st.markdown("""
    Test the API endpoints and manage API keys for client applications.
    This dashboard allows you to test all available API functionality.
    """)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["API Key Management", "Test Individual Lookup", "Test Organization Lookup", "Test Search"])
    
    with tab1:
        api_key_management_tab()
    
    with tab2:
        test_individual_lookup_tab()
    
    with tab3:
        test_organization_lookup_tab()
    
    with tab4:
        test_search_tab()

def api_key_management_tab():
    """API Key Management"""
    st.subheader("API Key Management")
    
    # Create new API key
    st.markdown("### Create New API Key")
    
    with st.form("create_api_key"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input(
                "Client Name*",
                placeholder="e.g., ACME Corp Integration"
            )
            
            client_email = st.text_input(
                "Client Email*",
                placeholder="dev@acme.com"
            )
        
        with col2:
            rate_limit = st.number_input(
                "Rate Limit (requests per hour)",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )
        
        if st.form_submit_button("Create API Key"):
            if client_name and client_email:
                create_api_key(client_name, client_email, rate_limit)
            else:
                st.error("Please fill in all required fields.")
    
    # Display existing API keys
    st.markdown("### Existing API Keys")
    display_api_keys()

def create_api_key(client_name, client_email, rate_limit):
    """Create a new API key"""
    try:
        result = api_service.create_api_key(client_name, client_email, rate_limit)
        
        if result.get('status') == 201:
            st.success(f"API Key created successfully!")
            
            # Display the new API key (only shown once)
            st.markdown("### ⚠️ New API Key Created")
            st.markdown("**Save this API key now - it will not be shown again!**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.code(result['api_key'], language='text')
            
            with col2:
                st.download_button(
                    label="Download API Key",
                    data=f"API_KEY={result['api_key']}\nCLIENT_NAME={client_name}\nRATE_LIMIT={rate_limit}",
                    file_name=f"api_key_{client_name.replace(' ', '_').lower()}.txt",
                    mime="text/plain"
                )
            
            st.markdown(f"""
            **API Key Details:**
            - Client Name: {client_name}
            - Client Email: {client_email}
            - Rate Limit: {rate_limit} requests/hour
            - Key ID: {result['key_id']}
            """)
            
        else:
            st.error(f"Failed to create API key: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"Error creating API key: {e}")

def display_api_keys():
    """Display existing API keys"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key_id, client_name, client_email, is_active, rate_limit, 
                   created_at, last_used, expires_at
            FROM api_keys 
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        
        if not results:
            st.info("No API keys found.")
            return
        
        for result in results:
            key_id, client_name, client_email, is_active, rate_limit, created_at, last_used, expires_at = result
            
            status_color = "🟢" if is_active else "🔴"
            status_text = "Active" if is_active else "Inactive"
            
            with st.expander(f"{status_color} {client_name} - {status_text}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Key ID:** {key_id}")
                    st.write(f"**Client Name:** {client_name}")
                    st.write(f"**Client Email:** {client_email}")
                    st.write(f"**Status:** {status_text}")
                
                with col2:
                    st.write(f"**Rate Limit:** {rate_limit} requests/hour")
                    st.write(f"**Created:** {created_at}")
                    st.write(f"**Last Used:** {last_used if last_used else 'Never'}")
                    st.write(f"**Expires:** {expires_at if expires_at else 'Never'}")
                
                # Action buttons
                col3, col4 = st.columns(2)
                
                with col3:
                    if is_active:
                        if st.button(f"Deactivate", key=f"deactivate_{key_id}"):
                            update_api_key_status(key_id, False)
                    else:
                        if st.button(f"Activate", key=f"activate_{key_id}"):
                            update_api_key_status(key_id, True)
                
                with col4:
                    if st.button(f"Delete", key=f"delete_{key_id}"):
                        delete_api_key(key_id)
    
    except Exception as e:
        st.error(f"Error loading API keys: {e}")
    finally:
        if conn:
            conn.close()

def update_api_key_status(key_id, is_active):
    """Update API key status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys 
            SET is_active = %s 
            WHERE key_id = %s
        """, (is_active, key_id))
        
        conn.commit()
        
        action = "activated" if is_active else "deactivated"
        st.success(f"API key {action} successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error updating API key: {e}")
    finally:
        if conn:
            conn.close()

def delete_api_key(key_id):
    """Delete API key"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM api_keys WHERE key_id = %s", (key_id,))
        conn.commit()
        
        st.success("API key deleted successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error deleting API key: {e}")
    finally:
        if conn:
            conn.close()

def test_individual_lookup_tab():
    """Test individual lookup API"""
    st.subheader("Test Individual Lookup API")
    
    st.markdown("""
    Test the individual lookup API endpoint. This simulates how client applications 
    would retrieve individual information using a canonical ID.
    """)
    
    with st.form("test_individual_lookup"):
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "API Key*",
                placeholder="Enter a valid API key",
                type="password"
            )
        
        with col2:
            canonical_id = st.text_input(
                "Canonical ID*",
                placeholder="e.g., john-doe-001"
            )
        
        if st.form_submit_button("Test Individual Lookup"):
            if api_key and canonical_id:
                test_individual_lookup(api_key, canonical_id)
            else:
                st.error("Please provide both API key and canonical ID.")

def test_individual_lookup(api_key, canonical_id):
    """Test individual lookup API call"""
    try:
        result = api_service.lookup_individual(api_key, canonical_id)
        
        st.markdown("### API Response")
        
        # Display status
        status_color = "🟢" if result.get('status') == 200 else "🔴"
        st.markdown(f"{status_color} **Status Code:** {result.get('status', 'Unknown')}")
        
        # Display response
        if result.get('status') == 200:
            st.success("Individual found successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Canonical ID:** {result.get('canonical_id')}")
                st.write(f"**Name:** {result.get('first_name')} {result.get('last_name')}")
                st.write(f"**Email:** {result.get('email')}")
                st.write(f"**Domain:** {result.get('domain')}")
            
            with col2:
                st.write(f"**Phone:** {result.get('phone', 'Not provided')}")
                st.write(f"**Status:** {result.get('status')}")
                st.write(f"**Created:** {result.get('created_at', 'Unknown')}")
                st.write(f"**Updated:** {result.get('updated_at', 'Unknown')}")
        
        elif result.get('status') == 404:
            st.warning("Individual not found.")
        
        elif result.get('status') == 401:
            st.error("Invalid API key.")
        
        elif result.get('status') == 429:
            st.error("Rate limit exceeded.")
        
        else:
            st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        # Show full JSON response
        st.markdown("### Full JSON Response")
        st.json(result)
        
    except Exception as e:
        st.error(f"Error testing API: {e}")

def test_organization_lookup_tab():
    """Test organization lookup API"""
    st.subheader("Test Organization Lookup API")
    
    st.markdown("""
    Test the organization lookup API endpoint. This simulates how client applications 
    would retrieve organization information using a canonical ID.
    """)
    
    with st.form("test_organization_lookup"):
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "API Key*",
                placeholder="Enter a valid API key",
                type="password"
            )
        
        with col2:
            canonical_id = st.text_input(
                "Canonical ID*",
                placeholder="e.g., acme-corp-001"
            )
        
        if st.form_submit_button("Test Organization Lookup"):
            if api_key and canonical_id:
                test_organization_lookup(api_key, canonical_id)
            else:
                st.error("Please provide both API key and canonical ID.")

def test_organization_lookup(api_key, canonical_id):
    """Test organization lookup API call"""
    try:
        result = api_service.lookup_organization(api_key, canonical_id)
        
        st.markdown("### API Response")
        
        # Display status
        status_color = "🟢" if result.get('status') == 200 else "🔴"
        st.markdown(f"{status_color} **Status Code:** {result.get('status', 'Unknown')}")
        
        # Display response
        if result.get('status') == 200:
            st.success("Organization found successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Canonical ID:** {result.get('canonical_id')}")
                st.write(f"**Organization:** {result.get('organization_name')}")
                st.write(f"**Type:** {result.get('organization_type')}")
                st.write(f"**Email:** {result.get('primary_contact_email')}")
                st.write(f"**Domain:** {result.get('domain')}")
            
            with col2:
                st.write(f"**Phone:** {result.get('phone', 'Not provided')}")
                st.write(f"**Website:** {result.get('website', 'Not provided')}")
                st.write(f"**Address:** {result.get('address', 'Not provided')}")
                st.write(f"**Created:** {result.get('created_at', 'Unknown')}")
                st.write(f"**Updated:** {result.get('updated_at', 'Unknown')}")
        
        elif result.get('status') == 404:
            st.warning("Organization not found.")
        
        elif result.get('status') == 401:
            st.error("Invalid API key.")
        
        elif result.get('status') == 429:
            st.error("Rate limit exceeded.")
        
        else:
            st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        # Show full JSON response
        st.markdown("### Full JSON Response")
        st.json(result)
        
    except Exception as e:
        st.error(f"Error testing API: {e}")

def test_search_tab():
    """Test search API"""
    st.subheader("Test Search API")
    
    st.markdown("""
    Test the search API endpoint. This simulates how client applications 
    would search for individuals and organizations.
    """)
    
    with st.form("test_search"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            api_key = st.text_input(
                "API Key*",
                placeholder="Enter a valid API key",
                type="password"
            )
        
        with col2:
            search_query = st.text_input(
                "Search Query*",
                placeholder="e.g., john, acme, @company.com"
            )
        
        with col3:
            entity_type = st.selectbox(
                "Entity Type",
                options=["both", "individual", "organization"],
                index=0
            )
        
        if st.form_submit_button("Test Search"):
            if api_key and search_query:
                test_search(api_key, search_query, entity_type)
            else:
                st.error("Please provide both API key and search query.")

def test_search(api_key, search_query, entity_type):
    """Test search API call"""
    try:
        result = api_service.search_entities(api_key, search_query, entity_type)
        
        st.markdown("### API Response")
        
        # Display status
        status_color = "🟢" if result.get('status') == 200 else "🔴"
        st.markdown(f"{status_color} **Status Code:** {result.get('status', 'Unknown')}")
        
        # Display response
        if result.get('status') == 200:
            st.success("Search completed successfully!")
            
            results_data = result.get('results', {})
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Individuals", result.get('total_individuals', 0))
            
            with col2:
                st.metric("Total Organizations", result.get('total_organizations', 0))
            
            with col3:
                total_results = result.get('total_individuals', 0) + result.get('total_organizations', 0)
                st.metric("Total Results", total_results)
            
            # Display individual results
            if results_data.get('individuals'):
                st.markdown("#### Individual Results")
                for individual in results_data['individuals']:
                    with st.expander(f"👤 {individual['first_name']} {individual['last_name']} ({individual['canonical_id']})"):
                        st.write(f"**Email:** {individual['email']}")
                        st.write(f"**Domain:** {individual['domain']}")
            
            # Display organization results
            if results_data.get('organizations'):
                st.markdown("#### Organization Results")
                for organization in results_data['organizations']:
                    with st.expander(f"🏢 {organization['organization_name']} ({organization['canonical_id']})"):
                        st.write(f"**Type:** {organization['organization_type']}")
                        st.write(f"**Email:** {organization['primary_contact_email']}")
                        st.write(f"**Domain:** {organization['domain']}")
            
            if not results_data.get('individuals') and not results_data.get('organizations'):
                st.info("No results found for your search query.")
        
        elif result.get('status') == 401:
            st.error("Invalid API key.")
        
        elif result.get('status') == 429:
            st.error("Rate limit exceeded.")
        
        else:
            st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        # Show full JSON response
        st.markdown("### Full JSON Response")
        st.json(result)
        
    except Exception as e:
        st.error(f"Error testing API: {e}")

if __name__ == "__main__":
    main()
