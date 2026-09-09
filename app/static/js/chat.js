let activeChatOrderId = null;
let chatSocket = null;
let chatIsOpen = false;

function showChatButtonForOrder(orderId, restaurantName, restaurantImage) {
    activeChatOrderId = orderId;
    const nameEl = document.getElementById('chatRestaurantName');
    if (nameEl && restaurantName) {
        nameEl.innerText = restaurantName;
    }
    const avatarEl = document.getElementById('chatRestaurantAvatar');
    if (avatarEl && restaurantImage) {
        avatarEl.src = restaurantImage;
    }
    const orderTitle = document.getElementById('chatOrderTitle');
    if (orderTitle && orderId) {
        orderTitle.innerText = 'Đơn #' + orderId;
    }
}

function toggleChatWidget() {
    const widget = document.getElementById('floatingChatWidget');
    if (!widget) return;

    if (chatIsOpen) {
        closeChatWidget();
    } else {
        openChatWidget();
    }
}

function openChatWidget() {
    const widget = document.getElementById('floatingChatWidget');
    if (!widget) return;

    widget.style.display = 'flex';
    chatIsOpen = true;

    if (activeChatOrderId && (!chatSocket || chatSocket.readyState !== WebSocket.OPEN)) {
        connectChatWebSocket(activeChatOrderId);
    }

    const input = document.getElementById('chatInput');
    if (input) {
        setTimeout(() => input.focus(), 150);
    }
}

function closeChatWidget() {
    const widget = document.getElementById('floatingChatWidget');
    if (widget) {
        widget.style.display = 'none';
    }
    chatIsOpen = false;
    disconnectChatWebSocket();
}

function connectChatWebSocket(orderId) {
    disconnectChatWebSocket();
    if (!orderId) return;

    const protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://';
    const socketUrl = protocol + location.host + '/ws/chat/' + orderId;

    try {
        chatSocket = new WebSocket(socketUrl);
    } catch (e) {
        return;
    }

    chatSocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data && data.message) {
                appendChatMessage(data);
            }
        } catch (err) {}
    };

    chatSocket.onclose = function() {
        chatSocket = null;
    };

    chatSocket.onerror = function() {
        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;
        }
    };
}

function disconnectChatWebSocket() {
    if (chatSocket) {
        try {
            chatSocket.close();
        } catch (e) {}
        chatSocket = null;
    }
}

function openChatWithOrder(orderId, restaurantName, restaurantImage) {
    showChatButtonForOrder(orderId, restaurantName, restaurantImage);
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
        container.innerHTML = `
            <div id="chatEmptyPlaceholder" style="text-align: center; color: #888; font-size: 13px; margin: auto; padding: 20px;">
                <i class="fa-solid fa-comments" style="font-size: 32px; color: #d4c5a9; margin-bottom: 8px; display: block;"></i>
                Bắt đầu trò chuyện trực tiếp với nhà hàng về đơn hàng.
            </div>
        `;
    }
    connectChatWebSocket(orderId);
    openChatWidget();
}

function appendChatMessage(msg) {
    const container = document.getElementById('chatMessagesContainer');
    if (!container) return;

    const placeholder = document.getElementById('chatEmptyPlaceholder');
    if (placeholder) {
        placeholder.remove();
    }

    if (document.querySelector(`[data-msg-id="${msg.id}"]`)) return;

    const widget = document.getElementById('floatingChatWidget');
    const myUserId = widget ? widget.getAttribute('data-current-user-id') : null;
    const isMe = (myUserId && String(msg.sender_id) === String(myUserId));

    const row = document.createElement('div');
    row.className = 'chat-msg-row ' + (isMe ? 'me' : 'other');
    row.setAttribute('data-msg-id', msg.id);

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerText = msg.message;

    const info = document.createElement('div');
    info.className = 'chat-msg-info';

    let senderLabel = isMe ? 'Bạn' : (msg.sender_name || 'Người gửi');
    if (!isMe && msg.is_restaurant) {
        senderLabel += ' (Quán)';
    }

    info.innerHTML = `<span>${senderLabel}</span> • <span>${msg.created_at}</span>`;

    row.appendChild(bubble);
    row.appendChild(info);
    container.appendChild(row);
    container.scrollTop = container.scrollHeight;
}

function sendChatMessage() {
    if (!activeChatOrderId) return;

    const input = document.getElementById('chatInput');
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
        connectChatWebSocket(activeChatOrderId);
        setTimeout(() => {
            if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({ message: text }));
                input.value = '';
                input.focus();
            } else {
                alert('Không thể kết nối websocket với phòng chat. Vui lòng thử lại!');
            }
        }, 500);
        return;
    }

    chatSocket.send(JSON.stringify({ message: text }));
    input.value = '';
    input.focus();
}

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chatInput');
    if (input) {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});

window.showChatButtonForOrder = showChatButtonForOrder;
window.openChatWithOrder = openChatWithOrder;
window.toggleChatWidget = toggleChatWidget;
window.openChatWidget = openChatWidget;
window.closeChatWidget = closeChatWidget;
window.sendChatMessage = sendChatMessage;
window.connectChatWebSocket = connectChatWebSocket;
window.disconnectChatWebSocket = disconnectChatWebSocket;
