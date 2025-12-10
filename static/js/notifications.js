// static/js/notifications.js
class NotificationManager {
    constructor() {
        this.pollingInterval = 15000; // 15 seconds
        this.pollingEnabled = true;
        this.unreadCount = 0;
        this.notificationSound = new Audio('/static/sounds/notification.mp3');
        this.init();
    }

    init() {
        if (document.getElementById('notificationBell')) {
            this.startPolling();
            this.setupEventListeners();
            this.updateBadge();
        }
    }

    startPolling() {
        setInterval(() => {
            if (this.pollingEnabled && this.isUserActive()) {
                this.checkNotifications();
            }
        }, this.pollingInterval);
    }

    isUserActive() {
        // Check if user is active on the page
        return !document.hidden;
    }

    async checkNotifications() {
        try {
            const response = await fetch('/api/notifications/');
            const data = await response.json();

            if (data.notifications && data.notifications.length > 0) {
                this.handleNewNotifications(data.notifications);
                this.updateBadge(data.notifications.length);
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }

    handleNewNotifications(notifications) {
        notifications.forEach(notification => {
            if (!notification.is_read) {
                this.showNotificationToast(notification);
                this.playNotificationSound();
            }
        });
    }

    showNotificationToast(notification) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${notification.title}</strong>
                <small>${notification.time}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${notification.message}
                ${notification.link ? `<br><a href="${notification.link}" class="btn btn-sm btn-primary mt-2">View</a>` : ''}
            </div>
        `;

        // Add to container
        const container = document.getElementById('notificationContainer') || this.createNotificationContainer();
        container.appendChild(toast);

        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();

        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
        return container;
    }

    playNotificationSound() {
        if (Notification.permission === 'granted') {
            this.notificationSound.play().catch(e => console.log('Audio play failed:', e));
        }
    }

    updateBadge(count) {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    setupEventListeners() {
        // Mark all as read
        const markAllReadBtn = document.getElementById('markAllRead');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }

        // Enable/disable notifications
        const notificationToggle = document.getElementById('notificationToggle');
        if (notificationToggle) {
            notificationToggle.addEventListener('change', (e) => {
                this.pollingEnabled = e.target.checked;
            });
        }
    }

    async markAllAsRead() {
        try {
            await fetch('/api/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
            this.updateBadge(0);
        } catch (error) {
            console.error('Error marking notifications as read:', error);
        }
    }
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    new NotificationManager();
});