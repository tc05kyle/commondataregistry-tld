"""Gravatar Integration Management Page"""
import streamlit as st
from services.gravatar_service import gravatar_service
from database.connection import get_db_connection
from utils.static_files import inject_custom_css
import pandas as pd
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Gravatar Integration",
    page_icon="🌐",
    layout="wide"
)

inject_custom_css()

def check_admin_access():
    """Check if user has admin access"""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.error("Please login as an admin to access this page")
        st.stop()

def display_gravatar_info():
    """Display information about Gravatar integration"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 2rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h3>🌐 Gravatar Profile Synchronization</h3>
        <p>Gravatar (Globally Recognized Avatars) provides "Profiles as a Service" - allowing you to automatically populate user profiles with rich data including avatars, bios, social links, work history, and more using just an email address.</p>
        
        <h4>Benefits of Gravatar Integration:</h4>
        <ul>
            <li><strong>Rich User Profiles:</strong> Automatically populate user data from their Gravatar profile</li>
            <li><strong>Consistent Identity:</strong> Users maintain the same avatar and profile across all Gravatar-enabled sites</li>
            <li><strong>No Manual Entry:</strong> Reduce user onboarding friction with auto-populated profiles</li>
            <li><strong>Real-time Sync:</strong> Profiles stay current when users update their Gravatar</li>
            <li><strong>Social Verification:</strong> Access verified social media accounts and contact information</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def setup_gravatar_api():
    """Setup Gravatar API configuration"""
    st.subheader("🔑 API Configuration")
    
    api_configured = gravatar_service.is_configured()
    
    if api_configured:
        st.success("✅ Gravatar API key is configured")
        
        # Test connection
        if st.button("Test API Connection"):
            with st.spinner("Testing Gravatar API connection..."):
                test_result = gravatar_service.test_connection()
                
                if test_result['success']:
                    st.success(test_result['message'])
                    if test_result['test_profile_found']:
                        st.info("Test profile successfully retrieved")
                    else:
                        st.warning("API connection works but test profile not found")
                else:
                    st.error(test_result['message'])
    else:
        st.warning("⚠️ Gravatar API key not configured")
        
        with st.expander("How to Get Gravatar API Key"):
            st.markdown("""
            1. **Create Gravatar Account**: Go to [gravatar.com](https://gravatar.com) and sign up
            2. **Access Developer Dashboard**: Visit [gravatar.com/developers](https://gravatar.com/developers)
            3. **Create Application**: Click "Create New Application" and fill in details
            4. **Generate API Key**: Copy your API key
            5. **Add to Environment**: Add `GRAVATAR_API_KEY=your_key_here` to your environment variables
            
            **Rate Limits:**
            - Without API Key: 100 requests/hour (limited data)
            - With API Key: 1,000 requests/hour (full profile data)
            """)
        
        # Manual API key input for testing
        st.markdown("---")
        st.subheader("Manual API Key Entry (for testing)")
        manual_key = st.text_input("Enter Gravatar API Key", type="password", key="manual_gravatar_key")
        
        if manual_key and st.button("Test Manual Key"):
            # Temporarily set the API key for testing
            gravatar_service.api_key = manual_key
            gravatar_service.session.headers.update({'Authorization': f'Bearer {manual_key}'})
            
            test_result = gravatar_service.test_connection()
            if test_result['success']:
                st.success("✅ API key works! Add it to your environment variables.")
            else:
                st.error("❌ API key test failed. Please check the key.")

def individual_profile_sync():
    """Sync individual user profile with Gravatar"""
    st.subheader("👤 Individual Profile Sync")
    
    # Search for user
    col1, col2 = st.columns(2)
    
    with col1:
        search_by = st.selectbox("Search by", ["Canonical ID", "Email"])
    
    with col2:
        if search_by == "Canonical ID":
            search_value = st.text_input("Enter Canonical ID", placeholder="e.g., JSmith1234DOM")
        else:
            search_value = st.text_input("Enter Email", placeholder="user@example.com")
    
    if search_value and st.button("Find User"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check which schema to use
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'")
            has_new_schema = cursor.fetchone() is not None
            
            if has_new_schema:
                if search_by == "Canonical ID":
                    cursor.execute("""
                        SELECT u.canonical_id, u.first_name, u.last_name, ue.email, u.status
                        FROM users u
                        JOIN user_emails ue ON u.user_id = ue.user_id
                        WHERE u.canonical_id = %s AND ue.is_primary = TRUE
                    """, (search_value,))
                else:
                    cursor.execute("""
                        SELECT u.canonical_id, u.first_name, u.last_name, ue.email, u.status
                        FROM users u
                        JOIN user_emails ue ON u.user_id = ue.user_id
                        WHERE ue.email = %s AND ue.is_primary = TRUE
                    """, (search_value,))
            else:
                if search_by == "Canonical ID":
                    cursor.execute("""
                        SELECT canonical_id, first_name, last_name, email, status
                        FROM individuals WHERE canonical_id = %s
                    """, (search_value,))
                else:
                    cursor.execute("""
                        SELECT canonical_id, first_name, last_name, email, status
                        FROM individuals WHERE email = %s
                    """, (search_value,))
            
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                canonical_id, first_name, last_name, email, status = user
                
                st.success(f"Found user: {first_name} {last_name} ({canonical_id})")
                
                # Display current sync status
                sync_status = gravatar_service.get_sync_status(canonical_id)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Current User Info:**")
                    st.write(f"Name: {first_name} {last_name}")
                    st.write(f"Email: {email}")
                    st.write(f"Status: {status}")
                    st.write(f"Canonical ID: {canonical_id}")
                
                with col2:
                    st.markdown("**Gravatar Sync Status:**")
                    if sync_status['has_sync']:
                        st.success("✅ Previously synced with Gravatar")
                        st.write(f"Last Sync: {sync_status['last_sync']}")
                        if sync_status['avatar_url']:
                            st.image(sync_status['avatar_url'], width=100, caption="Gravatar Avatar")
                    else:
                        st.info("ℹ️ No Gravatar sync found")
                
                # Sync button
                st.markdown("---")
                if st.button("🔄 Sync with Gravatar", type="primary"):
                    with st.spinner("Syncing with Gravatar..."):
                        result = gravatar_service.sync_user_profile(canonical_id, email)
                        
                        if result['success']:
                            st.success(result['message'])
                            
                            # Display synced data
                            if result['gravatar_data']:
                                st.subheader("📊 Synced Gravatar Data")
                                
                                gravatar_data = result['gravatar_data']
                                
                                # Basic info
                                if 'display_name' in gravatar_data:
                                    st.write(f"**Display Name:** {gravatar_data['display_name']}")
                                
                                if 'bio' in gravatar_data:
                                    st.write(f"**Bio:** {gravatar_data['bio']}")
                                
                                if 'location' in gravatar_data:
                                    st.write(f"**Location:** {gravatar_data['location']}")
                                
                                # Avatar
                                if result['avatar_url']:
                                    st.image(result['avatar_url'], width=150, caption="Gravatar Avatar")
                                
                                # Social accounts
                                if 'social_accounts' in gravatar_data and gravatar_data['social_accounts']:
                                    st.subheader("🔗 Social Accounts")
                                    for account in gravatar_data['social_accounts']:
                                        verified_icon = "✅" if account.get('verified') else "❓"
                                        st.write(f"{verified_icon} **{account['service']}:** {account.get('username', account.get('url', 'N/A'))}")
                        else:
                            st.error(result['message'])
                            if result['gravatar_data']:
                                st.info("Some data was retrieved but sync failed")
            else:
                st.error("User not found")
                
        except Exception as e:
            st.error(f"Error searching for user: {e}")

def bulk_sync_operations():
    """Bulk sync operations for multiple users"""
    st.subheader("📦 Bulk Sync Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sync_limit = st.number_input("Number of users to sync", min_value=1, max_value=100, value=10)
    
    with col2:
        st.info(f"This will sync up to {sync_limit} users who haven't been synced in the last 7 days")
    
    if st.button("🚀 Start Bulk Sync", type="primary"):
        if not gravatar_service.is_configured():
            st.error("Gravatar API key not configured. Please set up API access first.")
            return
        
        with st.spinner(f"Syncing {sync_limit} user profiles..."):
            results = gravatar_service.bulk_sync_users(sync_limit)
            
            # Display results
            st.subheader("📊 Bulk Sync Results")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Processed", results['total_processed'])
            
            with col2:
                st.metric("Successful Syncs", results['successful_syncs'])
            
            with col3:
                st.metric("No Gravatar Profile", results['no_gravatar_profile'])
            
            with col4:
                st.metric("Failed Syncs", results['failed_syncs'])
            
            # Detailed results
            if 'results' in results and results['results']:
                st.subheader("📋 Detailed Results")
                
                results_df = pd.DataFrame(results['results'])
                
                # Color code the results
                def color_success(val):
                    if val:
                        return 'background-color: #d4edda; color: #155724'
                    else:
                        return 'background-color: #f8d7da; color: #721c24'
                
                styled_df = results_df.style.applymap(color_success, subset=['success'])
                st.dataframe(styled_df, use_container_width=True)

def sync_statistics():
    """Display Gravatar sync statistics"""
    st.subheader("📈 Sync Statistics")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check which schema to use
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'users'")
        has_new_schema = cursor.fetchone() is not None
        
        if has_new_schema:
            # Get stats from new schema
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN metadata->>'gravatar_sync' IS NOT NULL THEN 1 END) as synced_users,
                    COUNT(CASE WHEN metadata->'gravatar_sync'->>'last_sync' > (NOW() - INTERVAL '30 days')::text THEN 1 END) as recently_synced
                FROM users
                WHERE status = 'approved'
            """)
        else:
            # Get stats from old schema
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN metadata->>'gravatar_sync' IS NOT NULL THEN 1 END) as synced_users,
                    COUNT(CASE WHEN metadata->'gravatar_sync'->>'last_sync' > (NOW() - INTERVAL '30 days')::text THEN 1 END) as recently_synced
                FROM individuals
                WHERE status = 'approved'
            """)
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if stats:
            total_users, synced_users, recently_synced = stats
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Approved Users", total_users)
            
            with col2:
                sync_percentage = (synced_users / total_users * 100) if total_users > 0 else 0
                st.metric("Users Synced with Gravatar", synced_users, f"{sync_percentage:.1f}%")
            
            with col3:
                recent_percentage = (recently_synced / total_users * 100) if total_users > 0 else 0
                st.metric("Recently Synced (30 days)", recently_synced, f"{recent_percentage:.1f}%")
    
    except Exception as e:
        st.error(f"Error fetching sync statistics: {e}")

def main():
    check_admin_access()
    
    st.markdown("""
    <div class="header-container">
        <h1>🌐 Gravatar Integration</h1>
        <p>Sync user profiles with Gravatar for rich identity data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display Gravatar information
    display_gravatar_info()
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 Setup", "👤 Individual Sync", "📦 Bulk Sync", "📈 Statistics"])
    
    with tab1:
        setup_gravatar_api()
    
    with tab2:
        individual_profile_sync()
    
    with tab3:
        bulk_sync_operations()
    
    with tab4:
        sync_statistics()

if __name__ == "__main__":
    main()