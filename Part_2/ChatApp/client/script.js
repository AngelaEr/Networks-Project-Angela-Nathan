/**
 * Chat Application Client
 * WebSocket client for real-time chat communication
 */

// DOM Elements
const connectForm = document.getElementById('connect-form');
const chatArea = document.getElementById('chat-area');
const statusEl = document.getElementById('status');
const usernameInput = document.getElementById('username');
const serverAddressInput = document.getElementById('server-address');
const connectBtn = document.getElementById('connect-btn');
const disconnectBtn = document.getElementById('disconnect-btn');
const messagesEl = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const clientCountEl = document.getElementById('client-count');
const userListEl = document.getElementById('user-list');
const pageTitleEl = document.getElementById('page-title');

// State
let ws = null;
let username = '';

// Set default server address to current host
serverAddressInput.value = window.location.host || 'localhost:10000';

/**
 * Update connection status display
 */
function setStatus(status) {
    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusEl.className = 'status ' + status;
}

/**
 * Add a message to the chat display
 */
function addMessage(sender, text, time, type = 'other') {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + type;

    if (type === 'system') {
        messageDiv.textContent = text;
    } else {
        const senderDiv = document.createElement('div');
        senderDiv.className = 'sender';
        senderDiv.textContent = sender;

        const textDiv = document.createElement('div');
        textDiv.className = 'text';
        textDiv.textContent = text;

        const timeDiv = document.createElement('div');
        timeDiv.className = 'time';
        timeDiv.textContent = time;

        messageDiv.appendChild(senderDiv);
        messageDiv.appendChild(textDiv);
        messageDiv.appendChild(timeDiv);
    }

    messagesEl.appendChild(messageDiv);

    // Auto-scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Get current timestamp in HH:MM:SS format
 */
function getTimestamp() {
    const now = new Date();
    return now.toTimeString().split(' ')[0];
}

/**
 * Update the connected users display
 */
function updateUserList(count, users) {
    clientCountEl.textContent = count;
    if (users && users.length > 0) {
        userListEl.textContent = users.join(', ');
    } else {
        userListEl.textContent = '';
    }
}

/**
 * Connect to WebSocket server
 */
function connect() {
    username = usernameInput.value.trim();
    const serverAddress = serverAddressInput.value.trim();

    if (!username) {
        alert('Please enter a username');
        usernameInput.focus();
        return;
    }

    if (!serverAddress) {
        alert('Please enter server address');
        serverAddressInput.focus();
        return;
    }

    setStatus('connecting');
    connectBtn.disabled = true;

    try {
        // Create WebSocket connection
        ws = new WebSocket('ws://' + serverAddress);

        ws.onopen = function () {
            console.log('[WS] Connected to server');
            setStatus('connected');

            // Update page title
            pageTitleEl.textContent = 'Chat Room';

            // Show chat area, hide connect form
            connectForm.classList.add('hidden');
            chatArea.classList.remove('hidden');

            // Send join message with username
            ws.send(username + '|JOIN|' + getTimestamp());

            // Focus message input
            messageInput.focus();
        };

        ws.onmessage = function (event) {
            console.log('[WS] Received:', event.data);

            // Parse message: "SENDER|MESSAGE|TIMESTAMP" or "USERLIST|count|users"
            const parts = event.data.split('|');

            // Handle user list updates
            if (parts[0] === 'USERLIST' && parts.length >= 3) {
                const count = parseInt(parts[1]);
                const users = parts[2] ? parts[2].split(',') : [];
                updateUserList(count, users);
                return;
            }

            if (parts.length >= 3) {
                const sender = parts[0];
                const message = parts[1];
                const timestamp = parts[2];

                // Determine message type
                let type = 'other';
                if (sender === 'SYSTEM') {
                    type = 'system';
                } else if (sender === username) {
                    type = 'user';
                }

                addMessage(sender, message, timestamp, type);
            }
        };

        ws.onclose = function (event) {
            console.log('[WS] Connection closed:', event.code, event.reason);
            handleDisconnect();
        };

        ws.onerror = function (error) {
            console.error('[WS] Error:', error);
            alert('Connection error. Make sure the server is running.');
            handleDisconnect();
        };

    } catch (error) {
        console.error('[WS] Failed to connect:', error);
        alert('Failed to connect: ' + error.message);
        handleDisconnect();
    }
}

/**
 * Disconnect from WebSocket server
 */
function disconnect() {
    if (ws) {
        // Send leave message
        ws.send(username + '|LEAVE|' + getTimestamp());
        ws.close();
    }
    handleDisconnect();
}

/**
 * Handle disconnection (cleanup)
 */
function handleDisconnect() {
    setStatus('disconnected');
    connectBtn.disabled = false;

    // Update page title
    pageTitleEl.textContent = 'Sign In';

    // Show connect form, hide chat area
    connectForm.classList.remove('hidden');
    chatArea.classList.add('hidden');

    // Clear messages and user list
    messagesEl.innerHTML = '';
    updateUserList(0, []);

    ws = null;
}

/**
 * Send a chat message
 */
function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }

    // Format: "USERNAME|MESSAGE|TIMESTAMP"
    const formatted = username + '|' + message + '|' + getTimestamp();
    ws.send(formatted);

    // Clear input
    messageInput.value = '';
    messageInput.focus();
}

// Event Listeners
connectBtn.addEventListener('click', connect);
disconnectBtn.addEventListener('click', disconnect);
sendBtn.addEventListener('click', sendMessage);

// Connect on Enter in username field
usernameInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        connect();
    }
});

// Send on Enter in message field
messageInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Also allow Enter on server address field
serverAddressInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        connect();
    }
});
