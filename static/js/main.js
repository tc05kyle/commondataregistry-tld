// Data Registry Platform - Main JavaScript

// Form validation helpers
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateDomain(domain) {
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
    return domainRegex.test(domain);
}

// Enhanced form interaction
document.addEventListener('DOMContentLoaded', function() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('.primary-button, .secondary-button');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                this.disabled = true;
                this.innerHTML = 'Processing...';
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = this.getAttribute('data-original-text') || 'Submit';
                }, 3000);
            }
        });
    });

    // Auto-save form data to localStorage
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // Load saved data
            const savedValue = localStorage.getItem(`form_${input.name}`);
            if (savedValue && input.type !== 'password') {
                input.value = savedValue;
            }

            // Save data on change
            input.addEventListener('change', function() {
                if (this.type !== 'password') {
                    localStorage.setItem(`form_${this.name}`, this.value);
                }
            });
        });

        // Clear saved data on successful submit
        form.addEventListener('submit', function() {
            setTimeout(() => {
                inputs.forEach(input => {
                    localStorage.removeItem(`form_${input.name}`);
                });
            }, 1000);
        });
    });

    // Table sorting functionality
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(table, index));
        });
    });
});

// Table sorting function
function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.getAttribute('data-sort-direction') !== 'asc';
    table.setAttribute('data-sort-direction', isAscending ? 'asc' : 'desc');
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Check if values are numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Clear and re-append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert-${type}`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '300px';
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
    
    // Allow manual close
    notification.addEventListener('click', () => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    });
}

// Export functions for use in other scripts
window.DataRegistry = {
    validateEmail,
    validateDomain,
    showNotification,
    sortTable
};