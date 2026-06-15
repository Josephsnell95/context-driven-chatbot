const WORKER_URL = 'https://bear-necessities-worker.josephsnell.workers.dev';
let messages = [];


const chatToggle = document.getElementById('chat-toggle');
const closeBtn = document.getElementById('close-btn');
const chatPanel = document.getElementById('chat-panel');
const consentBtn = document.getElementById('consent-btn');
const sendBtn = document.getElementById('send-btn');
const consentNtc = document.getElementById('consent-notice');
const messageHst = document.getElementById('message-history');
const chatInput = document.getElementById('chat-input');
const loading = document.getElementById('loading');

if (sessionStorage.getItem('chatOpen') === 'true') {
    chatPanel.style.display = 'flex';
    chatToggle.style.display = 'none';
}

function togglePanel() {
    if (chatPanel.style.display === 'none') {
        chatPanel.style.display = 'flex';
        chatToggle.style.display = 'none';
        sessionStorage.setItem('chatOpen', 'true');
    } else {
        chatPanel.style.display = 'none';
        chatToggle.style.display = 'flex';
        sessionStorage.setItem('chatOpen', 'false');
    }
}

chatToggle.addEventListener('click', togglePanel);

function closeChat() {
    chatPanel.style.display = 'none';
    chatToggle.style.display = 'flex';
    sessionStorage.setItem('chatOpen', 'false');
}

closeBtn.addEventListener('click', closeChat);

function consentHandler() {
    consentNtc.style.display = 'none';
    chatInput.disabled = false;
    sessionStorage.setItem('consented', 'true');
}

consentBtn.addEventListener('click', consentHandler);

if (sessionStorage.getItem('consented') === 'true') {
    consentNtc.style.display = 'none';
    chatInput.disabled = false;
}

function renderMessage(role, content) {
    const wrapper = document.createElement('div');
    wrapper.className = role === 'user' ? 'msg-wrapper-user' : 'msg-wrapper-bear';

    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = role === 'user' ? 'You' : 'Bear';

    const div = document.createElement('div');
    div.textContent = content;
    div.className = role === 'user' ? 'msg-user' : 'msg-bear';

    wrapper.appendChild(label);
    wrapper.appendChild(div);
    messageHst.appendChild(wrapper);
    messageHst.scrollTop = messageHst.scrollHeight;
}

const saved = sessionStorage.getItem('chatMessages');
if (saved) {
    messages = JSON.parse(saved);
    messages.forEach(m => renderMessage(m.role, m.content));
    messageHst.scrollTop = messageHst.scrollHeight;
}

async function sendMessage() {
    if (chatInput.disabled) return;
    const content = chatInput.value.trim();
    if (!content) return;

    messages.push({ role: 'user', content: content });

    renderMessage('user', content);

    sessionStorage.setItem('chatMessages', JSON.stringify(messages));

    chatInput.value = '';

    chatInput.disabled = true;

    loading.style.display = 'block';

    try {
        const response = await fetch(WORKER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(messages)
        });
        const data = await response.json();

        messages.push({ role: 'assistant', content: data.reply });
        sessionStorage.setItem('chatMessages', JSON.stringify(messages));
        renderMessage('assistant', data.reply);
    } catch (err) {
        renderMessage('assistant', "Something went wrong - try again, or reach out to Joe directly.");
    } finally {
        loading.style.display = 'none';
        chatInput.disabled = false;
    }
};

sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});