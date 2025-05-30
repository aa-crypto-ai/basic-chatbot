/**
 * Token Monitor - Automatically refreshes access tokens for active users
 * Monitors token expiration and refreshes when within 2-hour threshold
 */

class TokenMonitor {
    constructor() {
        this.refreshInterval = 30 * 60 * 1000; // Check every 30 minutes
        this.activityTimeout = 10 * 60 * 1000; // Consider user inactive after 10 minutes
        this.lastActivity = Date.now();
        this.intervalId = null;
        this.isRefreshing = false;
        
        this.init();
    }

    init() {
        // Start monitoring
        this.startMonitoring();
        
        // Track user activity
        this.trackActivity();
        
        console.log('Token monitor initialized');
    }

    startMonitoring() {
        // Initial check after a short delay
        setTimeout(() => this.checkAndRefreshToken(), 5000);
        
        // Set up periodic checks
        this.intervalId = setInterval(() => {
            this.checkAndRefreshToken();
        }, this.refreshInterval);
    }

    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    trackActivity() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        const updateActivity = () => {
            this.lastActivity = Date.now();
        };

        events.forEach(event => {
            document.addEventListener(event, updateActivity, { passive: true });
        });

        // Track visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.lastActivity = Date.now();
                // Check token when page becomes visible
                setTimeout(() => this.checkAndRefreshToken(), 1000);
            }
        });
    }

    isUserActive() {
        const timeSinceActivity = Date.now() - this.lastActivity;
        return timeSinceActivity < this.activityTimeout;
    }

    async checkAndRefreshToken() {
        // Only refresh for active users
        if (!this.isUserActive()) {
            console.log('User inactive, skipping token refresh check');
            return;
        }

        if (this.isRefreshing) {
            console.log('Token refresh already in progress');
            return;
        }

        try {
            this.isRefreshing = true;
            
            const response = await fetch('/auth/refresh', {
                method: 'POST',
                credentials: 'include', // Include cookies
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json(); // Proper JSON response now
                
                if (data.refreshed) {
                    console.log('Token refreshed successfully');
                    // Token was refreshed, cookie is automatically updated by server
                } else {
                    console.log('Token refresh not needed');
                }
            } else if (response.status === 401) {
                console.log('Token invalid, redirecting to login');
                // Token is invalid, redirect to login
                window.location.href = '/auth/login';
            } else {
                console.warn('Token refresh failed:', response.status);
            }
        } catch (error) {
            console.error('Error checking token:', error);
            // Silently fail - don't disrupt user experience
        } finally {
            this.isRefreshing = false;
        }
    }

    // Manual refresh method for specific actions
    async refreshNow() {
        await this.checkAndRefreshToken();
    }
}

// Initialize token monitor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tokenMonitor = new TokenMonitor();
});

// Also initialize if script is loaded after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.tokenMonitor) {
            window.tokenMonitor = new TokenMonitor();
        }
    });
} else {
    if (!window.tokenMonitor) {
        window.tokenMonitor = new TokenMonitor();
    }
}

// Enhanced predict function wrapper for Gradio integration
// This will be called when messages are sent to the chatbot
if (typeof window.originalPredict === 'undefined') {
    window.originalPredict = window.predict;
}

// Override predict to trigger token refresh on activity
window.predict = function(...args) {
    // Update activity timestamp
    if (window.tokenMonitor) {
        window.tokenMonitor.lastActivity = Date.now();
        
        // Optionally trigger immediate token check for important actions
        setTimeout(() => {
            if (window.tokenMonitor) {
                window.tokenMonitor.checkAndRefreshToken();
            }
        }, 100);
    }
    
    // Call original predict function
    if (window.originalPredict) {
        return window.originalPredict.apply(this, args);
    }
    
    return args; // Fallback
};
