let activeChatOrderId = null;
let chatSocket = null;
let chatIsOpen = false;
let restaurantNotifSocket = null;
let customerOrdersSocket = null;
const orderChatHistory = {};

function storeChatMessage(orderId, msgObj) {
    if (!orderId || !msgObj || !msgObj.message) return;
    const key = String(orderId);
    if (!orderChatHistory[key]) {
        orderChatHistory[key] = [];
    }
    const idx = orderChatHistory[key].findIndex(m =>
        (m.id && msgObj.id && String(m.id) === String(msgObj.id)) ||
        (m.message === msgObj.message && Boolean(m.is_restaurant) === Boolean(msgObj.is_restaurant))
    );
    if (idx >= 0) {
        if (msgObj.id && !orderChatHistory[key][idx].id) {
            orderChatHistory[key][idx].id = msgObj.id;
        }
    } else {
        orderChatHistory[key].push(msgObj);
    }
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
                storeChatMessage(data.order_id || orderId, data);
                appendChatMessage(data);

                const widget = document.getElementById('floatingChatWidget');
                const myUserRole = widget ? widget.getAttribute('data-current-user-role') : null;
                const isRestaurantPage = window.location.pathname.startsWith('/restaurant') || window.location.pathname.startsWith('/admin') || (myUserRole === 'RESTAURANT');
                const isFromOther = isRestaurantPage ? !data.is_restaurant : data.is_restaurant;
                if (isFromOther) {
                    playNotificationSound();
                }
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
    const card = document.getElementById('order-card-' + orderId);
    if (card) {
        const isEnded = card.querySelector('.badge-completed, .badge-cancelled');
        if (isEnded) {
            alert('Đơn hàng này đã hoàn thành hoặc đã hủy, không thể trò chuyện tiếp.');
            return;
        }
    }

    if (activeChatOrderId === orderId && chatIsOpen) {
        const input = document.getElementById('chatInput');
        if (input) input.focus();
        return;
    }

    showChatButtonForOrder(orderId, restaurantName, restaurantImage);
    clearOrderRowBadge(orderId);
    const container = document.getElementById('chatMessagesContainer');
    if (container) {
        container.innerHTML = '';
        const history = orderChatHistory[String(orderId)] || [];
        if (history.length > 0) {
            history.forEach(m => appendChatMessage(m));
        } else {
            container.innerHTML = `
                <div id="chatEmptyPlaceholder" style="text-align: center; color: #888; font-size: 13px; margin: auto; padding: 20px;">
                    <i class="fa-solid fa-comments" style="font-size: 32px; color: #d4c5a9; margin-bottom: 8px; display: block;"></i>
                    Bắt đầu trò chuyện trực tiếp về đơn hàng.
                </div>
            `;
        }
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

    if (msg.id && container.querySelector(`[data-msg-id="${msg.id}"]`)) return;

    const existingRows = container.querySelectorAll('.chat-msg-row');
    for (let i = 0; i < existingRows.length; i++) {
        const r = existingRows[i];
        if (r.getAttribute('data-msg-text') === msg.message &&
            r.getAttribute('data-msg-is-rest') === String(Boolean(msg.is_restaurant))) {
            if (msg.id) r.setAttribute('data-msg-id', msg.id);
            return;
        }
    }

    const widget = document.getElementById('floatingChatWidget');
    const myUserRole = widget ? widget.getAttribute('data-current-user-role') : null;
    const isRestaurantPage = window.location.pathname.startsWith('/restaurant') || window.location.pathname.startsWith('/admin') || (myUserRole === 'RESTAURANT');

    let isMe = false;
    if (isRestaurantPage) {
        isMe = Boolean(msg.is_restaurant);
    } else {
        isMe = !Boolean(msg.is_restaurant);
    }

    const row = document.createElement('div');
    row.className = 'chat-msg-row ' + (isMe ? 'me' : 'other');
    row.setAttribute('data-msg-id', msg.id || ('temp-' + Date.now()));
    row.setAttribute('data-msg-text', msg.message);
    row.setAttribute('data-msg-is-rest', String(Boolean(msg.is_restaurant)));

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

    const widget = document.getElementById('floatingChatWidget');
    const myUserId = widget ? widget.getAttribute('data-current-user-id') : null;
    const myUserName = widget ? widget.getAttribute('data-current-user-name') : null;
    const myUserRole = widget ? widget.getAttribute('data-current-user-role') : null;

    const isRestaurantPage = window.location.pathname.startsWith('/restaurant') || window.location.pathname.startsWith('/admin') || (myUserRole === 'RESTAURANT');
    const senderRole = isRestaurantPage ? 'RESTAURANT' : 'CUSTOMER';

    const sendPayload = {
        message: text,
        sender_id: myUserId ? parseInt(myUserId) : null,
        sender_name: myUserName || null,
        sender_role: senderRole
    };

    if (!chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
        connectChatWebSocket(activeChatOrderId);
        setTimeout(() => {
            if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify(sendPayload));
                input.value = '';
                input.focus();
            } else {
                alert('Không thể kết nối websocket với phòng chat. Vui lòng thử lại!');
            }
        }, 500);
        return;
    }

    chatSocket.send(JSON.stringify(sendPayload));
    input.value = '';
    input.focus();
}

