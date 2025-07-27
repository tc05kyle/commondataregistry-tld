"""User Dashboard for registered individuals and organizations"""
import streamlit as st
from services.user_auth import user_auth
from services.user_analytics import user_analytics
from services.animated_dashboard import animated_dashboard
from database.connection import get_db_connection
from utils.static_files import inject_custom_css, display_logo
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import time

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
    """Display the animated user dashboard"""
    user_data = user_auth.get_user_data()
    user_type = user_auth.get_user_type()
    
    if not user_data:
        st.error("Session expired. Please login again.")
        user_auth.logout_user()
        st.rerun()
        return
    
    # Get comprehensive dashboard data
    dashboard_data = user_analytics.get_user_dashboard_data(user_data['canonical_id'], user_type)
    analytics = dashboard_data.get('analytics', {})
    
    # Render animated welcome header
    greeting = animated_dashboard.render_welcome_header(user_data, user_type)
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown(f"**Logged in as:**")
        if user_type == "individual":
            st.markdown(f"{user_data['first_name']} {user_data['last_name']}")
        else:
            st.markdown(f"{user_data['organization_name']}")
        
        st.markdown(f"**ID:** {user_data['canonical_id']}")
        
        if st.button("🚪 Logout", use_container_width=True):
            user_auth.logout_user()
            st.rerun()
    
    # Render animated metrics
    animated_dashboard.render_animated_metrics(analytics, user_type)
    
    # Progress rings section
    st.markdown("---")
    animated_dashboard.render_progress_rings(analytics)
    
    # Timeline and insights
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        animated_dashboard.render_insights_timeline(user_data, analytics)
    
    with col2:
        animated_dashboard.render_personalized_insights(user_data, analytics, user_type)
    
    # Advanced visualizations
    st.markdown("---")
    
    # Tabs for detailed sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🔥 Activity", "📈 Comparison", "⚙️ Actions"])
    
    with tab1:
        display_enhanced_analytics(analytics, dashboard_data)
    
    with tab2:
        animated_dashboard.render_activity_heatmap(analytics)
    
    with tab3:
        animated_dashboard.render_comparison_radar(analytics, user_type)
    
    with tab4:
        display_enhanced_actions(user_data, user_type, dashboard_data)

def display_enhanced_analytics(analytics: dict, dashboard_data: dict):
    """Display enhanced analytics with animations"""
    st.markdown("### 📈 Detailed Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Profile completeness breakdown
        if analytics:
            completeness = analytics.get('profile_completeness', 0)
            
            # Create gauge chart for completeness
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = completeness,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Profile Completeness"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 50], 'color': "#f5576c"},
                        {'range': [50, 80], 'color': "#f093fb"},
                        {'range': [80, 100], 'color': "#48bb78"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=300, margin=dict(t=40, b=40, l=40, r=40))
            st.plotly_chart(fig, use_container_width=True, key="completeness_gauge")
    
    with col2:
        # Activity score over time (simulated)
        import random
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        scores = [min(50 + i + random.randint(-10, 10), 100) for i in range(len(dates))]
        
        fig = px.line(
            x=dates, 
            y=scores,
            title="Activity Score Trend",
            labels={'x': 'Date', 'y': 'Activity Score'}
        )
        
        fig.update_traces(line_color='#667eea', line_width=3)
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True, key="activity_trend")
    
    # Recommendations summary
    st.markdown("#### 🎯 Quick Recommendations")
    recommendations = dashboard_data.get('recommendations', [])
    
    if recommendations:
        for rec in recommendations[:2]:  # Show top 2
            priority_color = {
                'high': '#f5576c',
                'medium': '#f093fb', 
                'low': '#667eea'
            }.get(rec.get('priority', 'low'))
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {priority_color}; margin: 0.5rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <strong style="color: {priority_color};">{rec.get('title', 'Recommendation')}</strong><br>
                <small style="color: #666;">{rec.get('description', '')}</small>
            </div>
            """, unsafe_allow_html=True)

def display_enhanced_actions(user_data: dict, user_type: str, dashboard_data: dict):
    """Display enhanced actions with better UX"""
    st.markdown("### 🛠️ Available Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Data Management")
        
        # Enhanced data export
        if st.button("📥 Export Complete Data", help="Download comprehensive data export", use_container_width=True):
            with st.spinner("Preparing your data export..."):
                time.sleep(1)  # Simulate processing
                export_data = user_analytics.get_user_data_export(user_data['canonical_id'], user_type)
                
                if export_data:
                    # Create multiple format options
                    col_json, col_csv = st.columns(2)
                    
                    with col_json:
                        st.download_button(
                            "📄 Download JSON",
                            data=json.dumps(export_data, indent=2, default=str),
                            file_name=f"{user_data['canonical_id']}_export_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                    
                    with col_csv:
                        if dashboard_data.get('profile_info'):
                            profile_df = pd.DataFrame([dashboard_data['profile_info']])
                            st.download_button(
                                "📊 Download CSV",
                                data=profile_df.to_csv(index=False),
                                file_name=f"{user_data['canonical_id']}_profile.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
        
        if st.button("🔍 Search Registry", help="Search for other entities", use_container_width=True):
            st.info("🔄 Redirecting to Registry Lookup...")
            time.sleep(0.5)
        
        if st.button("🔑 Generate API Key", help="Create API access key", use_container_width=True):
            st.info("🔜 API key generation coming soon!")
    
    with col2:
        st.markdown("#### ⚙️ Account Management")
        
        if st.button("📧 Update Email Preferences", help="Manage notifications", use_container_width=True):
            st.info("🔜 Email preferences panel coming soon!")
        
        if st.button("🔒 Privacy Settings", help="Manage data privacy", use_container_width=True):
            st.info("🔜 Privacy management coming soon!")
        
        if st.button("📞 Contact Support", help="Get help", use_container_width=True):
            with st.expander("📝 Support Request Form", expanded=True):
                with st.form("enhanced_support_form"):
                    subject = st.selectbox(
                        "Request Type",
                        ["Profile Update", "Data Correction", "API Access", "Technical Issue", "General Inquiry"]
                    )
                    priority = st.select_slider(
                        "Priority",
                        options=["Low", "Medium", "High", "Urgent"],
                        value="Medium"
                    )
                    message = st.text_area("Message", placeholder="Describe your request in detail...")
                    
                    if st.form_submit_button("📤 Send Request", use_container_width=True):
                        if message:
                            st.success("✅ Support request submitted! We'll respond within 24 hours.")
                        else:
                            st.error("Please provide a message for your request.")

# Main page execution
if user_auth.is_authenticated():
    user_dashboard()
else:
    login_form()
# Old sections removed - replaced with animated dashboard

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

# Page execution handled at the bottom of the file