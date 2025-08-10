"""Enhanced navigation utilities for the Data Registry Platform"""
import streamlit as st

def inject_navigation_components():
    """Inject enhanced navigation bar, sidebar toggle, and footer"""
    
    # Fixed Navigation Bar
    navbar_html = """
    <div class="fixed-navbar">
        <div class="navbar-brand">
            <span>🏢</span>
            <span>Data Registry</span>
        </div>
        <nav class="navbar-nav">
            <a href="/" class="nav-link">🏠 Home</a>
            <a href="/8_Admin_Dashboard" class="nav-link">📊 Dashboard</a>
            <a href="/3_Registration_Request" class="nav-link">📝 Register</a>
            <a href="/5_Registry_Lookup" class="nav-link">🔍 Search</a>
            <a href="/7_User_Dashboard" class="nav-link">👤 Profile</a>
        </nav>
        <button class="navbar-toggle" id="mobileToggle">☰</button>
    </div>
    """
    
    # Responsive Sidebar Toggle (React-compatible)
    sidebar_html = """
    <button class="sidebar-toggle" id="sidebarToggle">
        <span id="sidebar-icon">☰</span>
    </button>
    
    <div class="sidebar-overlay" id="sidebarOverlay"></div>
    
    <div class="responsive-sidebar" id="responsiveSidebar">
        <div class="sidebar-content">
            <div class="sidebar-section">
                <h3>📊 Dashboard</h3>
                <a href="/8_Admin_Dashboard" class="sidebar-item">
                    <span class="icon">📈</span>
                    Admin Overview
                </a>
                <a href="/7_User_Dashboard" class="sidebar-item">
                    <span class="icon">👤</span>
                    User Profile
                </a>
            </div>
            
            <div class="sidebar-section">
                <h3>👥 User Management</h3>
                <a href="/1_Individual_Admin" class="sidebar-item">
                    <span class="icon">👤</span>
                    Individual Admin
                </a>
                <a href="/2_Organization_Admin" class="sidebar-item">
                    <span class="icon">🏢</span>
                    Organization Admin
                </a>
            </div>
            
            <div class="sidebar-section">
                <h3>🔧 System Tools</h3>
                <a href="/9_Schema_Migration" class="sidebar-item">
                    <span class="icon">🔄</span>
                    Schema Migration
                </a>
                <a href="/10_Gravatar_Integration" class="sidebar-item">
                    <span class="icon">🌐</span>
                    Gravatar Sync
                </a>
                <a href="/6_Production_Config" class="sidebar-item">
                    <span class="icon">⚙️</span>
                    Production Config
                </a>
            </div>
            
            <div class="sidebar-section">
                <h3>🔌 API & Registry</h3>
                <a href="/4_API_Testing" class="sidebar-item">
                    <span class="icon">🔌</span>
                    API Testing
                </a>
                <a href="/5_Registry_Lookup" class="sidebar-item">
                    <span class="icon">🔍</span>
                    Registry Search
                </a>
                <a href="/3_Registration_Request" class="sidebar-item">
                    <span class="icon">📝</span>
                    New Registration
                </a>
            </div>
        </div>
    </div>
    """
    
    # Enhanced JavaScript for navigation (fixed React compatibility)
    navigation_js = """
    <script>
    window.toggleSidebar = function() {
        const sidebar = document.getElementById('responsiveSidebar');
        const overlay = document.getElementById('sidebarOverlay');
        const icon = document.getElementById('sidebar-icon');
        
        if (sidebar && overlay && icon) {
            if (sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
                icon.innerHTML = '☰';
            } else {
                sidebar.classList.add('open');
                overlay.classList.add('active');
                icon.innerHTML = '✕';
            }
        }
    };
    
    window.closeSidebar = function() {
        const sidebar = document.getElementById('responsiveSidebar');
        const overlay = document.getElementById('sidebarOverlay');
        const icon = document.getElementById('sidebar-icon');
        
        if (sidebar && overlay && icon) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            icon.innerHTML = '☰';
        }
    };
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        // Add click handlers
        const toggleButton = document.getElementById('sidebarToggle');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (toggleButton) {
            toggleButton.addEventListener('click', window.toggleSidebar);
        }
        
        if (overlay) {
            overlay.addEventListener('click', window.closeSidebar);
        }
        
        // Close sidebar when clicking links
        const sidebarLinks = document.querySelectorAll('.sidebar-item');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(window.closeSidebar, 100);
            });
        });
    });
    </script>
    """
    
    # Footer
    footer_html = """
    <div class="fixed-footer">
        <div class="footer-content">
            <div class="footer-section">
                <h4>🏢 Data Registry</h4>
                <ul>
                    <li><a href="/3_Registration_Request">Register New User</a></li>
                    <li><a href="/5_Registry_Lookup">Search Registry</a></li>
                    <li><a href="/4_API_Testing">API Documentation</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4>👥 User Management</h4>
                <ul>
                    <li><a href="/1_Individual_Admin">Individual Admin</a></li>
                    <li><a href="/2_Organization_Admin">Organization Admin</a></li>
                    <li><a href="/7_User_Dashboard">User Dashboard</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4>🔧 Admin Tools</h4>
                <ul>
                    <li><a href="/8_Admin_Dashboard">System Dashboard</a></li>
                    <li><a href="/9_Schema_Migration">Schema Migration</a></li>
                    <li><a href="/10_Gravatar_Integration">Gravatar Integration</a></li>
                    <li><a href="/6_Production_Config">Production Config</a></li>
                </ul>
            </div>
            
            <div class="footer-section">
                <h4>📚 Resources</h4>
                <ul>
                    <li><a href="#help">Help & Support</a></li>
                    <li><a href="#docs">Documentation</a></li>
                    <li><a href="#privacy">Privacy Policy</a></li>
                    <li><a href="#terms">Terms of Service</a></li>
                </ul>
            </div>
        </div>
        
        <div class="footer-bottom">
            <p>&copy; 2025 Data Registry Platform. All rights reserved. | Canonical ID System with IP-like addressing</p>
        </div>
    </div>
    """
    
    # Inject all components
    st.markdown(navbar_html, unsafe_allow_html=True)
    st.markdown(sidebar_html, unsafe_allow_html=True)
    st.markdown(navigation_js, unsafe_allow_html=True)
    
    # Return footer to be added at end of page
    return footer_html

