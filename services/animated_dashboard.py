"""Animated dashboard service with personalized insights"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random
import time

class AnimatedDashboardService:
    """Creates animated dashboard components with personalized insights"""
    
    def __init__(self):
        self.animation_colors = {
            'primary': '#667eea',
            'secondary': '#764ba2', 
            'accent': '#f093fb',
            'warning': '#f5576c',
            'success': '#48bb78',
            'info': '#4299e1'
        }
    
    def render_welcome_header(self, user_data: Dict[str, Any], user_type: str):
        """Render animated welcome header"""
        # Inject animation CSS
        st.markdown("""
        <style>
        @import url('static/css/animations.css');
        </style>
        """, unsafe_allow_html=True)
        
        # Get personalized greeting
        greeting = self._get_personalized_greeting(user_data, user_type)
        
        # Welcome header with animation
        st.markdown(f"""
        <div class="welcome-header">
            <div class="welcome-title">{greeting['title']}</div>
            <div class="welcome-subtitle">{greeting['subtitle']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        return greeting
    
    def render_animated_metrics(self, analytics: Dict[str, Any], user_type: str):
        """Render animated metric cards"""
        st.markdown("### 📊 Your Dashboard Overview")
        
        # Create metric cards with animations
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = self._prepare_metrics(analytics, user_type)
        
        with col1:
            self._render_metric_card(
                metrics['completeness'], 
                delay_class="delay-1",
                color=self.animation_colors['success'] if metrics['completeness']['value'] > 80 else self.animation_colors['warning']
            )
        
        with col2:
            self._render_metric_card(
                metrics['activity'], 
                delay_class="delay-2",
                color=self.animation_colors['primary']
            )
        
        with col3:
            self._render_metric_card(
                metrics['engagement'], 
                delay_class="delay-3",
                color=self.animation_colors['accent']
            )
        
        with col4:
            self._render_metric_card(
                metrics['status'], 
                delay_class="delay-4",
                color=self.animation_colors['info']
            )
    
    def render_insights_timeline(self, user_data: Dict[str, Any], analytics: Dict[str, Any]):
        """Render animated insights timeline"""
        st.markdown("### 📈 Your Journey with Us")
        
        timeline_data = self._generate_timeline_data(user_data, analytics)
        
        # Create animated timeline chart
        fig = go.Figure()
        
        # Add timeline points
        fig.add_trace(go.Scatter(
            x=timeline_data['dates'],
            y=timeline_data['events'],
            mode='markers+lines',
            marker=dict(
                size=12,
                color=timeline_data['colors'],
                line=dict(width=2, color='white')
            ),
            line=dict(width=3, color=self.animation_colors['primary']),
            text=timeline_data['descriptions'],
            hovertemplate="<b>%{y}</b><br>%{text}<br>%{x}<extra></extra>",
            name="Your Journey"
        ))
        
        fig.update_layout(
            title="Account Timeline",
            xaxis_title="Date",
            yaxis_title="Milestones",
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        
        # Add animation effect
        fig.update_traces(
            marker=dict(
                line=dict(width=2),
                opacity=0.8
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, key="timeline_chart")
    
    def render_progress_rings(self, analytics: Dict[str, Any]):
        """Render animated progress rings"""
        st.markdown("### 🎯 Progress Overview")
        
        col1, col2, col3 = st.columns(3)
        
        # Profile completeness ring
        with col1:
            completeness = analytics.get('profile_completeness', 0)
            self._render_progress_ring(
                value=completeness,
                title="Profile Complete",
                color=self.animation_colors['success'],
                subtitle=f"{completeness}% filled"
            )
        
        # Activity score ring
        with col2:
            activity_score = analytics.get('activity_score', 0)
            self._render_progress_ring(
                value=activity_score,
                title="Activity Score",
                color=self.animation_colors['primary'],
                subtitle=f"{activity_score}/100 points"
            )
        
        # Engagement ring
        with col3:
            engagement = min(analytics.get('days_since_approval', 0) * 2, 100)
            self._render_progress_ring(
                value=engagement,
                title="Engagement Level",
                color=self.animation_colors['accent'],
                subtitle=f"{engagement}% active"
            )
    
    def render_personalized_insights(self, user_data: Dict[str, Any], analytics: Dict[str, Any], user_type: str):
        """Render personalized insights and recommendations"""
        st.markdown("### 💡 Personalized Insights")
        
        insights = self._generate_insights(user_data, analytics, user_type)
        
        for i, insight in enumerate(insights):
            # Create animated insight card
            st.markdown(f"""
            <div class="animated-section" style="animation-delay: {i * 0.2}s;">
                <div class="recommendation-card {insight['priority']}-priority">
                    <h4 style="margin: 0 0 10px 0; color: {insight['color']};">
                        {insight['icon']} {insight['title']}
                    </h4>
                    <p style="margin: 0 0 10px 0; color: #666;">
                        {insight['description']}
                    </p>
                    <small style="color: {insight['color']}; font-weight: bold;">
                        {insight['action']}
                    </small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_activity_heatmap(self, analytics: Dict[str, Any]):
        """Render animated activity heatmap"""
        st.markdown("### 🔥 Activity Heatmap")
        
        # Generate sample activity data
        dates = pd.date_range(start=datetime.now() - timedelta(days=90), end=datetime.now(), freq='D')
        activity_data = []
        
        for date in dates:
            # Simulate activity based on analytics
            base_activity = random.randint(0, 10) if analytics.get('activity_score', 0) > 50 else random.randint(0, 5)
            activity_data.append({
                'date': date,
                'day': date.strftime('%A'),
                'week': date.isocalendar()[1],
                'activity': base_activity
            })
        
        df = pd.DataFrame(activity_data)
        
        # Create heatmap
        fig = px.density_heatmap(
            df, 
            x='week', 
            y='day',
            z='activity',
            color_continuous_scale='Viridis',
            title="Daily Activity Pattern (Last 90 Days)"
        )
        
        fig.update_layout(
            height=300,
            xaxis_title="Week of Year",
            yaxis_title="Day of Week"
        )
        
        st.plotly_chart(fig, use_container_width=True, key="activity_heatmap")
    
    def render_comparison_radar(self, analytics: Dict[str, Any], user_type: str):
        """Render radar chart comparing user to platform average"""
        st.markdown("### 📊 Platform Comparison")
        
        # Generate comparison data
        categories = ['Profile Completeness', 'Activity Level', 'API Usage', 'Engagement', 'Data Quality']
        
        user_values = [
            analytics.get('profile_completeness', 0),
            min(analytics.get('activity_score', 0), 100),
            min(analytics.get('api_keys_count', 0) * 25, 100),
            min(analytics.get('days_since_approval', 0) * 2, 100),
            85  # Assume good data quality
        ]
        
        # Platform averages (simulated)
        platform_avg = [75, 60, 40, 65, 80]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=user_values,
            theta=categories,
            fill='toself',
            name='Your Profile',
            line_color=self.animation_colors['primary']
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=platform_avg,
            theta=categories,
            fill='toself',
            name='Platform Average',
            line_color=self.animation_colors['secondary'],
            opacity=0.6
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="How You Compare",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True, key="comparison_radar")
    
    def _get_personalized_greeting(self, user_data: Dict[str, Any], user_type: str) -> Dict[str, str]:
        """Generate personalized greeting"""
        hour = datetime.now().hour
        
        if hour < 12:
            time_greeting = "Good Morning"
        elif hour < 17:
            time_greeting = "Good Afternoon"
        else:
            time_greeting = "Good Evening"
        
        if user_type == "individual":
            name = f"{user_data.get('first_name', 'User')}"
            title = f"{time_greeting}, {name}! 👋"
            subtitle = f"Welcome to your personalized data registry dashboard"
        else:
            org_name = user_data.get('organization_name', 'Organization')
            title = f"{time_greeting}, {org_name}! 🏢"
            subtitle = f"Your organization's data registry command center"
        
        return {
            'title': title,
            'subtitle': subtitle
        }
    
    def _prepare_metrics(self, analytics: Dict[str, Any], user_type: str) -> Dict[str, Dict]:
        """Prepare metrics for animated display"""
        days_registered = analytics.get('days_registered', 0)
        
        return {
            'completeness': {
                'title': 'Profile Complete',
                'value': analytics.get('profile_completeness', 0),
                'unit': '%',
                'icon': '✅',
                'trend': 'up' if analytics.get('profile_completeness', 0) > 50 else 'neutral'
            },
            'activity': {
                'title': 'Days Active',
                'value': days_registered,
                'unit': 'days',
                'icon': '📅',
                'trend': 'up' if days_registered > 30 else 'neutral'
            },
            'engagement': {
                'title': 'Engagement Score',
                'value': analytics.get('activity_score', 0),
                'unit': '/100',
                'icon': '⭐',
                'trend': 'up' if analytics.get('activity_score', 0) > 60 else 'neutral'
            },
            'status': {
                'title': 'Account Status',
                'value': 'Active' if analytics.get('days_since_approval', 0) >= 0 else 'Pending',
                'unit': '',
                'icon': '🟢' if analytics.get('days_since_approval', 0) >= 0 else '🟡',
                'trend': 'up'
            }
        }
    
    def _render_metric_card(self, metric: Dict[str, Any], delay_class: str, color: str):
        """Render individual animated metric card"""
        trend_icon = "↗️" if metric['trend'] == 'up' else "➡️"
        
        st.markdown(f"""
        <div class="metric-card {delay_class}" style="--accent-color: {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">
                        {metric['icon']} {metric['title']}
                    </div>
                    <div style="font-size: 1.8rem; font-weight: bold; color: {color};">
                        {metric['value']}{metric['unit']}
                    </div>
                </div>
                <div style="font-size: 1.2rem;">
                    {trend_icon}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_progress_ring(self, value: int, title: str, color: str, subtitle: str):
        """Render animated progress ring"""
        # Create donut chart for progress ring
        fig = go.Figure(data=[go.Pie(
            values=[value, 100-value], 
            hole=.7,
            marker_colors=[color, '#f0f2f6'],
            showlegend=False,
            textinfo='none',
            hoverinfo='skip'
        )])
        
        fig.update_layout(
            height=200,
            margin=dict(t=20, b=20, l=20, r=20),
            annotations=[dict(text=f'{value}%', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"ring_{title.replace(' ', '_')}")
        st.markdown(f"<div style='text-align: center; margin-top: -20px;'><strong>{title}</strong><br><small>{subtitle}</small></div>", unsafe_allow_html=True)
    
    def _generate_timeline_data(self, user_data: Dict[str, Any], analytics: Dict[str, Any]) -> Dict[str, List]:
        """Generate timeline data for visualization"""
        events = ['Registration', 'Approval', 'First Activity', 'Profile Update']
        dates = []
        colors = []
        descriptions = []
        
        # Registration date
        reg_date = analytics.get('registration_date', datetime.now() - timedelta(days=30))
        dates.append(reg_date)
        colors.append(self.animation_colors['info'])
        descriptions.append("Account created successfully")
        
        # Approval date
        app_date = analytics.get('approval_date', datetime.now() - timedelta(days=25))
        dates.append(app_date)
        colors.append(self.animation_colors['success'])
        descriptions.append("Account approved by admin")
        
        # First activity (simulated)
        first_activity = app_date + timedelta(days=1)
        dates.append(first_activity)
        colors.append(self.animation_colors['primary'])
        descriptions.append("First dashboard access")
        
        # Recent activity
        recent_activity = datetime.now() - timedelta(days=1)
        dates.append(recent_activity)
        colors.append(self.animation_colors['accent'])
        descriptions.append("Recent profile activity")
        
        return {
            'dates': dates,
            'events': events,
            'colors': colors,
            'descriptions': descriptions
        }
    
    def _generate_insights(self, user_data: Dict[str, Any], analytics: Dict[str, Any], user_type: str) -> List[Dict[str, Any]]:
        """Generate personalized insights"""
        insights = []
        
        # Profile completeness insight
        completeness = analytics.get('profile_completeness', 0)
        if completeness < 100:
            insights.append({
                'title': 'Complete Your Profile',
                'description': f'Your profile is {completeness}% complete. Adding missing information improves data accuracy and unlocks additional features.',
                'action': 'Update profile information in the Profile tab',
                'priority': 'high' if completeness < 60 else 'medium',
                'color': self.animation_colors['warning'] if completeness < 60 else self.animation_colors['info'],
                'icon': '📝'
            })
        
        # API usage insight
        if analytics.get('api_keys_count', 0) == 0:
            insights.append({
                'title': 'Unlock API Access',
                'description': 'Generate API keys to programmatically access your data and integrate with external systems.',
                'action': 'Create your first API key in Available Actions',
                'priority': 'medium',
                'color': self.animation_colors['primary'],
                'icon': '🔑'
            })
        
        # Engagement insight
        days_active = analytics.get('days_since_approval', 0)
        if days_active < 7:
            insights.append({
                'title': 'Explore Platform Features',
                'description': 'You\'re new here! Discover registry search, data management tools, and integration options.',
                'action': 'Browse all dashboard sections and features',
                'priority': 'low',
                'color': self.animation_colors['accent'],
                'icon': '🌟'
            })
        
        # Data backup insight
        insights.append({
            'title': 'Keep Your Data Safe',
            'description': 'Regular data exports ensure you always have access to your registered information.',
            'action': 'Download your data export as backup',
            'priority': 'low',
            'color': self.animation_colors['success'],
            'icon': '💾'
        })
        
        return insights[:3]  # Limit to 3 insights for better UX

# Global animated dashboard service
animated_dashboard = AnimatedDashboardService()