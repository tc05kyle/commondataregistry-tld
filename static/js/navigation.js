/**
 * Enhanced Navigation JavaScript for Data Registry Platform
 */

// Navigation state management
let sidebarOpen = false;

/**
 * Toggle responsive sidebar
 */
function toggleSidebar() {
    const sidebar = document.getElementById('responsiveSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const icon = document.getElementById('sidebar-icon');
    
    if (!sidebar || !overlay || !icon) {
        console.warn('Navigation elements not found');
        return;
    }
    
    if (sidebarOpen) {
        closeSidebar();
    } else {
        openSidebar();
    }
}

/**
 * Open sidebar
 */
function openSidebar() {
    const sidebar = document.getElementById('responsiveSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const icon = document.getElementById('sidebar-icon');
    
    if (sidebar && overlay && icon) {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        icon.innerHTML = '✕';
        sidebarOpen = true;
        
        // Add escape key listener
        document.addEventListener('keydown', handleEscapeKey);
    }
}

/**
 * Close sidebar
 */
function closeSidebar() {
    const sidebar = document.getElementById('responsiveSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const icon = document.getElementById('sidebar-icon');
    
    if (sidebar && overlay && icon) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        icon.innerHTML = '☰';
        sidebarOpen = false;
        
        // Remove escape key listener
        document.removeEventListener('keydown', handleEscapeKey);
    }
}

/**
 * Handle escape key to close sidebar
 */
function handleEscapeKey(event) {
    if (event.key === 'Escape' && sidebarOpen) {
        closeSidebar();
    }
}

/**
 * Toggle mobile navigation
 */
function toggleMobileNav() {
    const navbar = document.querySelector('.navbar-nav');
    
    if (navbar) {
        navbar.classList.toggle('mobile-open');
    }
}

/**
 * Highlight current page in navigation
 */
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-item');
    
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Initialize navigation when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Close sidebar when clicking on links
    const sidebarLinks = document.querySelectorAll('.sidebar-item');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Allow normal navigation
            setTimeout(closeSidebar, 100);
        });
    });
    
    // Highlight current page
    highlightCurrentPage();
    
    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading animation for page transitions
    const pageLinks = document.querySelectorAll('a[href^="/"]');
    pageLinks.forEach(link => {
        link.addEventListener('click', function() {
            const loader = document.createElement('div');
            loader.className = 'page-loader';
            loader.innerHTML = '<div class="loader-spinner"></div>';
            document.body.appendChild(loader);
            
            // Remove loader after navigation
            setTimeout(() => {
                if (document.body.contains(loader)) {
                    document.body.removeChild(loader);
                }
            }, 2000);
        });
    });
});

/**
 * Handle window resize for responsive navigation
 */
window.addEventListener('resize', function() {
    // Close sidebar on desktop view
    if (window.innerWidth > 768 && sidebarOpen) {
        closeSidebar();
    }
});

/**
 * Context menu management
 */
function showContextMenu(pageType, actions) {
    const contextMenu = document.getElementById('contextMenu');
    if (!contextMenu) return;
    
    // Clear existing actions
    contextMenu.innerHTML = '';
    
    // Add header
    const header = document.createElement('h3');
    header.textContent = `${pageType} Actions`;
    contextMenu.appendChild(header);
    
    // Add actions
    actions.forEach(action => {
        const button = document.createElement('button');
        button.className = 'context-action';
        button.innerHTML = `${action.icon} ${action.label}`;
        button.onclick = () => handleContextAction(action.action);
        contextMenu.appendChild(button);
    });
    
    contextMenu.style.display = 'block';
}

/**
 * Handle context action
 */
function handleContextAction(action) {
    // Dispatch custom event for Streamlit to handle
    const event = new CustomEvent('contextAction', {
        detail: { action: action }
    });
    window.dispatchEvent(event);
    
    // Close context menu
    const contextMenu = document.getElementById('contextMenu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
}

// Export functions for global access
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;
window.toggleMobileNav = toggleMobileNav;
window.showContextMenu = showContextMenu;