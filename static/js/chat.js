// MindSense Production Chat JS Driver

document.addEventListener('DOMContentLoaded', () => {
    scrollToBottom();
});

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function sendQuickMessage(text) {
    const input = document.getElementById('user-input');
    if (input) {
        input.value = text;
        handleChatSubmit(new Event('submit'));
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();

    const input = document.getElementById('user-input');
    const userMessage = input.value.trim();
    if (!userMessage) return;

    // Remove empty state placeholder if present
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.remove();

    input.value = '';
    input.disabled = true;

    appendUserMessage(userMessage);

    const typingIndicator = document.getElementById('typing-indicator');
    typingIndicator.classList.remove('hidden');
    typingIndicator.classList.add('flex');
    scrollToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: userMessage,
                mode: typeof currentMode !== 'undefined' ? currentMode : 'mental'
            })
        });

        const data = await response.json();

        typingIndicator.classList.add('hidden');
        typingIndicator.classList.remove('flex');
        input.disabled = false;
        input.focus();

        if (data.success) {
            appendBotMessage(data.response, data.emotion, data.intent, data.sentiment);
        } else {
            appendBotMessage("I encountered an issue generating a response. Please try again.", "Neutral", "Error", null);
        }
    } catch (err) {
        typingIndicator.classList.add('hidden');
        typingIndicator.classList.remove('flex');
        input.disabled = false;
        appendBotMessage("Network error. Please check your connection.", "Neutral", "Error", null);
    }
}

function appendUserMessage(msg) {
    const container = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'flex flex-col items-end space-y-1 animate-fade-slide';
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    wrapper.innerHTML = `
        <div class="bg-teal-600 text-white p-3.5 rounded-2xl rounded-tr-none max-w-lg text-sm shadow-md">
            ${escapeHtml(msg)}
        </div>
        <span class="text-[10px] text-slate-400 font-medium mr-1">${now}</span>
    `;
    container.appendChild(wrapper);
    scrollToBottom();
}

function appendBotMessage(botMsg, emotion, intent, sentiment) {
    const container = document.getElementById('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'flex items-start gap-3 space-y-1 animate-fade-slide';

    // Render newlines as <br> for multi-sentence responses
    const formattedMsg = escapeHtml(botMsg).replace(/\n/g, '<br>');

    const intentBadge = intent && intent !== 'General'
        ? `<span class="px-2 py-0.5 bg-sky-500/10 text-sky-600 dark:text-sky-400 rounded-md font-semibold text-[10px]">Intent: ${escapeHtml(intent)}</span>`
        : '';

    const sentimentBadge = sentiment
        ? `<span class="px-2 py-0.5 bg-slate-100 dark:bg-slate-700/60 rounded-md text-[10px] text-slate-500 dark:text-slate-400">+${sentiment.positive}% / -${sentiment.negative}%</span>`
        : '';

    wrapper.innerHTML = `
        <div class="w-8 h-8 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20 flex items-center justify-center shrink-0 mt-1">
            <i class="fa-solid fa-robot text-xs"></i>
        </div>
        <div class="space-y-1 max-w-xl">
            <div class="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 p-4 rounded-2xl rounded-tl-none text-sm shadow-sm leading-relaxed">
                ${formattedMsg}
            </div>
            <div class="flex items-center flex-wrap gap-2 text-[10px] text-slate-400 ml-1">
                <span class="px-2 py-0.5 bg-slate-200 dark:bg-slate-700/60 rounded-md font-semibold text-slate-600 dark:text-slate-300">
                    Mood: ${escapeHtml(emotion || 'Calm')}
                </span>
                ${intentBadge}
                ${sentimentBadge}
            </div>
        </div>
    `;

    container.appendChild(wrapper);
    scrollToBottom();
}

async function startNewChatSession() {
    if (confirm("Start a new chat session? Previous turns will be archived in History.")) {
        try {
            const response = await fetch('/api/chat/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: typeof currentMode !== 'undefined' ? currentMode : 'mental' })
            });
            const data = await response.json();
            if (data.success) {
                window.location.reload();
            }
        } catch (err) {
            alert("Error clearing session.");
        }
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text || '';
    return div.innerHTML;
}