def create_page_header(title: str, description: str, icon: str = "🏢"):
    """Create a consistent page header with navigation"""
    
    # Main content wrapper with top margin for fixed navbar
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    header_html = f"""
    <div class="header-container fade-in-up">
        <h1>{icon} {title}</h1>
        <p>{description}</p>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def close_page_with_footer(footer_html: str):
    """Close the page content and add footer"""
    st.markdown('</div>', unsafe_allow_html=True)  # Close main-content
    st.markdown(footer_html, unsafe_allow_html=True)

def get_contextual_sidebar_items(page_type: str):
    """Get contextual sidebar items based on current page"""
    
    context_items = {
        'admin': [
            {'icon': '📊', 'label': 'System Overview', 'action': 'view_metrics'},
            {'icon': '👥', 'label': 'User Management', 'action': 'manage_users'},
            {'icon': '📋', 'label': 'Pending Requests', 'action': 'view_pending'},
            {'icon': '📈', 'label': 'Analytics', 'action': 'view_analytics'},
            {'icon': '⚙️', 'label': 'Settings', 'action': 'view_settings'}
        ],
        'user': [
            {'icon': '👤', 'label': 'My Profile', 'action': 'view_profile'},
            {'icon': '📧', 'label': 'My Emails', 'action': 'manage_emails'},
            {'icon': '📱', 'label': 'My Phones', 'action': 'manage_phones'},
            {'icon': '🏢', 'label': 'Organizations', 'action': 'view_orgs'},
            {'icon': '🔐', 'label': 'Privacy', 'action': 'privacy_settings'}
        ],
        'registration': [
            {'icon': '📝', 'label': 'New Registration', 'action': 'new_form'},
            {'icon': '✅', 'label': 'Validation', 'action': 'validate_form'},
            {'icon': '📋', 'label': 'Review', 'action': 'review_form'},
            {'icon': '📤', 'label': 'Submit', 'action': 'submit_form'}
        ],
        'lookup': [
            {'icon': '🔍', 'label': 'Quick Search', 'action': 'quick_search'},
            {'icon': '🎯', 'label': 'Advanced Search', 'action': 'advanced_search'},
            {'icon': '📊', 'label': 'Search Results', 'action': 'view_results'},
            {'icon': '💾', 'label': 'Export Results', 'action': 'export_results'}
        ],
        'migration': [
            {'icon': '📊', 'label': 'Preview Changes', 'action': 'preview_migration'},
            {'icon': '🗃️', 'label': 'Create Schema', 'action': 'create_schema'},
            {'icon': '🔄', 'label': 'Migrate Data', 'action': 'migrate_data'},
            {'icon': '✅', 'label': 'Validation', 'action': 'validate_migration'},
            {'icon': '🔙', 'label': 'Rollback', 'action': 'rollback_migration'}
        ]
    }
    
    return context_items.get(page_type, [])

def render_contextual_sidebar(page_type: str):
    """Render contextual sidebar for current page"""
    items = get_contextual_sidebar_items(page_type)
    
    if items:
        with st.sidebar:
            st.markdown(f"### 📋 {page_type.title()} Actions")
            
            for item in items:
                if st.button(f"{item['icon']} {item['label']}", key=f"ctx_{item['action']}"):
                    # Store action in session state for handling
                    st.session_state[f"action_{item['action']}"] = True
                    st.rerun()