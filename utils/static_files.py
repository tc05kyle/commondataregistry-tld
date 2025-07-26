"""Static file utilities for Streamlit app"""
import streamlit as st
import os
import base64

def load_css(file_path):
    """Load CSS file and inject into Streamlit"""
    try:
        with open(file_path, 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found: {file_path}")

def load_local_svg(file_path):
    """Load local SVG file and return as base64 string"""
    try:
        with open(file_path, 'r') as f:
            svg_content = f.read()
        return svg_content
    except FileNotFoundError:
        return None

def get_base64_encoded_image(file_path):
    """Get base64 encoded image for embedding"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def display_logo():
    """Display the application logo"""
    logo_path = "static/images/logo.svg"
    if os.path.exists(logo_path):
        logo_svg = load_local_svg(logo_path)
        if logo_svg:
            st.markdown(f'<div style="text-align: center;">{logo_svg}</div>', unsafe_allow_html=True)
        else:
            st.markdown("### 🏢 Data Registry Platform")
    else:
        st.markdown("### 🏢 Data Registry Platform")

def inject_custom_css():
    """Inject custom CSS styles"""
    css_path = "static/css/styles.css"
    if os.path.exists(css_path):
        load_css(css_path)
    
    # Additional inline styles for better Streamlit integration
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .stSelectbox > div > div > div {
        background-color: #f8f9fa;
    }
    
    .stTextInput > div > div > input {
        background-color: #f8f9fa;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #f8f9fa;
    }
    
    /* Status badge styling */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .status-approved {
        background-color: #27ae60;
        color: white;
    }
    
    .status-pending {
        background-color: #f39c12;
        color: white;
    }
    
    .status-rejected {
        background-color: #e74c3c;
        color: white;
    }
    
    /* Custom button styles */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
        color: white;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #2c3e50;
    }
    
    /* Hide Streamlit menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def create_status_badge(status):
    """Create a styled status badge"""
    status_lower = status.lower()
    if status_lower == 'approved':
        return f'<span class="status-badge status-approved">{status}</span>'
    elif status_lower == 'pending':
        return f'<span class="status-badge status-pending">{status}</span>'
    elif status_lower == 'rejected':
        return f'<span class="status-badge status-rejected">{status}</span>'
    else:
        return f'<span class="status-badge">{status}</span>'