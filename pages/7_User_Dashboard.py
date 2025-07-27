"""User Dashboard for registered individuals and organizations"""
import streamlit as st
from services.user_auth import user_auth
from services.user_analytics import user_analytics
from database.connection import get_db_connection
from utils.static_files import inject_custom_css, display_logo
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

# Inject custom CSS
inject_custom_css()

# Display logo
display_logo()

st.title("👤 User Dashboard")
st.markdown("---")

def login_form():
    """Display user login form"""
    st.markdown("### Access Your Data Registry Account")
    st.markdown("Enter your Canonical ID and registered email address to access your dashboard.")
    
    with st.form("user_login_form"):
        canonical_id = st.text_input("Canonical ID", placeholder="e.g., IND-12345 or ORG-67890")
        email = st.text_input("Email Address", placeholder="your.email@domain.com")
        
        submitted = st.form_submit_button("Access Dashboard")
        
        if submitted:
            if canonical_id and email:
                if user_auth.authenticate_user(canonical_id, email):
                    st.success("Login successful! Redirecting to your dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid credentials or account not found. Please check your Canonical ID and email address.")
            else:
                st.error("Please enter both Canonical ID and email address.")

def user_dashboard():
    """Display the user dashboard"""
    user_data = user_auth.get_user_data()
    user_type = user_auth.get_user_type()
    
    if not user_data:
        st.error("Session expired. Please login again.")
        user_auth.logout_user()
        st.rerun()
        return
    
    # Header with user info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if user_type == "individual":
            st.markdown(f"## Welcome, {user_data['first_name']} {user_data['last_name']}")
            st.markdown(f"**Canonical ID:** {user_data['canonical_id']}")
        else:
            st.markdown(f"## Welcome, {user_data['organization_name']}")
            st.markdown(f"**Canonical ID:** {user_data['canonical_id']}")
    
    with col2:
        if st.button("Logout"):
            user_auth.logout_user()
            st.rerun()
    
    st.markdown("---")
    
    # Get comprehensive dashboard data
    dashboard_data = user_analytics.get_user_dashboard_data(user_data['canonical_id'], user_type)
    analytics = dashboard_data.get('analytics', {})
    
    # Display key metrics
    st.markdown("### 📊 Account Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Profile Completeness", 
            f"{analytics.get('profile_completeness', 0)}%",
            help="Percentage of profile fields completed"
        )
    
    with col2:
        days_registered = 0
        if analytics.get('registration_date'):
            days_registered = (datetime.now() - analytics['registration_date']).days
        st.metric(
            "Days Registered", 
            days_registered,
            help="Number of days since registration"
        )
    
    with col3:
        st.metric(
            "API Keys", 
            analytics.get('api_keys_count', 0),
            help="Number of API keys generated for your account"
        )
    
    with col4:
        status_color = "🟢" if user_data.get('status') == 'approved' else "🟡"
        st.metric(
            "Account Status", 
            f"{status_color} {user_data.get('status', 'Unknown').title()}",
            help="Current account status"
        )
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Profile Information", "Data Analytics", "Available Actions", "Account History", "Recommendations"])
    
    with tab1:
        display_profile_information(user_data, user_type)
    
    with tab2:
        display_data_analytics(user_data, analytics)
    
    with tab3:
        display_available_actions(user_data, user_type)
    
    with tab4:
        display_account_history(user_data, user_type, dashboard_data.get('activity_history', []))
    
    with tab5:
        display_recommendations(dashboard_data.get('recommendations', []))

