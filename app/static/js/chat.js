let activeChatOrderId = null;
let activeChatPollTimer = null;
let lastChatMsgId = 0;
let isSendingChatMsg = false;
let chatIsOpen = false;

function initRealtimeChat() {
    fetch('/api/chat/active_order')
        .then(res => {
            if (!res.ok) return null;
            return res.json();
        })
        .then(data => {
            if (!data || !data.active) return;
            showChatButtonForOrder(data.order_id, data.restaurant_name, data.restaurant_image);
        })
        .catch(err => {});
}

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

    const badge = document.getElementById('floatingChatBadge');
    if (badge) {
        badge.style.display = 'none';
        badge.innerText = '0';
    }

    if (activeChatOrderId) {
        loadChatMessages(activeChatOrderId, true);
        startChatPolling(activeChatOrderId);
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
    stopChatPolling();
}

function openChatWithOrder(orderId, restaurantName, restaurantImage) {
    showChatButtonForOrder(orderId, restaurantName, restaurantImage);
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
        container.innerHTML = `
            <div id="chatEmptyPlaceholder" style="text-align: center; color: #888; font-size: 13px; margin: auto; padding: 20px;">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 28px; color: #cda434; margin-bottom: 8px; display: block;"></i>
                Đang tải tin nhắn...
            </div>
        `;
    }
    lastChatMsgId = 0;
    openChatWidget();
}

function renderMessageRow(msg) {
    const row = document.createElement('div');
    row.className = 'chat-msg-row ' + (msg.is_me ? 'me' : 'other');
    row.setAttribute('data-msg-id', msg.id);

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerText = msg.message;

    const info = document.createElement('div');
    info.className = 'chat-msg-info';

    let senderLabel = msg.is_me ? 'Bạn' : (msg.sender_name || 'Người gửi');
    if (!msg.is_me && msg.is_restaurant) {
        senderLabel += ' (Quán)';
    }

    info.innerHTML = `<span>${senderLabel}</span> • <span>${msg.created_at}</span>`;

    row.appendChild(bubble);
    row.appendChild(info);
    return row;
}

function loadChatMessages(orderId, scrollToBottom = false) {
    if (!orderId) return;

    fetch(`/api/chat/${orderId}/messages?after_id=${lastChatMsgId}`)
        .then(res => {
            if (!res.ok) return null;
            return res.json();
        })
        .then(data => {
            if (!data || !data.messages) return;

            const container = document.getElementById('chatMessagesContainer');
            if (!container) return;

            const placeholder = document.getElementById('chatEmptyPlaceholder');

            if (data.restaurant_name) {
                const nameEl = document.getElementById('chatRestaurantName');
                if (nameEl) nameEl.innerText = data.restaurant_name;
            }
            if (data.restaurant_image) {
                const avatarEl = document.getElementById('chatRestaurantAvatar');
                if (avatarEl) avatarEl.src = data.restaurant_image;
            }

            if (data.messages.length > 0) {
                if (placeholder) {
                    placeholder.remove();
                }

                data.messages.forEach(msg => {
                    if (document.querySelector(`[data-msg-id="${msg.id}"]`)) return;
                    const el = renderMessageRow(msg);
                    container.appendChild(el);
                    if (msg.id > lastChatMsgId) {
                        lastChatMsgId = msg.id;
                    }
                });

                if (scrollToBottom) {
                    container.scrollTop = container.scrollHeight;
                }
            } else if (lastChatMsgId === 0 && !container.querySelector('.chat-msg-row')) {
                if (!placeholder) {
                    container.innerHTML = `
                        <div id="chatEmptyPlaceholder" style="text-align: center; color: #888; font-size: 13px; margin: auto; padding: 20px;">
                            <i class="fa-solid fa-comments" style="font-size: 32px; color: #d4c5a9; margin-bottom: 8px; display: block;"></i>
                            Bắt đầu trò chuyện với nhà hàng về đơn hàng của bạn.
                        </div>
                    `;
                }
            }
        })
        .catch(err => {});
}

function sendChatMessage() {
    if (!activeChatOrderId || isSendingChatMsg) return;

    const input = document.getElementById('chatInput');
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    isSendingChatMsg = true;
    const btn = document.getElementById('btnSendChat');
    if (btn) btn.disabled = true;

    fetch(`/api/chat/${activeChatOrderId}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    })
        .then(res => {
            if (!res.ok) throw new Error('Send failed');
            return res.json();
        })
        .then(data => {
            if (data && data.message) {
                input.value = '';
                const container = document.getElementById('chatMessagesContainer');
                const placeholder = document.getElementById('chatEmptyPlaceholder');
                if (placeholder) placeholder.remove();

                if (container && !document.querySelector(`[data-msg-id="${data.message.id}"]`)) {
                    const el = renderMessageRow(data.message);
                    container.appendChild(el);
                    if (data.message.id > lastChatMsgId) {
                        lastChatMsgId = data.message.id;
                    }
                    container.scrollTop = container.scrollHeight;
                }
            }
        })
        .catch(err => {
            alert('Không thể gửi tin nhắn. Vui lòng thử lại!');
        })
        .finally(() => {
            isSendingChatMsg = false;
            if (btn) btn.disabled = false;
            if (input) input.focus();
        });
}

function startChatPolling(orderId) {
    stopChatPolling();
    activeChatPollTimer = setInterval(() => {
        if (chatIsOpen && activeChatOrderId) {
            loadChatMessages(activeChatOrderId, true);
        }
    }, 2500);
}

function stopChatPolling() {
    if (activeChatPollTimer) {
        clearInterval(activeChatPollTimer);
        activeChatPollTimer = null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initRealtimeChat();

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

window.initRealtimeChat = initRealtimeChat;
window.showChatButtonForOrder = showChatButtonForOrder;
window.openChatWithOrder = openChatWithOrder;
window.toggleChatWidget = toggleChatWidget;
window.openChatWidget = openChatWidget;
window.closeChatWidget = closeChatWidget;
window.sendChatMessage = sendChatMessage;
