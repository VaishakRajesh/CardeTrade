/*
 * CardeTrade — AI Chatbot Widget
 * ================================
 * Manages the floating AI chatbot interface on the platform.
 * Handles toggling the chat panel open/closed, sending user
 * messages to the server via POST /chat/api/, and displaying
 * both messages and typing indicators in the chat log.
 */

(function () {
    'use strict';

    // ==========================================================
    // DOM REFERENCES — Cache elements used throughout the widget
    // ==========================================================
    const chatLog = document.getElementById('chatLog');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatToggle = document.getElementById('chatToggle');
    const chatPanel = document.getElementById('chatPanel');
    const chatBadge = document.getElementById('chatBadge');
    const chatClose = document.getElementById('chatClose');

    // Bail out if required elements are missing from the DOM
    if (!chatLog || !chatInput || !chatSend) return;

    // ==========================================================
    // addMessage — Append a message bubble to the chat log
    //     text:   The message content (plain text)
    //     sender: 'user' or 'bot' — controls CSS class & style
    // ==========================================================
    function addMessage(text, sender) {
        const msg = document.createElement('div');
        msg.className = 'chat-msg chat-msg-' + sender;
        msg.textContent = text;
        chatLog.appendChild(msg);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // ==========================================================
    // addTyping — Insert a "bot is typing" animation indicator
    //     Adds three animated dots inside the chat log while
    //     waiting for the server response.
    // ==========================================================
    function addTyping() {
        const el = document.createElement('div');
        el.className = 'chat-msg chat-msg-bot chat-typing';
        el.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        el.id = 'chatTyping';
        chatLog.appendChild(el);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // ==========================================================
    // removeTyping — Remove the typing indicator from the log
    //     Called when the server response is received or on
    //     error, so the real bot reply can be shown instead.
    // ==========================================================
    function removeTyping() {
        const el = document.getElementById('chatTyping');
        if (el) el.remove();
    }

    // ==========================================================
    // getCookie — Read a named cookie value from document.cookie
    //     Used to retrieve the CSRF token required by Django
    //     for POST requests.
    // ==========================================================
    function getCookie(name) {
        let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    // ==========================================================
    // sendMessage — Send the user's message to the chatbot API
    //     1. Reads and trims the input value
    //     2. Clears the input, shows user message & typing dots
    //     3. POSTs to /chat/api/ with CSRF protection
    //     4. On success: removes typing dots, shows bot reply
    //     5. On error: removes typing dots, shows error message
    // ==========================================================
    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        addMessage(text, 'user');
        addTyping();

        fetch('/chat/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ message: text }),
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            removeTyping();
            addMessage(data.response || 'No response received.', 'bot');
        })
        .catch(function () {
            removeTyping();
            addMessage('Connection error. Please try again.', 'bot');
        });
    }

    // ==========================================================
    // EVENT LISTENERS — Wire up the send button & Enter key
    //     Clicking #chatSend or pressing Enter (without Shift)
    //     triggers sendMessage().
    // ==========================================================
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // ==========================================================
    // TOGGLE WIDGET — Open/close the chat panel on toggle click
    //     Also focuses the input when the panel opens.
    // ==========================================================
    if (chatToggle && chatPanel) {
        chatToggle.addEventListener('click', function () {
            var isOpen = chatPanel.classList.contains('open');
            chatPanel.classList.toggle('open');
            chatToggle.classList.toggle('hidden');
            if (!isOpen) chatInput.focus();
        });
    }

    // ==========================================================
    // CLOSE BUTTON — Dismiss the chat panel via the X button
    // ==========================================================
    if (chatClose) {
        chatClose.addEventListener('click', function () {
            chatPanel.classList.remove('open');
            chatToggle.classList.remove('hidden');
        });
    }
})();
