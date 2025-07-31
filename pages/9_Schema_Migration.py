"""Schema Migration Page - Transition to User-Centric Data Model"""
import streamlit as st
from services.migration_service import migration_service
from database.canonical_id_system import canonical_id_service
from database.connection import get_db_connection
from utils.static_files import inject_custom_css
from utils.canonical_id_examples import generate_examples, explain_format
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Schema Migration",
    page_icon="🔄",
    layout="wide"
)

inject_custom_css()

def check_admin_access():
    """Check if user has admin access"""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.error("Please login as an admin to access this page")
        st.stop()

def preview_canonical_id_changes():
    """Preview how canonical IDs will change"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT canonical_id, first_name, last_name, email, phone
            FROM individuals 
            LIMIT 10
        """)
        
        individuals = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if individuals:
            preview_data = []
            for individual in individuals:
                old_id = individual[0]
                if individual[4]:  # has phone
                    new_id = canonical_id_service.generate_canonical_id(
                        individual[1], individual[2], individual[4], individual[3]
                    )
                else:
                    new_id = f"{old_id} (no phone - keeping old ID)"
                
                preview_data.append({
                    'Old Canonical ID': old_id,
                    'New Canonical ID': new_id,
                    'Name': f"{individual[1]} {individual[2]}",
                    'Email': individual[3],
                    'Phone': individual[4] or 'Not provided'
                })
            
            df = pd.DataFrame(preview_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No individuals found to preview")
            
    except Exception as e:
        st.error(f"Error generating preview: {e}")

def main():
    check_admin_access()
    
    st.markdown("""
    <div class="header-container">
        <h1>🔄 Schema Migration</h1>
        <p>Transition to User-Centric Canonical ID System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    .migration-info {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #ffc107;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda, #a7e3a7);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Migration Information
    st.markdown("""
    <div class="migration-info">
        <h3>🎯 New Canonical ID System</h3>
        <p>The new system creates user-centric canonical IDs with IP-address-like format:</p>
        <ul>
            <li><strong>Format:</strong> FirstInitial.LastName.Last4OfPhone.FullEmail</li>
            <li><strong>Example:</strong> J.Smith.6738.jsmith@hotmail.com (like 192.168.1.1 for networks)</li>
            <li><strong>Segments:</strong> 4 components for specific identity, with email providing full contact context</li>
            <li><strong>Benefits:</strong> Human-readable, hierarchical, includes direct contact information</li>
            <li>Each user can have multiple emails, phones, and organization relationships</li>
            <li>Only one primary email and phone per user</li>
            <li>Organizations linked to users through relationships table</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Warning about migration
    st.markdown("""
    <div class="warning-box">
        <h3>⚠️ Important Migration Notes</h3>
        <ul>
            <li>This migration will create new database tables alongside existing ones</li>
            <li>Original data will be preserved during migration</li>
            <li>New canonical IDs will be generated based on name, phone, and email</li>
            <li>Users without phone numbers will keep their existing canonical IDs</li>
            <li>Please backup your database before proceeding</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different migration steps
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Preview Changes", "🗃️ Create Schema", "🔄 Migrate Data", "✅ Validation"])
    
    with tab1:
        st.subheader("Preview Canonical ID Changes")
        st.markdown("See how the new IP-like canonical ID system will work:")
        
        # Show format explanation
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**New Format Examples:**")
            examples = generate_examples()
            for example in examples[:3]:
                st.code(f"{example['name']} → {example['expected_id']}")
        
        with col2:
            st.markdown("**Format Structure:**")
            format_info = explain_format()
            st.code("FirstInitial.LastName.Last4Phone.FullEmail")
            st.caption("Like IP addresses: readable, hierarchical, parseable")
        
        st.markdown("---")
        
        if st.button("Generate Preview from Current Data", type="primary"):
            with st.spinner("Generating preview..."):
                preview_canonical_id_changes()
    
    with tab2:
        st.subheader("Create New Database Schema")
        st.markdown("Create the new user-centric database tables:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create New Schema", type="primary"):
                with st.spinner("Creating new database schema..."):
                    success = migration_service.create_new_tables()
                    if success:
                        st.success("New schema created successfully!")
                    else:
                        st.error("Failed to create new schema")
        
        with col2:
            st.info("This will create new tables without affecting existing data")
    
    with tab3:
        st.subheader("Migrate Existing Data")
        st.markdown("Transfer data from old tables to new structure:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Migrate Individuals to Users", type="primary"):
                with st.spinner("Migrating individuals..."):
                    success = migration_service.migrate_individuals_to_users()
                    if success:
                        st.success("Individuals migrated successfully!")
                    else:
                        st.error("Failed to migrate individuals")
        
        with col2:
            if st.button("Migrate Organizations", type="secondary"):
                with st.spinner("Migrating organizations..."):
                    success = migration_service.migrate_organizations()
                    if success:
                        st.success("Organizations migrated successfully!")
                    else:
                        st.error("Failed to migrate organizations")
        
        st.markdown("---")
        
        # Full migration option
        if st.button("🚀 Run Complete Migration", type="primary", use_container_width=True):
            with st.spinner("Running complete migration..."):
                success = migration_service.run_full_migration()
                if success:
                    st.balloons()
                    st.markdown("""
                    <div class="success-box">
                        <h3>🎉 Migration Completed Successfully!</h3>
                        <p>Your database has been successfully migrated to the new user-centric schema.</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab4:
        st.subheader("Migration Validation")
        st.markdown("Validate the migration results:")
        
        if st.button("Run Validation", type="primary"):
            with st.spinner("Validating migration..."):
                validation_results = migration_service.validate_migration()
                
                if validation_results:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Individuals → Users",
                            validation_results['new_users'],
                            validation_results['new_users'] - validation_results['old_individuals']
                        )
                    
                    with col2:
                        st.metric(
                            "Organizations",
                            validation_results['new_organizations'],
                            validation_results['new_organizations'] - validation_results['old_organizations']
                        )
                    
                    with col3:
                        st.metric("Primary Emails", validation_results['primary_emails'])
                    
                    with col4:
                        st.metric("Primary Phones", validation_results['primary_phones'])
        
        # Display migration log
        if st.button("Show Migration Log"):
            log_entries = migration_service.get_migration_log()
            if log_entries:
                st.subheader("Migration Log")
                for entry in log_entries:
                    if "✅" in entry:
                        st.success(entry)
                    elif "⚠️" in entry:
                        st.warning(entry)
                    elif "❌" in entry:
                        st.error(entry)
                    else:
                        st.info(entry)
            else:
                st.info("No migration log available")
    
    # Current System Status
    st.markdown("---")
    st.subheader("📋 Current System Status")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if new tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('users', 'user_emails', 'user_phones', 'user_organizations')
        """)
        new_tables = [row[0] for row in cursor.fetchall()]
        
        # Get record counts
        cursor.execute("SELECT COUNT(*) FROM individuals")
        old_individuals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM organizations")
        old_organizations = cursor.fetchone()[0]
        
        new_users = 0
        new_orgs = 0
        if 'users' in new_tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            new_users = cursor.fetchone()[0]
        
        if 'organizations' in new_tables:
            cursor.execute("SELECT COUNT(*) FROM organizations WHERE organization_canonical_id LIKE 'ORG-%'")
            new_orgs = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Individuals", old_individuals)
        
        with col2:
            st.metric("Current Organizations", old_organizations)
        
        with col3:
            st.metric("Migrated Users", new_users)
        
        with col4:
            st.metric("Migrated Organizations", new_orgs)
        
        # Schema status
        if new_tables:
            st.success(f"New schema exists with tables: {', '.join(new_tables)}")
        else:
            st.info("New schema not yet created")
            
    except Exception as e:
        st.error(f"Error checking system status: {e}")

if __name__ == "__main__":
    main()