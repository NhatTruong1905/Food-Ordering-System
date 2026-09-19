let aiChatIsOpen = false;
let aiAbortController = null;
let isAiStreaming = false;

async function checkAiServerStatus() {
    const dot = document.getElementById('aiStatusDot');
    const text = document.getElementById('aiStatusText');
    if (!dot) return;

    try {
        const resp = await fetch('/api/ai-chat/status', { cache: 'no-store' });
        const data = await resp.json();
        if (data.status === 'online') {
            dot.className = 'ai-status-indicator online';
            dot.title = 'AI RAG Server: Trực tuyến';
            if (text) text.innerText = 'Trực tuyến • Sẵn sàng tư vấn';
        } else {
            dot.className = 'ai-status-indicator offline';
            dot.title = 'AI RAG Server: Ngoại tuyến';
            if (text) text.innerText = 'Chưa bật server RAG (cổng 8000)';
        }
    } catch (err) {
        dot.className = 'ai-status-indicator offline';
        if (text) text.innerText = 'Ngoại tuyến';
    }
}

function toggleAiChat() {
    if (aiChatIsOpen) {
        closeAiChat();
    } else {
        openAiChat();
    }
}

function openAiChat() {
    const widget = document.getElementById('floatingAiChatWidget');
    const btn = document.getElementById('floatingAiBtn');
    if (!widget) return;

    widget.classList.add('active');
    widget.setAttribute('aria-hidden', 'false');
    if (btn) btn.classList.add('active');
    aiChatIsOpen = true;

    const input = document.getElementById('aiChatInput');
    if (input) {
        setTimeout(() => input.focus(), 200);
    }

    scrollAiChatToBottom();
    checkAiServerStatus();
}

function closeAiChat() {
    const widget = document.getElementById('floatingAiChatWidget');
    const btn = document.getElementById('floatingAiBtn');
    if (!widget) return;

    widget.classList.remove('active');
    widget.setAttribute('aria-hidden', 'true');
    if (btn) btn.classList.remove('active');
    aiChatIsOpen = false;
}

function clearAiChat() {
    if (isAiStreaming) {
        stopAiStream();
    }

    const list = document.getElementById('aiMessagesList');
    if (list) {
        list.innerHTML = '';
    }

    const welcome = document.getElementById('aiWelcomeBox');
    if (welcome) {
        welcome.style.display = 'block';
    }

    const input = document.getElementById('aiChatInput');
    if (input) input.focus();
}

function askAiSuggestion(question) {
    const input = document.getElementById('aiChatInput');
    if (!input) return;
    input.value = question;
    handleAiSubmit(new Event('submit'));
}

async function handleAiSubmit(event) {
    if (event) event.preventDefault();
    if (isAiStreaming) return;

    const input = document.getElementById('aiChatInput');
    if (!input) return;

    const question = input.value.trim();
    if (!question) return;

    const welcome = document.getElementById('aiWelcomeBox');
    if (welcome) {
        welcome.style.display = 'none';
    }

    appendUserMessage(question);
    input.value = '';

    const aiMessageEl = createAiMessageElement();
    const contentEl = aiMessageEl.querySelector('.ai-msg-content');

    setAiTyping(true);
    setStreamingState(true);

    aiAbortController = new AbortController();

    try {
        let response = null;
        try {
            response = await fetch('/api/ai-chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: question, top_k: 3 }),
                signal: aiAbortController.signal
            });
        } catch (fetchErr) {
            try {
                response = await fetch('http://127.0.0.1:8000/query/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: question, top_k: 3 }),
                    signal: aiAbortController.signal
                });
            } catch (directErr) {
                throw fetchErr;
            }
        }

        setAiTyping(false);

        if (!response.ok) {
            const errData = await response.text();
            contentEl.innerHTML = `<span class="ai-error-text">⚠️ Không thể tải dữ liệu: ${escapeHtml(errData || response.statusText)}</span>`;
            return;
        }

        if (!response.body) {
            contentEl.innerHTML = `<span class="ai-error-text">⚠️ Trình duyệt không hỗ trợ đọc Stream phản hồi.</span>`;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let displayedText = '';
        let targetText = '';
        let streamDone = false;

        const typewriterPromise = new Promise((resolve) => {
            function typeNext() {
                if (aiAbortController === null) {
                    resolve();
                    return;
                }
                if (displayedText.length < targetText.length) {
                    const diff = targetText.length - displayedText.length;
                    const step = Math.min(Math.max(1, Math.floor(diff / 6)), 5);
                    displayedText = targetText.slice(0, displayedText.length + step);
                    contentEl.innerHTML = formatAiResponse(displayedText) + '<span class="ai-typing-cursor">▌</span>';
                    scrollAiChatToBottom();
                    setTimeout(typeNext, 16);
                } else if (!streamDone) {
                    setTimeout(typeNext, 20);
                } else {
                    contentEl.innerHTML = formatAiResponse(displayedText);
                    scrollAiChatToBottom();
                    resolve();
                }
            }
            typeNext();
        });

        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                streamDone = true;
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            targetText += chunk;
        }

        await typewriterPromise;

    } catch (err) {
        setAiTyping(false);
        if (err.name === 'AbortError') {
            contentEl.innerHTML += '<div class="ai-stopped-tag"><i class="fa-solid fa-circle-stop"></i> Đã dừng phản hồi.</div>';
        } else {
            contentEl.innerHTML = `
                <div class="ai-error-box">
                    <p><strong>⚠️ Không thể kết nối tới AI Server:</strong></p>
                    <p>Vui lòng đảm bảo server RAG đã được bật tại cổng 8000 bằng lệnh:</p>
                    <code>python RAG-Food-Ordering-System/api/main.py</code>
                </div>
            `;
        }
    } finally {
        setStreamingState(false);
        aiAbortController = null;
        scrollAiChatToBottom();
    }
}