let lastNotificationSoundTime = 0;
function playNotificationSound() {
    const now = Date.now();
    if (now - lastNotificationSoundTime < 600) return;
    lastNotificationSoundTime = now;
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
        osc.start(audioCtx.currentTime);
        osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {}
}

function showChatToast(data) {
    let container = document.getElementById('toastChatContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastChatContainer';
        container.className = 'toast-chat-container';
        document.body.appendChild(container);
    }

    const toastId = 'toast-order-' + data.order_id;
    let toast = document.getElementById(toastId);
    if (toast) toast.remove();

    toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast-chat-item';

    const widget = document.getElementById('floatingChatWidget');
    const myUserRole = widget ? widget.getAttribute('data-current-user-role') : null;
    const isRestaurantPage = window.location.pathname.startsWith('/restaurant') || window.location.pathname.startsWith('/admin') || (myUserRole === 'RESTAURANT');

    const displaySender = data.is_restaurant
        ? (data.restaurant_name || data.sender_name || 'Nhà hàng')
        : (data.customer_name || data.sender_name || 'Khách hàng');

    const chatTitle = isRestaurantPage
        ? ('Khách hàng (' + displaySender + ' - Đơn #' + data.order_id + ')')
        : (data.restaurant_name || 'Nhà hàng');
    const chatImg = isRestaurantPage ? '' : (data.restaurant_image || '');

    toast.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="color: #ffd269; font-size: 13.5px;">
                <i class="fa-solid fa-bell" style="margin-right: 5px;"></i> Tin nhắn Đơn #${data.order_id}
            </strong>
            <span style="font-size: 11px; opacity: 0.8;">${data.created_at || ''}</span>
        </div>
        <div style="font-size: 13px; line-height: 1.4; color: #fff; margin-top: 4px;">
            <strong>${displaySender}:</strong> "${data.message}"
        </div>
        <div style="display: flex; justify-content: flex-end; margin-top: 6px; gap: 8px;">
            <button type="button" class="btn-toast-reply" style="background: #ffd269; color: #1a4224; border: none; border-radius: 5px; padding: 5px 12px; font-size: 12px; font-weight: 700; cursor: pointer;">
                <i class="fa-solid fa-reply"></i> Xem &amp; Trả lời
            </button>
        </div>
    `;

    toast.onclick = function() {
        openChatWithOrder(data.order_id, chatTitle, chatImg);
        toast.remove();
    };

    const replyBtn = toast.querySelector('.btn-toast-reply');
    if (replyBtn) {
        replyBtn.onclick = function(e) {
            e.stopPropagation();
            openChatWithOrder(data.order_id, chatTitle, chatImg);
            toast.remove();
        };
    }

    container.appendChild(toast);

    setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 15000);
}

function updateOrderRowBadge(orderId) {
    const btns = document.querySelectorAll(`.btn-order-chat-${orderId}, button[onclick*="openChatWithOrder(${orderId},"]`);
    btns.forEach(btn => {
        let badge = btn.querySelector('.badge-unread-chat');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'badge-unread-chat';
            badge.style.cssText = 'background: #e74c3c; color: #fff; border-radius: 10px; padding: 2px 7px; font-size: 11px; margin-left: 6px; font-weight: 700; animation: badgePulse 1.5s infinite;';
            badge.innerText = '1';
            btn.appendChild(badge);
        } else {
            const count = parseInt(badge.innerText || '1') + 1;
            badge.innerText = count;
        }
    });
}

function clearOrderRowBadge(orderId) {
    const btns = document.querySelectorAll(`.btn-order-chat-${orderId}, button[onclick*="openChatWithOrder(${orderId},"]`);
    btns.forEach(btn => {
        const badge = btn.querySelector('.badge-unread-chat');
        if (badge) badge.remove();
    });
    const toast = document.getElementById('toast-order-' + orderId);
    if (toast) toast.remove();
}

function handleIncomingNotification(data) {
    if (!data || !data.order_id || !data.message) return;

    const msgObj = {
        id: data.id || null,
        order_id: data.order_id,
        sender_id: data.sender_id || (data.is_restaurant ? -2 : -1),
        sender_name: data.sender_name || (data.is_restaurant ? (data.restaurant_name || 'Nhà hàng') : (data.customer_name || 'Khách hàng')),
        is_restaurant: Boolean(data.is_restaurant),
        message: data.message,
        created_at: data.created_at || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    storeChatMessage(data.order_id, msgObj);
    playNotificationSound();
    showChatToast(data);

    if (chatIsOpen && activeChatOrderId === data.order_id) {
        appendChatMessage(msgObj);
        return;
    }

    updateOrderRowBadge(data.order_id);
}

function initRestaurantNotifications() {
    if (restaurantNotifSocket && restaurantNotifSocket.readyState === WebSocket.OPEN) return;
    const protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://';
    const socketUrl = protocol + location.host + '/ws/restaurant/notifications';
    try {
        restaurantNotifSocket = new WebSocket(socketUrl);
    } catch (e) {
        return;
    }
    restaurantNotifSocket.onopen = function() {
        const widget = document.getElementById('floatingChatWidget');
        const myUserId = widget ? widget.getAttribute('data-current-user-id') : null;
        if (myUserId && restaurantNotifSocket.readyState === WebSocket.OPEN) {
            restaurantNotifSocket.send(JSON.stringify({ user_id: parseInt(myUserId) }));
        }
    };
    restaurantNotifSocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data && data.type === 'new_chat_message') {
                handleIncomingNotification(data);
            }
        } catch (e) {}
    };
    restaurantNotifSocket.onclose = function() {
        restaurantNotifSocket = null;
        setTimeout(initRestaurantNotifications, 5000);
    };
    restaurantNotifSocket.onerror = function() {
        if (restaurantNotifSocket) {
            restaurantNotifSocket.close();
            restaurantNotifSocket = null;
        }
    };
}

function initCustomerOrdersWebSocket() {
    if (customerOrdersSocket && customerOrdersSocket.readyState === WebSocket.OPEN) return;
    const protocol = (location.protocol === 'https:') ? 'wss://' : 'ws://';
    const socketUrl = protocol + location.host + '/ws/customer/orders';
    try {
        customerOrdersSocket = new WebSocket(socketUrl);
    } catch(e) {
        return;
    }
    customerOrdersSocket.onopen = function() {
        const widget = document.getElementById('floatingChatWidget');
        const myUserId = widget ? widget.getAttribute('data-current-user-id') : null;
        if (myUserId && customerOrdersSocket.readyState === WebSocket.OPEN) {
            customerOrdersSocket.send(JSON.stringify({ user_id: parseInt(myUserId) }));
        }
    };
    customerOrdersSocket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data && data.type === 'order_status_updated') {
                handleLiveOrderStatusUpdate(data);
            } else if (data && data.type === 'new_chat_message') {
                handleIncomingNotification(data);
            }
        } catch(e) {}
    };
    customerOrdersSocket.onclose = function() {
        customerOrdersSocket = null;
        setTimeout(initCustomerOrdersWebSocket, 5000);
    };
    customerOrdersSocket.onerror = function() {
        if (customerOrdersSocket) {
            customerOrdersSocket.close();
            customerOrdersSocket = null;
        }
    };
}

let lastProcessedOrderStatus = {};

function handleLiveOrderStatusUpdate(data) {
    if (!data || !data.order_id) return;
    const orderId = data.order_id;
    const st = data.status;

    const dedupeKey = orderId + ':' + st;
    const now = Date.now();
    if (lastProcessedOrderStatus[dedupeKey] && (now - lastProcessedOrderStatus[dedupeKey] < 2000)) {
        return;
    }
    lastProcessedOrderStatus[dedupeKey] = now;

    const card = document.getElementById('order-card-' + orderId);
    if (!card) return;

    playNotificationSound();

    if (st === 'COMPLETED' || st === 'CANCELLED') {
        const chatBtn = card.querySelector('.btn-chat-restaurant');
        if (chatBtn) {
            chatBtn.remove();
        }
        const restChatBtn = document.querySelector(`.btn-order-chat-${orderId}`) || document.querySelector(`button[onclick*="openChatWithOrder(${orderId},"]`);
        if (restChatBtn) {
            restChatBtn.remove();
        }
        if (activeChatOrderId === orderId && chatIsOpen) {
            closeChatWidget();
        }
    }

    const badgeContainer = card.querySelector('.order-card-header > div:last-child');
    if (badgeContainer) {
        let badgeHtml = '';
        if (st === 'PENDING') {
            badgeHtml = '<span class="order-status-badge badge-pending"><i class="fa-solid fa-hourglass-half"></i> Chờ xác nhận</span>';
        } else if (st === 'CONFIRMED' || st === 'PREPARING') {
            badgeHtml = '<span class="order-status-badge badge-preparing"><i class="fa-solid fa-utensils"></i> Đang chuẩn bị</span>';
        } else if (st === 'DELIVERING') {
            badgeHtml = '<span class="order-status-badge badge-delivering"><i class="fa-solid fa-truck-fast"></i> Đang giao hàng</span>';
        } else if (st === 'COMPLETED') {
            badgeHtml = '<span class="order-status-badge badge-completed"><i class="fa-solid fa-circle-check"></i> Giao thành công</span>';
        } else if (st === 'CANCELLED') {
            badgeHtml = '<span class="order-status-badge badge-cancelled"><i class="fa-solid fa-ban"></i> Đã hủy đơn</span>';
        }
        if (badgeHtml) {
            badgeContainer.innerHTML = badgeHtml;
        }
    }

    if (st === 'CANCELLED') {
        const stepperBox = card.querySelector('.order-stepper-box');
        if (stepperBox) {
            stepperBox.style.display = 'none';
        }
        let cancelledBanner = card.querySelector('.order-cancelled-banner');
        if (!cancelledBanner) {
            cancelledBanner = document.createElement('div');
            cancelledBanner.className = 'order-cancelled-banner';
            cancelledBanner.innerHTML = `
                <i class="fa-solid fa-circle-xmark" style="font-size: 20px;"></i>
                <div>
                    <strong>Đơn hàng này đã bị hủy.</strong>
                    <div style="font-size: 12.5px; opacity: 0.9; margin-top: 2px;">
                        Cập nhật lúc: Vừa xong
                    </div>
                </div>
            `;
            const header = card.querySelector('.order-card-header');
            if (header && header.nextElementSibling) {
                card.insertBefore(cancelledBanner, header.nextElementSibling);
            }
        } else {
            cancelledBanner.style.display = 'flex';
        }
        const cancelBtn = card.querySelector('.btn-cancel-order');
        if (cancelBtn) {
            cancelBtn.remove();
        }
    } else {
        const cancelledBanner = card.querySelector('.order-cancelled-banner');
        if (cancelledBanner) {
            cancelledBanner.style.display = 'none';
        }
        const stepperBox = card.querySelector('.order-stepper-box');
        if (stepperBox) {
            stepperBox.style.display = 'block';

            const lineFill = stepperBox.querySelector('.stepper-line-fill');
            if (lineFill) {
                if (st === 'COMPLETED') lineFill.style.width = '100%';
                else if (st === 'DELIVERING') lineFill.style.width = '66%';
                else if (st === 'CONFIRMED' || st === 'PREPARING') lineFill.style.width = '33%';
                else lineFill.style.width = '0%';
            }

            const steps = stepperBox.querySelectorAll('.stepper-step');
            if (steps.length >= 4) {
                steps[0].className = 'stepper-step completed' + (st === 'PENDING' ? ' active' : '');

                const isStep2 = ['CONFIRMED', 'PREPARING', 'DELIVERING', 'COMPLETED'].includes(st);
                steps[1].className = 'stepper-step' + (isStep2 ? ' completed' : '') + (['CONFIRMED', 'PREPARING'].includes(st) ? ' active' : '');
                const sub2 = steps[1].querySelector('div:last-child');
                if (sub2) sub2.innerText = isStep2 ? 'Bếp nấu' : 'Chờ duyệt';

                const isStep3 = ['DELIVERING', 'COMPLETED'].includes(st);
                steps[2].className = 'stepper-step' + (isStep3 ? ' completed' : '') + (st === 'DELIVERING' ? ' active' : '');
                const sub3 = steps[2].querySelector('div:last-child');
                if (sub3) sub3.innerText = isStep3 ? 'Shipper nhận' : 'Lộ trình';

                const isStep4 = (st === 'COMPLETED');
                steps[3].className = 'stepper-step' + (isStep4 ? ' completed active' : '');
                const sub4 = steps[3].querySelector('div:last-child');
                if (sub4) sub4.innerText = isStep4 ? 'Hoàn tất' : 'Đích đến';
            }
        }
    }

    card.style.transition = 'box-shadow 0.4s ease, transform 0.4s ease';
    card.style.boxShadow = '0 0 0 4px #2ecc71, 0 12px 30px rgba(46, 204, 113, 0.25)';
    card.style.transform = 'scale(1.01)';
    setTimeout(() => {
        card.style.boxShadow = '';
        card.style.transform = '';
    }, 2500);

    let statusVi = 'Cập nhật';
    if (st === 'PENDING') statusVi = 'Chờ xác nhận';
    else if (st === 'CONFIRMED') statusVi = 'Đã xác nhận';
    else if (st === 'PREPARING') statusVi = 'Đang chuẩn bị';
    else if (st === 'DELIVERING') statusVi = 'Đang giao hàng';
    else if (st === 'COMPLETED') statusVi = 'Giao thành công';
    else if (st === 'CANCELLED') statusVi = 'Đã hủy';

    showStatusToast(orderId, statusVi);
}

function showStatusToast(orderId, statusVi) {
    let container = document.getElementById('toastChatContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastChatContainer';
        container.className = 'toast-chat-container';
        document.body.appendChild(container);
    }
    const toastId = 'toast-status-order-' + orderId;
    const oldToast = document.getElementById(toastId);
    if (oldToast) {
        oldToast.remove();
    }
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast-chat-item';
    toast.style.borderColor = '#2ecc71';
    toast.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="color: #ffd269; font-size: 13.5px;">
                <i class="fa-solid fa-bell"></i> Cập nhật Đơn #${orderId}
            </strong>
        </div>
        <div style="font-size: 13px; color: #fff; margin-top: 4px;">
            Trạng thái mới: <strong style="color: #2ecc71;">${statusVi}</strong>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 6000);
}

function initRealtimeListeners() {
    const input = document.getElementById('chatInput');
    if (input) {
        input.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    const widget = document.getElementById('floatingChatWidget');
    if (widget) {
        const myUserId = widget.getAttribute('data-current-user-id');
        const myUserRole = widget.getAttribute('data-current-user-role');
        if (myUserId) {
            if (myUserRole === 'RESTAURANT') {
                initRestaurantNotifications();
            } else {
                initCustomerOrdersWebSocket();
            }
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRealtimeListeners);
} else {
    initRealtimeListeners();
}

window.showChatButtonForOrder = showChatButtonForOrder;
window.openChatWithOrder = openChatWithOrder;
window.toggleChatWidget = toggleChatWidget;
window.openChatWidget = openChatWidget;
window.closeChatWidget = closeChatWidget;
window.sendChatMessage = sendChatMessage;
window.connectChatWebSocket = connectChatWebSocket;
window.disconnectChatWebSocket = disconnectChatWebSocket;
window.initRestaurantNotifications = initRestaurantNotifications;
window.handleIncomingNotification = handleIncomingNotification;
window.handleIncomingCustomerMessage = handleIncomingNotification;
window.initCustomerOrdersWebSocket = initCustomerOrdersWebSocket;
window.handleLiveOrderStatusUpdate = handleLiveOrderStatusUpdate;
