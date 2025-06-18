// PWA functionality for FamilyChef
// Handles service worker registration and PWA features

class FamilyChefPWA {
    constructor() {
        this.init();
    }

    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/core/js/sw.js');
                console.log('PWA: Service Worker registered successfully', registration);
                
                // Handle updates
                registration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate(registration.installing);
                });
                
                // Check for already waiting service worker
                if (registration.waiting) {
                    this.showUpdateAvailable();
                }
                
            } catch (error) {
                console.error('PWA: Service Worker registration failed', error);
            }
        }

        // Set up offline/online event listeners
        this.setupConnectionListeners();
        
        // Set up install prompt
        this.setupInstallPrompt();
        
        // Initialize UI components
        this.initializeUI();
    }

    handleServiceWorkerUpdate(worker) {
        worker.addEventListener('statechange', () => {
            if (worker.state === 'installed') {
                this.showUpdateAvailable();
            }
        });
    }

    showUpdateAvailable() {
        // Show update notification
        const updateBanner = document.createElement('div');
        updateBanner.className = 'update-banner';
        updateBanner.innerHTML = `
            <div class="update-content">
                <span>A new version of FamilyChef is available!</span>
                <button id="updateBtn" class="btn btn-primary">Update</button>
                <button id="dismissBtn" class="btn btn-secondary">Later</button>
            </div>
        `;
        
        document.body.appendChild(updateBanner);
        
        // Handle update button click
        document.getElementById('updateBtn').addEventListener('click', () => {
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.getRegistration().then(registration => {
                    if (registration && registration.waiting) {
                        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                    }
                });
            }
            window.location.reload();
        });
        
        // Handle dismiss button click
        document.getElementById('dismissBtn').addEventListener('click', () => {
            updateBanner.remove();
        });
    }

    setupConnectionListeners() {
        // Show offline/online status
        const showConnectionStatus = (isOnline) => {
            let statusBanner = document.querySelector('.connection-status');
            
            if (!statusBanner) {
                statusBanner = document.createElement('div');
                statusBanner.className = 'connection-status';
                document.body.appendChild(statusBanner);
            }
            
            if (isOnline) {
                statusBanner.className = 'connection-status online';
                statusBanner.textContent = 'Back online';
                setTimeout(() => statusBanner.remove(), 3000);
            } else {
                statusBanner.className = 'connection-status offline';
                statusBanner.textContent = 'You are offline - some features may be limited';
            }
        };

        window.addEventListener('online', () => {
            showConnectionStatus(true);
            this.syncWhenOnline();
        });

        window.addEventListener('offline', () => {
            showConnectionStatus(false);
        });

        // Initial status check
        if (!navigator.onLine) {
            showConnectionStatus(false);
        }
    }

    setupInstallPrompt() {
        let deferredPrompt;
        let installPrompt = null; // PWA install prompt event reference
        
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67 and earlier from automatically showing the prompt
            e.preventDefault();
            
            // Stash the event so it can be triggered later
            deferredPrompt = e;
            installPrompt = e; // Store reference for installPrompt functionality
            
            // Show install button
            this.showInstallButton(deferredPrompt);
        });

        // Handle successful installation
        window.addEventListener('appinstalled', () => {
            console.log('PWA: App installed successfully');
            this.hideInstallButton();
            deferredPrompt = null;
        });
    }

    showInstallButton(deferredPrompt) {
        const installButton = document.getElementById('installBtn');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    // Show the install prompt
                    deferredPrompt.prompt();
                    
                    // Wait for the user to respond
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log(`PWA: User response to install prompt: ${outcome}`);
                    
                    // Clear the deferred prompt
                    deferredPrompt = null;
                    this.hideInstallButton();
                }
            });
        }
    }

    hideInstallButton() {
        const installButton = document.getElementById('installBtn');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    syncWhenOnline() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(registration => {
                return registration.sync.register('menu-sync');
            }).catch(error => {
                console.log('PWA: Background sync registration failed', error);
            });
        }
    }

    initializeUI() {
        // Add PWA-specific CSS classes
        document.documentElement.classList.add('pwa-enabled');
        
        // Check if running as PWA
        if (window.matchMedia('(display-mode: standalone)').matches || 
            window.navigator.standalone === true) {
            document.documentElement.classList.add('pwa-standalone');
        }
        
        // Handle responsive design
        this.handleResponsiveDesign();
        
        // Initialize dark mode if supported
        this.initializeDarkMode();
    }

    handleResponsiveDesign() {
        // Add responsive classes based on screen size
        const updateResponsiveClasses = () => {
            const width = window.innerWidth;
            const body = document.body;
            
            // Remove existing responsive classes
            body.classList.remove('mobile', 'tablet', 'desktop');
            
            // Add appropriate class
            if (width <= 480) {
                body.classList.add('mobile');
            } else if (width <= 768) {
                body.classList.add('tablet');
            } else {
                body.classList.add('desktop');
            }
        };
        
        // Initial check
        updateResponsiveClasses();
        
        // Listen for resize events
        window.addEventListener('resize', updateResponsiveClasses);
    }

    initializeDarkMode() {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        const currentTheme = localStorage.getItem('theme');
        
        // Set initial theme
        if (currentTheme) {
            document.documentElement.setAttribute('data-theme', currentTheme);
        } else if (prefersDark.matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
        }
        
        // Listen for system theme changes
        prefersDark.addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });
        
        // Add theme toggle functionality
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                
                document.documentElement.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
            });
        }
    }
}

// Initialize PWA when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FamilyChefPWA();
});

// Export for use in other modules
window.FamilyChefPWA = FamilyChefPWA;