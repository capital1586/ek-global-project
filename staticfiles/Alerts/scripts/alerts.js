/**
 * Alerts Management JavaScript
 * Handles CRUD operations and UI interactions for the alerts system
 */

document.addEventListener('DOMContentLoaded', function() {
    // Constants
    const API_ENDPOINTS = {
        ALERTS: '/alerts/api/alerts/',
        NOTIFY: '/alerts/api/notify/'
    };
    
    // UI Elements
    const statusFilter = document.getElementById('statusFilter');
    const conditionFilter = document.getElementById('conditionFilter');
    const symbolSearch = document.getElementById('symbolSearch');
    const portfolioFilter = document.getElementById('portfolioFilter');
    const alertsTable = document.getElementById('alertsTable');
    const notificationSound = document.getElementById('notificationSound');
    const createAlertModal = document.getElementById('createAlertModal');
    const toastEl = document.getElementById('notificationToast');
    
    // Initialize Bootstrap components
    const deleteModal = document.getElementById('deleteAlertModal') ? 
        new bootstrap.Modal(document.getElementById('deleteAlertModal')) : null;
    const toast = toastEl ? new bootstrap.Toast(toastEl) : null;
    
    // Initialize event listeners
    initializeListeners();
    
    // Load and prepare notification sound
    preloadNotificationSound();
    
    /**
     * Initialize all event listeners
     */
    function initializeListeners() {
        // Condition type changes
        const conditionTypeSelect = document.getElementById('condition_type');
        if (conditionTypeSelect) {
            handleConditionTypeChanges(conditionTypeSelect);
        }
        
        // Delete alert buttons
        const deleteButtons = document.querySelectorAll('.delete-alert-btn');
        if (deleteButtons.length > 0) {
            setupDeleteButtons(deleteButtons);
        }
        
        // Filter controls
        if (statusFilter || conditionFilter || symbolSearch || portfolioFilter) {
            setupFilterControls();
        }
        
        // Trigger alert buttons
        const triggerButtons = document.querySelectorAll('.trigger-alert-btn');
        if (triggerButtons.length > 0) {
            setupTriggerButtons(triggerButtons);
        }
        
        // Portfolio selection in create form
        const portfolioSelect = document.getElementById('portfolio_id');
        if (portfolioSelect) {
            setupPortfolioSelect(portfolioSelect);
        }
        
        // Clear any stuck backdrops
        clearStuckBackdrops();
        
        // Theme toggle functionality
        setupThemeToggle();
    }
    
    /**
     * Preload notification sound for faster playback
     */
    function preloadNotificationSound() {
        if (notificationSound) {
            notificationSound.load();
            
            // Create a silent audio context to enable audio on first user interaction
            // This helps with browsers that block audio until user interaction
            document.addEventListener('click', function enableAudio() {
                document.removeEventListener('click', enableAudio);
                notificationSound.volume = 0;
                notificationSound.play().catch(() => {});
                notificationSound.pause();
                notificationSound.volume = 1;
            }, { once: true });
        }
    }
    
    /**
     * Setup theme toggle functionality
     */
    function setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                document.body.classList.toggle('dark-theme');
                const isDarkTheme = document.body.classList.contains('dark-theme');
                localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
            });
            
            // Apply saved theme
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
        }
    }
    
    /**
     * Handle condition type select changes to show/hide fields
     */
    function handleConditionTypeChanges(conditionTypeSelect) {
        const thresholdField = document.querySelector('.threshold-field');
        const customConditionField = document.querySelector('.custom-condition-field');
        
        function updateFieldVisibility() {
            if (conditionTypeSelect.value === 'custom') {
                thresholdField.style.display = 'none';
                customConditionField.style.display = 'block';
            } else {
                thresholdField.style.display = 'block';
                customConditionField.style.display = 'none';
            }
        }
        
        // Initial visibility
        updateFieldVisibility();
        
        // Update on change
        conditionTypeSelect.addEventListener('change', updateFieldVisibility);
    }
    
    /**
     * Setup delete confirmation buttons
     */
    function setupDeleteButtons(deleteButtons) {
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alertId = this.getAttribute('data-alert-id');
                if (confirmDeleteBtn) {
                    // Update the delete URL
                    const deleteUrl = confirmDeleteBtn.getAttribute('href').replace(/\/\d+\//, `/${alertId}/`);
                    confirmDeleteBtn.href = deleteUrl;
                    // Show the modal
                    deleteModal.show();
                }
            });
        });
    }
    
    /**
     * Set up portfolio selection in create alert form
     */
    function setupPortfolioSelect(portfolioSelect) {
        const symbolInput = document.getElementById('symbol');
        
        // If we have a portfolio that preselects a stock, update symbol
        portfolioSelect.addEventListener('change', function() {
            const portfolioId = this.value;
            
            // If portfolio is selected, we could fetch stocks in that portfolio
            // and either autofill or provide a dropdown
            if (portfolioId) {
                fetch(`/portfolio/${portfolioId}/stocks/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success' && data.stocks.length > 0) {
                            // Could create a dropdown here, but for now just focus the symbol field
                            symbolInput.focus();
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching portfolio stocks:', error);
                    });
            }
        });
    }
    
    /**
     * Setup filtering functionality
     */
    function setupFilterControls() {
        function filterAlerts() {
            if (!alertsTable) return;
            
            const status = statusFilter ? statusFilter.value : '';
            const condition = conditionFilter ? conditionFilter.value : '';
            const symbol = symbolSearch ? symbolSearch.value.toLowerCase() : '';
            const portfolio = portfolioFilter ? portfolioFilter.value : '';
            
            const rows = alertsTable.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                if (row.querySelector('.empty-state')) {
                    return; // Skip the empty state row
                }
                
                const rowStatus = row.querySelector('.status-badge')?.innerText.toLowerCase() || '';
                const rowCondition = row.querySelector('td:nth-child(4)')?.innerText.toLowerCase() || '';
                const rowSymbol = row.querySelector('td:nth-child(2)')?.innerText.toLowerCase() || '';
                const rowPortfolio = row.querySelector('td:nth-child(3) .badge')?.innerText.toLowerCase() || '';
                
                let statusMatch = true;
                let conditionMatch = true;
                let symbolMatch = true;
                let portfolioMatch = true;
                
                if (status && !rowStatus.includes(status.toLowerCase())) {
                    statusMatch = false;
                }
                
                if (condition && !rowCondition.includes(condition.toLowerCase())) {
                    conditionMatch = false;
                }
                
                if (symbol && !rowSymbol.includes(symbol)) {
                    symbolMatch = false;
                }
                
                if (portfolio && !rowPortfolio.includes(portfolio.toLowerCase())) {
                    portfolioMatch = false;
                }
                
                if (statusMatch && conditionMatch && symbolMatch && portfolioMatch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
        
        // Add event listeners for filtering
        if (statusFilter) statusFilter.addEventListener('change', filterAlerts);
        if (conditionFilter) conditionFilter.addEventListener('change', filterAlerts);
        if (symbolSearch) symbolSearch.addEventListener('input', filterAlerts);
        if (portfolioFilter) portfolioFilter.addEventListener('change', filterAlerts);
    }
    
    /**
     * Setup alert trigger buttons
     */
    function setupTriggerButtons(triggerButtons) {
        triggerButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alertId = this.getAttribute('data-alert-id');
                
                // Get the alert details for toast notification
                const row = document.querySelector(`tr[data-alert-id="${alertId}"]`);
                if (!row) return;
                
                const title = row.querySelector('td:first-child strong')?.innerText || 'Alert';
                const symbol = row.querySelector('td:nth-child(2)')?.innerText || '';
                
                // Trigger the alert
                triggerAlert(alertId, title, symbol);
            });
        });
    }
    
    /**
     * Trigger an alert - send to server and show notification
     */
    function triggerAlert(alertId, title, symbol) {
        // Update toast content
        if (toastEl) {
            const toastBody = document.getElementById('toastBody');
            const toastTime = document.getElementById('toastTime');
            
            if (toastBody) {
                toastBody.innerText = `Alert triggered: ${title} (${symbol})`;
            }
            
            if (toastTime) {
                toastTime.innerText = 'Just now';
            }
            
            // Show toast
            toast.show();
        }
        
        // Play sound
        playNotificationSound();
        
        // Send notification to server
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (csrfToken) {
            // Show loading state
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            fetch(API_ENDPOINTS.NOTIFY, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    alert_id: alertId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' || data.status === 'partial') {
                    if (data.status === 'partial') {
                        console.warn('Alert triggered with warnings:', data.message);
                    }
                    
                    // Update UI to reflect the new status after a delay
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    console.error('Error:', data.message);
                    // Reset button state
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-bell"></i>';
                }
            })
            .catch(error => {
                console.error('Error triggering alert:', error);
                // Reset button state
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-bell"></i>';
            });
        }
    }
    
    /**
     * Play notification sound with error handling
     */
    function playNotificationSound() {
        if (notificationSound) {
            // Clone the audio node to allow multiple plays
            try {
                // Try direct play first
                notificationSound.currentTime = 0;
                const playPromise = notificationSound.play();
                
                // Handle promise-based play API
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            // Play started successfully
                        })
                        .catch(e => {
                            console.warn("Could not play notification sound:", e);
                            // Fallback method for browsers with autoplay restrictions
                            const fallbackSound = new Audio('/static/Alerts/sounds/alert_notification.mp3');
                            fallbackSound.volume = 1.0;
                            fallbackSound.play().catch(() => {
                                console.warn("Fallback sound also failed to play");
                            });
                        });
                }
            } catch(e) {
                console.warn("Error playing notification sound:", e);
            }
        }
    }
    
    /**
     * Clear any stuck modal backdrops
     */
    function clearStuckBackdrops() {
        const stuckBackdrops = document.querySelectorAll('.modal-backdrop');
        stuckBackdrops.forEach(backdrop => {
            if (backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
            }
        });
        
        // Also make sure body doesn't have modal-open class if no modals are open
        const openModals = document.querySelectorAll('.modal.show');
        if (openModals.length === 0 && document.body.classList.contains('modal-open')) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }
    
    /**
     * Create a new alert via the API
     */
    function createAlert(formData) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (csrfToken) {
            fetch(API_ENDPOINTS.ALERTS, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Reload page to show new alert
                    location.reload();
                } else {
                    console.error('Error creating alert:', data.message);
                }
            })
            .catch(error => {
                console.error('Error creating alert:', error);
            });
        }
    }
    
    /**
     * Delete an alert via the API
     */
    function deleteAlert(alertId) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (csrfToken) {
            fetch(API_ENDPOINTS.ALERTS, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    id: alertId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Remove alert from DOM or reload page
                    location.reload();
                } else {
                    console.error('Error deleting alert:', data.message);
                }
            })
            .catch(error => {
                console.error('Error deleting alert:', error);
            });
        }
    }
}); 