def display_profile_information(user_data, user_type):
    """Display user profile information"""
    st.markdown("### 👤 Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if user_type == "individual":
            st.info(f"**Name:** {user_data['first_name']} {user_data['last_name']}")
            st.info(f"**Birth Date:** {user_data.get('birth_date', 'Not provided')}")
        else:
            st.info(f"**Organization:** {user_data['organization_name']}")
            st.info(f"**Industry:** {user_data.get('industry', 'Not provided')}")
            st.info(f"**Website:** {user_data.get('website', 'Not provided')}")
        
        st.info(f"**Email:** {user_data['email']}")
        st.info(f"**Phone:** {user_data.get('phone', 'Not provided')}")
    
    with col2:
        st.info(f"**Address:** {user_data.get('address', 'Not provided')}")
        st.info(f"**Registration Date:** {user_data.get('created_at', 'Unknown')}")
        st.info(f"**Approval Date:** {user_data.get('approved_at', 'Not approved yet')}")
        st.info(f"**Status:** {user_data.get('status', 'Unknown').title()}")
    
    # Profile update form
    with st.expander("Update Profile Information"):
        st.markdown("**Note:** Profile updates require admin approval.")
        
        with st.form("profile_update_form"):
            if user_type == "individual":
                new_phone = st.text_input("Phone", value=user_data.get('phone', ''))
                new_address = st.text_area("Address", value=user_data.get('address', ''))
            else:
                new_phone = st.text_input("Phone", value=user_data.get('phone', ''))
                new_address = st.text_area("Address", value=user_data.get('address', ''))
                new_website = st.text_input("Website", value=user_data.get('website', ''))
            
            if st.form_submit_button("Request Profile Update"):
                st.info("Profile update requests will be implemented in the next version.")

def display_data_analytics(user_data, analytics):
    """Display data analytics and visualizations"""
    st.markdown("### 📈 Data Analytics")
    
    # Profile completeness chart
    completeness = analytics.get('profile_completeness', 0)
    fig_completeness = go.Figure(data=[
        go.Pie(
            labels=['Completed', 'Missing'],
            values=[completeness, 100 - completeness],
            hole=0.6,
            marker_colors=['#1f77b4', '#d62728']
        )
    ])
    fig_completeness.update_layout(
        title="Profile Completeness",
        showlegend=True,
        height=400
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(fig_completeness, use_container_width=True)
    
    with col2:
        st.markdown("#### Registration Timeline")
        
        if analytics.get('registration_date') and analytics.get('approval_date'):
            reg_date = analytics['registration_date']
            app_date = analytics['approval_date']
            
            timeline_data = pd.DataFrame({
                'Event': ['Registration', 'Approval'],
                'Date': [reg_date, app_date],
                'Status': ['Submitted', 'Approved']
            })
            
            fig_timeline = px.timeline(
                timeline_data,
                x_start='Date',
                x_end='Date',
                y='Event',
                color='Status',
                title="Account Timeline"
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("Timeline data not available")
    
    # Usage statistics (placeholder for future implementation)
    st.markdown("#### Usage Statistics")
    st.info("Detailed usage statistics will be available once data integration features are implemented.")

def display_available_actions(user_data, user_type):
    """Display available actions for the user"""
    st.markdown("### 🛠️ Available Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Data Management")
        
        if st.button("🔍 Search Registry", help="Search for other registered entities"):
            st.info("Redirecting to Registry Lookup...")
            # This would redirect to the registry lookup page
        
        if st.button("📊 Download My Data", help="Download your registered data"):
            # Generate comprehensive data export using analytics service
            export_data = user_analytics.get_user_data_export(user_data['canonical_id'], user_type)
            
            if export_data:
                st.download_button(
                    "📥 Download Complete Data Export",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"{user_data['canonical_id']}_complete_export_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                
                # Also offer CSV format for profile data
                if dashboard_data.get('profile_info'):
                    profile_df = pd.DataFrame([dashboard_data['profile_info']])
                    csv_data = profile_df.to_csv(index=False)
                    st.download_button(
                        "📊 Download Profile CSV",
                        data=csv_data,
                        file_name=f"{user_data['canonical_id']}_profile.csv",
                        mime="text/csv"
                    )
            else:
                st.error("Unable to generate data export")
        
        if st.button("🔗 Generate API Key", help="Generate API key for data access"):
            st.info("API key generation will be implemented in the next version.")
    
    with col2:
        st.markdown("#### Account Actions")
        
        if st.button("📧 Update Email Preferences", help="Manage email notification settings"):
            st.info("Email preferences management will be implemented in the next version.")
        
        if st.button("🔒 Privacy Settings", help="Manage data privacy settings"):
            st.info("Privacy settings will be implemented in the next version.")
        
        if st.button("❓ Request Support", help="Contact support team"):
            with st.form("support_request_form"):
                subject = st.selectbox(
                    "Subject",
                    ["Profile Update", "Data Correction", "API Access", "Technical Issue", "Other"]
                )
                message = st.text_area("Message", placeholder="Describe your request...")
                
                if st.form_submit_button("Send Request"):
                    if message:
                        st.success("Support request submitted successfully. We'll contact you via email.")
                    else:
                        st.error("Please enter a message.")

def display_account_history(user_data, user_type, activity_history):
    """Display account history and activities"""
    st.markdown("### 📋 Account History")
    
    # Activity history from analytics service
    st.markdown("#### Activity Timeline")
    
    if activity_history:
        # Convert to DataFrame for better display
        history_df_data = []
        for activity in activity_history:
            history_df_data.append({
                'Date': activity.get('date', '').strftime('%Y-%m-%d %H:%M') if activity.get('date') else 'Unknown',
                'Event': activity.get('event', 'Unknown'),
                'Description': activity.get('description', ''),
                'Type': activity.get('type', 'general').title()
            })
        
        df_history = pd.DataFrame(history_df_data)
        st.dataframe(df_history, use_container_width=True)
        
        # Activity timeline chart
        if len(history_df_data) > 1:
            try:
                # Create timeline visualization
                fig_timeline = px.scatter(
                    df_history, 
                    x='Date', 
                    y='Event',
                    color='Type',
                    hover_data=['Description'],
                    title="Activity Timeline"
                )
                fig_timeline.update_layout(height=400)
                st.plotly_chart(fig_timeline, use_container_width=True)
            except Exception as e:
                st.info("Timeline visualization not available")
    else:
        st.info("No activity history available")
    
    # Future enhancements info
    st.markdown("#### Future Activity Tracking")
    st.info("Enhanced activity logging will include:")
    st.markdown("""
    - Profile updates and changes
    - API key usage statistics
    - Data access and download requests
    - Support ticket interactions
    - Privacy setting modifications
    - Integration with external systems
    """)

def display_recommendations(recommendations):
    """Display personalized recommendations for the user"""
    st.markdown("### 💡 Personalized Recommendations")
    
    if not recommendations:
        st.info("No recommendations available at this time.")
        return
    
    # Group recommendations by priority
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']
    
    # Display high priority recommendations first
    if high_priority:
        st.markdown("#### 🔴 High Priority")
        for rec in high_priority:
            with st.container():
                st.markdown(f"**{rec['title']}**")
                st.markdown(rec['description'])
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"💡 {rec['action']}")
                with col2:
                    if st.button(f"Act", key=f"high_{rec['type']}"):
                        st.info(f"Feature coming soon: {rec['action']}")
                st.markdown("---")
    
    # Medium priority recommendations
    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority:
            with st.expander(rec['title']):
                st.markdown(rec['description'])
                st.caption(f"💡 Suggested action: {rec['action']}")
                if st.button(f"Take Action", key=f"med_{rec['type']}"):
                    st.info(f"Feature coming soon: {rec['action']}")
    
    # Low priority recommendations
    if low_priority:
        st.markdown("#### 🟢 Low Priority")
        for rec in low_priority:
            with st.expander(rec['title']):
                st.markdown(rec['description'])
                st.caption(f"💡 Suggested action: {rec['action']}")

def main():
    """Main function for user dashboard"""
    if user_auth.is_user_authenticated():
        user_dashboard()
    else:
        login_form()

if __name__ == "__main__":
    main()