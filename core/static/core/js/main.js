// FamilyChef Main JavaScript
// Core functionality for the PWA application

class FamilyChef {
    constructor() {
        this.apiBase = '/api';
        this.cache = new Map();
        this.init();
    }

    async init() {
        // Initialize the application
        console.log('FamilyChef: Initializing application...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadInitialData();
        
        // Set up periodic data refresh
        this.setupDataRefresh();
        
        console.log('FamilyChef: Application initialized');
    }

    setupEventListeners() {
        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });

        // Menu item clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.menu-item')) {
                this.handleMenuItemClick(e.target);
            }
        });

        // Order status updates
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="update-status"]')) {
                e.preventDefault();
                this.handleStatusUpdate(e.target);
            }
        });

        // Theme toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('#themeToggle')) {
                this.toggleTheme();
            }
        });

        // Search functionality
        const searchInput = document.querySelector('#menuSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterMenu(e.target.value);
            });
        }
    }

    async loadInitialData() {
        try {
            // Load menu data
            const menuData = await this.fetchAPI('/menu/');
            this.renderMenu(menuData);

            // Load orders if on chef board
            if (document.querySelector('.chef-board')) {
                const ordersData = await this.fetchAPI('/orders/');
                this.renderOrders(ordersData);
            }

            // Load pantry data if on pantry page
            if (document.querySelector('.pantry-view')) {
                const pantryData = await this.fetchAPI('/pantry-stock/');
                this.renderPantry(pantryData);
            }

        } catch (error) {
            console.error('FamilyChef: Failed to load initial data', error);
            this.showNotification('Failed to load data. Please check your connection.', 'error');
        }
    }

    async fetchAPI(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        
        // Check cache first
        if (options.method === 'GET' || !options.method) {
            const cached = this.cache.get(url);
            if (cached && Date.now() - cached.timestamp < 300000) { // 5 min cache
                return cached.data;
            }
        }

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Cache GET requests
            if (options.method === 'GET' || !options.method) {
                this.cache.set(url, {
                    data,
                    timestamp: Date.now()
                });
            }

            return data;
        } catch (error) {
            console.error('FamilyChef: API request failed', error);
            throw error;
        }
    }

    renderMenu(data) {
        const menuContainer = document.querySelector('.menu-grid');
        if (!menuContainer) return;

        const menuItems = data.results || data;
        
        menuContainer.innerHTML = menuItems.map(item => `
            <div class="menu-item ${!item.is_available ? 'unavailable' : ''}" data-cuisine-id="${item.id}">
                <h3 class="menu-item-title">${this.escapeHtml(item.name)}</h3>
                <p class="menu-item-description">${this.escapeHtml(item.description || '')}</p>
                <div class="menu-item-time">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5z"/>
                    </svg>
                    ${item.default_time_min || 0} minutes
                </div>
                ${item.is_available ? `
                    <button class="btn btn-primary mt-md" data-action="order-item">
                        Order Now
                    </button>
                ` : ''}
            </div>
        `).join('');

        // Add click handlers for order buttons
        menuContainer.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="order-item"]')) {
                const menuItem = e.target.closest('.menu-item');
                const cuisineId = menuItem.dataset.cuisineId;
                this.orderItem(cuisineId);
            }
        });
    }

    renderOrders(data) {
        const orderBoard = document.querySelector('.chef-board');
        if (!orderBoard) return;

        const orders = data.results || data;
        const ordersByStatus = {
            'NEW': orders.filter(o => o.status === 'NEW'),
            'COOKING': orders.filter(o => o.status === 'COOKING'),
            'DONE': orders.filter(o => o.status === 'DONE')
        };

        Object.entries(ordersByStatus).forEach(([status, statusOrders]) => {
            const column = orderBoard.querySelector(`[data-status="${status}"]`);
            if (column) {
                const ordersList = column.querySelector('.orders-list');
                ordersList.innerHTML = statusOrders.map(order => `
                    <div class="order-card" data-order-id="${order.id}">
                        <h4>${this.escapeHtml(order.cuisine_name)}</h4>
                        <p>Ordered by: ${this.escapeHtml(order.created_by_name)}</p>
                        <p>Time: ${new Date(order.created_at).toLocaleTimeString()}</p>
                        <div class="order-actions">
                            ${this.getOrderActions(order)}
                        </div>
                    </div>
                `).join('');
            }
        });
    }

    getOrderActions(order) {
        switch (order.status) {
            case 'NEW':
                return `<button class="btn btn-warning" data-action="update-status" data-order-id="${order.id}" data-status="COOKING">Start Cooking</button>`;
            case 'COOKING':
                return `<button class="btn btn-success" data-action="update-status" data-order-id="${order.id}" data-status="DONE">Mark Done</button>`;
            case 'DONE':
                return `<span class="status-badge done">Completed</span>`;
            default:
                return '';
        }
    }

    async orderItem(cuisineId) {
        try {
            await this.fetchAPI('/orders/', {
                method: 'POST',
                body: JSON.stringify({
                    cuisine: cuisineId,
                    status: 'NEW'
                })
            });

            this.showNotification('Order placed successfully!', 'success');
        } catch (error) {
            console.error('Failed to place order:', error);
            this.showNotification('Failed to place order. Please try again.', 'error');
        }
    }

    async handleStatusUpdate(button) {
        const orderId = button.dataset.orderId;
        const newStatus = button.dataset.status;

        try {
            await this.fetchAPI(`/orders/${orderId}/update_status/`, {
                method: 'PATCH',
                body: JSON.stringify({ status: newStatus })
            });

            // Refresh orders display
            const ordersData = await this.fetchAPI('/orders/');
            this.renderOrders(ordersData);

            this.showNotification('Order status updated!', 'success');
        } catch (error) {
            console.error('Failed to update order status:', error);
            this.showNotification('Failed to update order status.', 'error');
        }
    }

    filterMenu(searchTerm) {
        const menuItems = document.querySelectorAll('.menu-item');
        const term = searchTerm.toLowerCase();

        menuItems.forEach(item => {
            const title = item.querySelector('.menu-item-title').textContent.toLowerCase();
            const description = item.querySelector('.menu-item-description').textContent.toLowerCase();
            
            if (title.includes(term) || description.includes(term)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        this.showNotification(`Switched to ${newTheme} theme`, 'info');
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${this.escapeHtml(message)}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Add to DOM
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    setupDataRefresh() {
        // Refresh data every 30 seconds when page is visible
        let refreshInterval;

        const startRefresh = () => {
            refreshInterval = setInterval(async () => {
                if (!document.hidden) {
                    try {
                        // Clear cache to force fresh data
                        this.cache.clear();
                        await this.loadInitialData();
                    } catch (error) {
                        console.error('Failed to refresh data:', error);
                    }
                }
            }, 30000);
        };

        const stopRefresh = () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        };

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopRefresh();
            } else {
                startRefresh();
            }
        });

        // Start initial refresh
        startRefresh();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Additional notification styles
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 16px;
        max-width: 300px;
        z-index: 1200;
        animation: slideIn 0.3s ease-out;
    }
    
    .notification-success { border-left: 4px solid #4CAF50; }
    .notification-error { border-left: 4px solid #F44336; }
    .notification-warning { border-left: 4px solid #FF9800; }
    .notification-info { border-left: 4px solid #2196F3; }
    
    .notification-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        margin-left: 10px;
        color: #666;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    [data-theme="dark"] .notification {
        background: #1e1e1e;
        border-color: #333;
        color: #fff;
    }
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.familyChef = new FamilyChef();
});

// Export for testing and external use
window.FamilyChef = FamilyChef;