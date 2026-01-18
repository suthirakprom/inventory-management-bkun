// Session Management Utilities for StockMinds Inventory System
// Handles session storage, validation, inactivity tracking, and logout

const SESSION_KEY = 'stockminds_session';
const INACTIVITY_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
const WARNING_TIME = 10 * 60 * 1000; // Show warning 10 minutes before logout

let inactivityTimer = null;
let warningTimer = null;

/**
 * Get current session from storage
 * @returns {Object|null} Session object or null if not found
 */
function getSession() {
    const rememberMe = localStorage.getItem(SESSION_KEY);
    const sessionData = sessionStorage.getItem(SESSION_KEY);

    const data = rememberMe || sessionData;
    if (!data) return null;

    try {
        return JSON.parse(data);
    } catch (e) {
        console.error('Error parsing session data:', e);
        return null;
    }
}

/**
 * Store session data
 * @param {Object} user - User object from login response
 * @param {string} token - Session token
 * @param {boolean} rememberMe - Whether to persist session
 */
function setSession(user, token, rememberMe = false) {
    const sessionData = {
        user_id: user.user_id || user.User_ID,
        username: user.username || user.Username,
        role: user.role || user.Role,
        email: user.email || user.Email,
        login_time: new Date().toISOString(),
        session_token: token,
        remember_me: rememberMe
    };

    const dataString = JSON.stringify(sessionData);

    if (rememberMe) {
        localStorage.setItem(SESSION_KEY, dataString);
    } else {
        sessionStorage.setItem(SESSION_KEY, dataString);
    }

    // Start inactivity timer
    startInactivityTimer();
}

/**
 * Clear all session data
 */
function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(SESSION_KEY);

    // Clear timers
    if (inactivityTimer) clearTimeout(inactivityTimer);
    if (warningTimer) clearTimeout(warningTimer);
}

/**
 * Check if session exists and is valid
 * @returns {boolean} True if session is valid
 */
function isSessionValid() {
    const session = getSession();
    if (!session) return false;

    // Check if token exists
    if (!session.session_token) return false;

    // Additional validation can be added here (e.g., expiration check)
    return true;
}

/**
 * Start inactivity timer
 */
function startInactivityTimer() {
    // Clear existing timers
    if (inactivityTimer) clearTimeout(inactivityTimer);
    if (warningTimer) clearTimeout(warningTimer);

    // Set warning timer (show warning 2 minutes before logout)
    warningTimer = setTimeout(() => {
        showInactivityWarning();
    }, INACTIVITY_TIMEOUT - WARNING_TIME);

    // Set logout timer
    inactivityTimer = setTimeout(() => {
        handleInactivityLogout();
    }, INACTIVITY_TIMEOUT);
}

/**
 * Reset inactivity timer on user activity
 */
function resetInactivityTimer() {
    startInactivityTimer();

    // Hide warning if it's showing
    const warningElement = document.getElementById('inactivity-warning');
    if (warningElement) {
        warningElement.remove();
    }
}

/**
 * Show inactivity warning to user
 */
function showInactivityWarning() {
    // Remove existing warning if any
    const existingWarning = document.getElementById('inactivity-warning');
    if (existingWarning) existingWarning.remove();

    // Create warning element
    const warning = document.createElement('div');
    warning.id = 'inactivity-warning';
    warning.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #1e293b;
        border: 2px solid #f59e0b;
        border-radius: 0.75rem;
        padding: 1.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        z-index: 10000;
        max-width: 350px;
        animation: slideIn 0.3s ease-out;
    `;

    warning.innerHTML = `
        <div style="color: #f59e0b; font-weight: 600; margin-bottom: 0.5rem; font-size: 1rem;">
            ⚠️ Inactivity Warning
        </div>
        <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1rem;">
            You will be logged out in 10 minutes due to inactivity.
        </div>
        <button onclick="stayLoggedIn()" style="
            background: #10b981;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-weight: 600;
            width: 100%;
        ">Stay Logged In</button>
    `;

    document.body.appendChild(warning);
}

/**
 * Handle stay logged in action
 */
function stayLoggedIn() {
    resetInactivityTimer();

    const warning = document.getElementById('inactivity-warning');
    if (warning) warning.remove();
}

/**
 * Handle inactivity logout
 */
function handleInactivityLogout() {
    clearSession();
    alert('You have been logged out due to inactivity.');
    window.location.href = 'login.html?reason=inactivity';
}

/**
 * Logout user and redirect to login page
 * @param {string} message - Optional message to show on login page
 */
async function logout(message = 'Logged out successfully') {
    const session = getSession();

    // Call backend logout endpoint if we have a session
    if (session && session.session_token) {
        try {
            await fetch('/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.session_token}`
                }
            });
        } catch (e) {
            console.error('Error calling logout endpoint:', e);
            // Continue with logout even if API call fails
        }
    }

    // Clear session
    clearSession();

    // Redirect to login page with message
    const params = new URLSearchParams({ message: message });
    window.location.href = `login.html?${params.toString()}`;
}

/**
 * Get authorization header for API calls
 * @returns {Object} Headers object with Authorization
 */
function getAuthHeaders() {
    const session = getSession();
    if (!session || !session.session_token) {
        return {};
    }

    return {
        'Authorization': `Bearer ${session.session_token}`
    };
}

/**
 * Initialize session management on page load
 * Should be called when the page loads (not on login page)
 */
function initSessionManagement() {
    // Check if session is valid
    if (!isSessionValid()) {
        // Redirect to login if not on login page
        if (!window.location.pathname.includes('login.html')) {
            window.location.href = 'login.html?reason=no_session';
        }
        return;
    }

    // Start inactivity timer
    startInactivityTimer();

    // Listen for user activity to reset timer
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
        document.addEventListener(event, resetInactivityTimer, { passive: true });
    });
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.getSession = getSession;
    window.setSession = setSession;
    window.clearSession = clearSession;
    window.isSessionValid = isSessionValid;
    window.logout = logout;
    window.getAuthHeaders = getAuthHeaders;
    window.initSessionManagement = initSessionManagement;
    window.stayLoggedIn = stayLoggedIn;
    window.resetInactivityTimer = resetInactivityTimer;
}
