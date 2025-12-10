// static/js/main.js
// Main JavaScript file for Campus Essentials Hub

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // Image preview for file inputs
    document.querySelectorAll('.image-preview-input').forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const previewId = this.getAttribute('data-preview');
            const preview = document.getElementById(previewId);

            if (file && preview) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(file);
            }
        });
    });

    // Confirm actions
    document.querySelectorAll('[data-confirm]').forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide alerts
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Search functionality
function performSearch(query) {
    if (query.length < 2) return;

    fetch(`/api/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            updateSearchResults(data.results);
        })
        .catch(error => console.error('Search error:', error));
}

// Form validation enhancements
function enhanceForms() {
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
}

// Load more functionality for listings
function setupLoadMore() {
    const loadMoreButtons = document.querySelectorAll('.load-more');
    loadMoreButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const container = this.closest('.load-more-container');
            const hiddenItems = container.querySelectorAll('.item-hidden');
            const itemsToShow = 3;

            for (let i = 0; i < itemsToShow && i < hiddenItems.length; i++) {
                hiddenItems[i].classList.remove('item-hidden');
                hiddenItems[i].classList.add('item-visible');
            }

            // Hide button if no more items
            const remaining = container.querySelectorAll('.item-hidden').length;
            if (remaining === 0) {
                this.style.display = 'none';
            }
        });
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    enhanceForms();
    setupLoadMore();

    // Rating stars
    document.querySelectorAll('.rating-stars').forEach(function(container) {
        const rating = parseFloat(container.getAttribute('data-rating'));
        const stars = container.querySelectorAll('.star');

        stars.forEach(function(star, index) {
            if (index < Math.floor(rating)) {
                star.classList.add('fas', 'text-warning');
                star.classList.remove('far');
            } else if (index < rating) {
                star.classList.add('fas', 'fa-star-half-alt', 'text-warning');
                star.classList.remove('far', 'fa-star');
            }
        });
    });
});

// Utility function for making AJAX requests
function makeRequest(url, method = 'GET', data = null) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options);
}