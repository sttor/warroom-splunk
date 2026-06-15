document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('config-form');
    const statusMsg = document.getElementById('status-message');
    const saveBtn = document.getElementById('save-btn');

    // Load existing config if available
    fetch('/api/config')
        .then(res => res.json())
        .then(data => {
            if (data.SLACK_BOT_TOKEN) document.getElementById('slack-bot-token').value = '********';
            if (data.SLACK_APP_TOKEN) document.getElementById('slack-app-token').value = '********';
            if (data.MCP_HOST) document.getElementById('mcp-host').value = data.MCP_HOST;
        })
        .catch(err => console.log('No existing config found.'));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        statusMsg.textContent = '';
        statusMsg.className = '';

        const payload = {
            slack_bot_token: document.getElementById('slack-bot-token').value,
            slack_app_token: document.getElementById('slack-app-token').value,
            splunk_mcp_url: document.getElementById('splunk_mcp_url').value,
            splunk_mcp_token: document.getElementById('splunk_mcp_token').value,
            vt_api_key: document.getElementById('vt_api_key').value,
            ollama_model: document.getElementById('ollama_model').value,
            llm_api_key: document.getElementById('llm-api-key').value
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                statusMsg.textContent = 'Configuration saved successfully!';
                statusMsg.className = 'success';
                document.getElementById('chat-section').style.display = 'block';
            } else {
                throw new Error('Failed to save configuration');
            }
        } catch (error) {
            statusMsg.textContent = error.message;
            statusMsg.className = 'error';
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Configuration';
        }
    });

    // Chat Logic
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const chatSendBtn = document.getElementById('send-btn');

    function appendMessage(text, isUser) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        // Simple markdown parsing for bold
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        msgDiv.innerHTML = `<p>${formattedText}</p>`;
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        appendMessage(text, true);
        chatInput.value = '';
        chatSendBtn.disabled = true;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            
            if (response.ok) {
                appendMessage(data.reply, false);
            } else {
                appendMessage("Error: " + data.detail, false);
            }
        } catch (error) {
            appendMessage("Error communicating with backend.", false);
        } finally {
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    });
});
