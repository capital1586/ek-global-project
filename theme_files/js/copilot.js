/**
 * Crypto Copilot JavaScript
 * Handles the interaction between the UI and the backend API
 */

// Chat history storage
let chatHistory = [];
const MAX_CHAT_HISTORY = 50;

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the copilot
    initCopilot();
    
    // Fetch initial crypto data
    fetchCryptoData();
    
    // Fetch recent queries
    fetchRecentQueries();
});

/**
 * Initialize the copilot UI and event handlers
 */
function initCopilot() {
    // Form submission handlers
    const copilotForm = document.getElementById('copilotForm');
    const copilotFullscreenForm = document.getElementById('copilotFullscreenForm');
    
    if (copilotForm) {
        copilotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('copilotQuery').value.trim();
            if (query) {
                processQuery(query, 'sidebar');
                document.getElementById('copilotQuery').value = '';
                updateCharCounter();
            }
        });
    }
    
    if (copilotFullscreenForm) {
        copilotFullscreenForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.getElementById('copilotFullscreenQuery').value.trim();
            if (query) {
                processQuery(query, 'fullscreen');
                document.getElementById('copilotFullscreenQuery').value = '';
                updateFullscreenCharCounter();
            }
        });
    }
    
    // Character counter functionality
    const copilotQuery = document.getElementById('copilotQuery');
    const fullscreenQuery = document.getElementById('copilotFullscreenQuery');
    
    if (copilotQuery) {
        copilotQuery.addEventListener('input', updateCharCounter);
        updateCharCounter();
    }
    
    if (fullscreenQuery) {
        fullscreenQuery.addEventListener('input', updateFullscreenCharCounter);
        updateFullscreenCharCounter();
    }
    
    // Suggestion click handlers
    setupSuggestionHandlers();
    
    // Initialize UI controls
    setupUIControls();
}

/**
 * Setup UI controls for the copilot
 */