function stopAiStream() {
    if (aiAbortController) {
        aiAbortController.abort();
    }
    setStreamingState(false);
}

function setStreamingState(streaming) {
    isAiStreaming = streaming;
    const btnSend = document.getElementById('btnSendAiChat');
    const btnStop = document.getElementById('btnStopAiStream');
    const input = document.getElementById('aiChatInput');

    if (streaming) {
        if (btnSend) btnSend.style.display = 'none';
        if (btnStop) btnStop.style.display = 'flex';
        if (input) input.disabled = true;
    } else {
        if (btnSend) btnSend.style.display = 'flex';
        if (btnStop) btnStop.style.display = 'none';
        if (input) {
            input.disabled = false;
            input.focus();
        }
    }
}

function setAiTyping(show) {
    const indicator = document.getElementById('aiTypingIndicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
        if (show) scrollAiChatToBottom();
    }
}

function appendUserMessage(text) {
    const list = document.getElementById('aiMessagesList');
    if (!list) return;

    const row = document.createElement('div');
    row.className = 'ai-msg-row user';

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    row.innerHTML = `
        <div class="ai-msg-bubble user">
            <div class="ai-msg-text">${escapeHtml(text)}</div>
            <div class="ai-msg-time">${timeStr}</div>
        </div>
    `;

    list.appendChild(row);
    scrollAiChatToBottom();
}

function createAiMessageElement() {
    const list = document.getElementById('aiMessagesList');
    const row = document.createElement('div');
    row.className = 'ai-msg-row bot';

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    row.innerHTML = `
        <div class="ai-msg-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="ai-msg-bubble bot">
            <div class="ai-msg-header">
                <span class="ai-bot-name">AI Concierge</span>
                <span class="ai-msg-time">${timeStr}</span>
            </div>
            <div class="ai-msg-content"></div>
        </div>
    `;

    list.appendChild(row);
    scrollAiChatToBottom();
    return row;
}

function formatAiResponse(rawText) {
    if (!rawText) return '';

    let text = escapeHtml(rawText);

    text = text.replace(/(\d{1,3}(?:\.\d{3})+)\s*(VNĐ|VND|đ|Đ)/gi, '<span class="ai-price-badge">$1 $2</span>');
    text = text.replace(/^-\s+(.+)$/gm, '<li class="ai-bullet-item">$1</li>');
    text = text.replace(/(<li class="ai-bullet-item">.*?<\/li>)+/gs, '<ul class="ai-bullet-list">$&</ul>');
    text = text.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="ai-numbered-item"><span class="ai-item-num">$1.</span> <span class="ai-item-text">$2</span></div>');
    text = text.replace(/\n\n/g, '<div class="ai-p-spacer"></div>');
    text = text.replace(/\n/g, '<br>');

    return text;
}

function escapeHtml(str) {
    if (!str) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return str.replace(/[&<>"']/g, m => map[m]);
}

function scrollAiChatToBottom() {
    const body = document.getElementById('aiChatBody');
    if (body) {
        body.scrollTop = body.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAiServerStatus();

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && aiChatIsOpen) {
            closeAiChat();
        }
    });

    document.addEventListener('click', (e) => {
        const widget = document.getElementById('floatingAiChatWidget');
        const btn = document.getElementById('floatingAiBtn');
        if (aiChatIsOpen && widget && btn) {
            if (!widget.contains(e.target) && !btn.contains(e.target)) {
            }
        }
    });
});

window.toggleAiChat = toggleAiChat;
window.openAiChat = openAiChat;
window.closeAiChat = closeAiChat;
window.clearAiChat = clearAiChat;
window.askAiSuggestion = askAiSuggestion;
window.handleAiSubmit = handleAiSubmit;
window.stopAiStream = stopAiStream;
