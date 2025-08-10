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
    
    # Enhanced navigation and layout styles
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fixed Navbar */
    .fixed-navbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        backdrop-filter: blur(10px);
    }

    .navbar-brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .navbar-nav {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .nav-link {
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.3s;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .nav-link:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-1px);
    }

    /* Responsive Sidebar */
    .sidebar-toggle {
        position: fixed;
        top: 80px;
        left: 10px;
        background: #667eea;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        z-index: 999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        font-size: 1.1rem;
    }

    .sidebar-toggle:hover {
        background: #5a67d8;
        transform: scale(1.05);
    }

    .responsive-sidebar {
        position: fixed;
        top: 70px;
        left: -340px;
        width: 340px;
        height: calc(100vh - 70px);
        background: white;
        z-index: 999;
        transition: left 0.3s ease;
        overflow-y: auto;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.1);
    }

    .responsive-sidebar.open {
        left: 0;
    }

    .sidebar-content {
        padding: 1.5rem;
    }

    .sidebar-section {
        margin-bottom: 2.5rem;
    }

    .sidebar-section h3 {
        color: #667eea;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f1f3f4;
    }

    .sidebar-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        color: #333;
        text-decoration: none;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    .sidebar-item:hover {
        background: #f8f9ff;
        color: #667eea;
        transform: translateX(5px);
    }

    .sidebar-item .icon {
        margin-right: 0.75rem;
        font-size: 1.1rem;
    }
    
    /* Main content adjustment */
    .main .block-container {
        padding-top: 90px;
        padding-bottom: 2rem;
        max-width: none;
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
        font-weight: 500;
    }
    
    .status-approved {
        background: #d4edda;
        color: #155724;
    }
    
    .status-pending {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-rejected {
        background: #f8d7da;
        color: #721c24;
    }

    /* Footer */
    .fixed-footer {
        background: #2c3e50;
        color: white;
        padding: 2rem 1rem 1rem;
        margin-top: 2rem;
    }

    .footer-content {
        max-width: 1200px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
    }

    .footer-section h4 {
        margin-bottom: 1rem;
        color: #ecf0f1;
        font-weight: 600;
    }

    .footer-section ul {
        list-style: none;
        padding: 0;
    }

    .footer-section ul li {
        margin-bottom: 0.5rem;
    }

    .footer-section ul li a {
        color: #bdc3c7;
        text-decoration: none;
        transition: color 0.3s;
        font-weight: 500;
    }

    .footer-section ul li a:hover {
        color: #ecf0f1;
    }

    .footer-bottom {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #34495e;
        color: #bdc3c7;
        font-size: 0.9rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .navbar-nav {
            display: none;
        }
        
        .sidebar-toggle {
            left: 5px;
            top: 75px;
            padding: 0.5rem;
        }
        
        .navbar-brand {
            font-size: 1.2rem;
        }
    }

    @media (max-width: 480px) {
        .responsive-sidebar {
            width: 100%;
            left: -100%;
        }
    }
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