function setupUIControls() {
    const askCopilotBtn = document.getElementById('askCopilotBtn');
    const closeCopilotBtn = document.getElementById('closeCopilotBtn');
    const minimizeCopilotBtn = document.getElementById('minimizeCopilotBtn');
    const closeFullscreenBtn = document.getElementById('closeFullscreenBtn');
    const copilotOverlay = document.getElementById('copilotOverlay');
    const copilotSidebar = document.getElementById('copilotSidebar');
    const copilotFullscreen = document.getElementById('copilotFullscreen');
    
    // Function to open the sidebar
    function openSidebar() {
        if (copilotOverlay && copilotSidebar) {
            copilotOverlay.classList.add('active');
            copilotSidebar.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Focus on the input field
            setTimeout(() => {
                const inputField = document.getElementById('copilotQuery');
                if (inputField) {
                    inputField.focus();
                }
            }, 300);
        }
    }
    
    // Function to close the sidebar
    function closeSidebar() {
        if (copilotOverlay && copilotSidebar) {
            copilotOverlay.classList.remove('active');
            copilotSidebar.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Function to open fullscreen mode
    function openFullscreen() {
        if (copilotFullscreen) {
            copilotFullscreen.classList.add('active');
            closeSidebar();
            document.body.style.overflow = 'hidden';
            
            // Focus on the input field
            setTimeout(() => {
                const inputField = document.getElementById('copilotFullscreenQuery');
                if (inputField) {
                    inputField.focus();
                }
            }, 300);
        }
    }
    
    // Function to close fullscreen mode
    function closeFullscreen() {
        if (copilotFullscreen) {
            copilotFullscreen.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Add click event to the button
    if (askCopilotBtn) {
        askCopilotBtn.addEventListener('click', openSidebar);
    }
    
    // Close sidebar when clicking the close button
    if (closeCopilotBtn) {
        closeCopilotBtn.addEventListener('click', closeSidebar);
    }
    
    // Close sidebar when clicking outside
    if (copilotOverlay) {
        copilotOverlay.addEventListener('click', function(e) {
            // Only close if clicking directly on the overlay, not on its children
            if (e.target === copilotOverlay) {
                closeSidebar();
            }
        });
    }
    
    // Switch to fullscreen mode
    if (minimizeCopilotBtn) {
        minimizeCopilotBtn.addEventListener('click', openFullscreen);
    }
    
    // Close fullscreen mode
    if (closeFullscreenBtn) {
        closeFullscreenBtn.addEventListener('click', closeFullscreen);
    }
}

/**
 * Process a user query
 * @param {string} query - The user's query
 * @param {string} mode - 'sidebar' or 'fullscreen'
 */
function processQuery(query, mode) {
    // Add user message to chat
    addMessageToHistory(query, 'user');
    
    // Update UI
    const historyContainer = mode === 'sidebar' 
        ? document.getElementById('copilotChatHistory')
        : document.getElementById('copilotFullscreenChatHistory');
    
    if (!historyContainer) {
        console.error('Chat history container not found');
        return;
    }
    
    updateChatUI(historyContainer);
    
    // Show loading indicator
    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'history-item copilot-message';
    loadingMessage.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    historyContainer.appendChild(loadingMessage);
    historyContainer.scrollTop = historyContainer.scrollHeight;
    
    // Get CSRF token
    const csrftoken = getCookie('csrftoken');
    
    // Call API
    fetch('/copilot/api/process-query/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        // Remove loading indicator
        if (historyContainer.contains(loadingMessage)) {
            historyContainer.removeChild(loadingMessage);
        }
        
        if (data.status === 'success') {
            // Add AI response to chat
            addMessageToHistory(data.response, 'copilot');
            updateChatUI(historyContainer);
        } else {
            // Handle error
            addMessageToHistory("Sorry, I encountered an error processing your request. Please try again.", 'copilot');
            updateChatUI(historyContainer);
            console.error('Error:', data.message);
        }
    })
    .catch(error => {
        // Remove loading indicator
        if (historyContainer.contains(loadingMessage)) {
            historyContainer.removeChild(loadingMessage);
        }
        
        // Handle network error
        addMessageToHistory("Sorry, there was a network error. Please check your connection and try again.", 'copilot');
        updateChatUI(historyContainer);
        console.error('Network Error:', error);
    });
}

/**
 * Add a message to the chat history
 * @param {string} message - The message text
 * @param {string} sender - 'user' or 'copilot'
 */
function addMessageToHistory(message, sender) {
    chatHistory.push({
        message: message,
        sender: sender,
        timestamp: new Date().toISOString()
    });
    
    // Limit chat history size
    if (chatHistory.length > MAX_CHAT_HISTORY) {
        chatHistory.shift();
    }
}

/**
 * Update the chat UI based on chat history
 * @param {HTMLElement} historyContainer - The container element for the chat history
 */
function updateChatUI(historyContainer) {
    if (!historyContainer) return;
    
    // Clear the container
    historyContainer.innerHTML = '';
    
    // Add messages from chat history
    chatHistory.forEach(item => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `history-item ${item.sender === 'user' ? 'user-message' : 'copilot-message'}`;
        
        // Format the message text (handle newlines)
        const formattedMessage = item.message.replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-timestamp">${formatTimestamp(item.timestamp)}</div>
        `;
        
        historyContainer.appendChild(messageDiv);
    });
    
    // Scroll to bottom
    historyContainer.scrollTop = historyContainer.scrollHeight;
}

/**
 * Format timestamp for display
 * @param {string} timestamp - ISO timestamp
 * @returns {string} - Formatted time string
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

/**
 * Update character counter for sidebar input
 */
function updateCharCounter() {
    const input = document.getElementById('copilotQuery');
    const counter = document.querySelector('.char-counter');
    
    if (input && counter) {
        const length = input.value.length;
        counter.textContent = `${length}/500`;
        
        // Add warning class if approaching limit
        if (length > 450) {
            counter.classList.add('char-warning');
        } else {
            counter.classList.remove('char-warning');
        }
    }
}

/**
 * Update character counter for fullscreen input
 */
function updateFullscreenCharCounter() {
    const input = document.getElementById('copilotFullscreenQuery');
    const counter = document.querySelector('.copilot-fullscreen-char-counter');
    
    if (input && counter) {
        const length = input.value.length;
        counter.textContent = `${length}/500`;
        
        // Add warning class if approaching limit
        if (length > 450) {
            counter.classList.add('char-warning');
        } else {
            counter.classList.remove('char-warning');
        }
    }
}

/**
 * Fetch crypto data from the API
 */
function fetchCryptoData() {
    fetch('/copilot/api/crypto-data/?limit=10')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateCryptoDataUI(data.data);
            } else {
                console.error('Error fetching crypto data:', data.message);
                document.getElementById('cryptoDataContainer').innerHTML = 
                    '<div class="error-message">Failed to load cryptocurrency data. Please try again later.</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('cryptoDataContainer').innerHTML = 
                '<div class="error-message">Failed to load cryptocurrency data. Please try again later.</div>';
        });
}

/**
 * Update the UI with crypto data
 * @param {Array} cryptoData - Array of crypto asset data
 */
function updateCryptoDataUI(cryptoData) {
    const container = document.getElementById('cryptoDataContainer');
    
    if (!container) return;
    
    if (!cryptoData || cryptoData.length === 0) {
        container.innerHTML = '<div class="no-data-message">No cryptocurrency data available at the moment.</div>';
        return;
    }
    
    let html = '<div class="crypto-list">';
    
    cryptoData.forEach(crypto => {
        // Format price change with color
        const priceChangeClass = crypto.price_change_24h >= 0 ? 'price-up' : 'price-down';
        const priceChangeIcon = crypto.price_change_24h >= 0 ? '↑' : '↓';
        const priceChangeFormatted = `${priceChangeIcon} ${Math.abs(crypto.price_change_24h).toFixed(2)}%`;
        
        html += `
            <div class="crypto-item">
                <div class="crypto-icon">
                    <img src="${crypto.image_url}" alt="${crypto.symbol}" onerror="this.src='/static/img/crypto-default.png'">
                </div>
                <div class="crypto-info">
                    <div class="crypto-name">${crypto.name} <span class="crypto-symbol">${crypto.symbol}</span></div>
                    <div class="crypto-price">$${crypto.current_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                </div>
                <div class="crypto-change ${priceChangeClass}">
                    ${priceChangeFormatted}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Fetch recent queries from the API
 */
function fetchRecentQueries() {
    fetch('/copilot/api/recent-queries/?limit=5')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                updateRecentQueriesUI(data.data);
            } else {
                console.error('Error fetching recent queries:', data.message);
                document.getElementById('recentQueriesContainer').innerHTML = 
                    '<div class="error-message">Failed to load recent queries. Please try again later.</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('recentQueriesContainer').innerHTML = 
                '<div class="error-message">Failed to load recent queries. Please try again later.</div>';
        });
}

/**
 * Update the UI with recent queries
 * @param {Array} queriesData - Array of recent query data
 */
function updateRecentQueriesUI(queriesData) {
    const container = document.getElementById('recentQueriesContainer');
    
    if (!container) return;
    
    if (!queriesData || queriesData.length === 0) {
        container.innerHTML = '<div class="no-data-message">No recent queries yet. Ask something to get started!</div>';
        return;
    }
    
    let html = '<div class="queries-list">';
    
    queriesData.forEach(query => {
        const date = new Date(query.created_at);
        const formattedDate = date.toLocaleString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        html += `
            <div class="query-item" onclick="selectSuggestion('${query.user_query.replace(/'/g, "\\'")}')">
                <div class="query-text">${query.user_query}</div>
                <div class="query-time">${formattedDate}</div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Setup click handlers for suggestion buttons
 */
function setupSuggestionHandlers() {
    // This is handled by the onclick attributes in the HTML
    // But we could add dynamic suggestion handling here if needed
}

/**
 * Select a suggestion and populate the input field
 * @param {string} text - The suggestion text
 */
function selectSuggestion(text) {
    const input = document.getElementById('copilotQuery');
    if (input) {
        input.value = text;
        updateCharCounter();
        input.focus();
    }
}

/**
 * Select a fullscreen suggestion and populate the input field
 * @param {string} text - The suggestion text
 */
function selectFullscreenQuestion(text) {
    const input = document.getElementById('copilotFullscreenQuery');
    if (input) {
        input.value = text;
        updateFullscreenCharCounter();
        input.focus();
    }
}

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name
 * @returns {string} - Cookie value
 */
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
