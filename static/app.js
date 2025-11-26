// State
let useWebSearch = false;
let uploadedFiles = [];

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const webSearchToggle = document.getElementById('webSearchToggle');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileList = document.getElementById('fileList');
const ingestBtn = document.getElementById('ingestBtn');
const statusMessage = document.getElementById('statusMessage');
const fileCount = document.getElementById('fileCount');
const serverStatus = document.getElementById('serverStatus');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSystemStatus();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Chat
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Web Search Toggle
    webSearchToggle.addEventListener('change', (e) => {
        useWebSearch = e.target.checked;
        showNotification(useWebSearch ? 'Web Search Enabled' : 'Web Search Disabled', 'info');
    });

    // File Upload
    fileInput.addEventListener('change', handleFileSelect);
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent-blue)';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border-glass)';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-glass)';
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    });

    // Ingestion
    ingestBtn.addEventListener('click', runIngestion);
}

// Chat Functions
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Clear input
    chatInput.value = '';
    sendBtn.disabled = true;

    // Add user message
    addMessage(message, 'user');

    // Add AI placeholder
    const aiMessageDiv = addMessage('Thinking...', 'ai', true);
    const messageText = aiMessageDiv.querySelector('.message-text');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, use_web: useWebSearch })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'chunk') {
                        fullResponse += data.content;
                        messageText.textContent = fullResponse;
                    } else if (data.type === 'sources') {
                        const sourcesDiv = document.createElement('div');
                        sourcesDiv.className = 'message-sources';
                        sourcesDiv.textContent = `📚 Sources: ${data.sources.join(', ')}`;
                        aiMessageDiv.querySelector('.message-content').appendChild(sourcesDiv);
                    } else if (data.type === 'error') {
                        messageText.textContent = `⚠️ Error: ${data.message}`;
                        messageText.style.color = 'var(--error)';
                    }
                }
            }

            // Auto-scroll
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } catch (error) {
        messageText.textContent = `⚠️ Connection error: ${error.message}`;
        messageText.style.color = 'var(--error)';
    } finally {
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function addMessage(text, type, isPlaceholder = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';

    const author = document.createElement('div');
    author.className = 'message-author';
    author.textContent = type === 'user' ? 'You' : 'Saturday';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;

    content.appendChild(author);
    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// File Upload Functions
function handleFileSelect() {
    const files = Array.from(fileInput.files);
    if (files.length === 0) return;

    fileList.innerHTML = '';
    uploadedFiles = [];

    files.forEach(file => {
        uploadFile(file);
    });
}

async function uploadFile(file) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <span class="file-item-name">${file.name}</span>
        <span class="file-item-status">Uploading...</span>
    `;
    fileList.appendChild(fileItem);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            fileItem.querySelector('.file-item-status').textContent = '✓ Uploaded';
            fileItem.querySelector('.file-item-status').style.color = 'var(--success)';
            uploadedFiles.push(file.name);
            showNotification(`Uploaded ${file.name}`, 'success');
        } else {
            throw new Error(result.message || 'Upload failed');
        }
    } catch (error) {
        fileItem.querySelector('.file-item-status').textContent = '✗ Failed';
        fileItem.querySelector('.file-item-status').style.color = 'var(--error)';
        showNotification(`Upload failed: ${error.message}`, 'error');
    }

    loadSystemStatus();
}

// Ingestion
async function runIngestion() {
    ingestBtn.disabled = true;
    statusMessage.textContent = 'Ingesting...';
    statusMessage.style.color = 'var(--accent-blue)';

    try {
        const response = await fetch('/api/ingest', { method: 'POST' });
        const result = await response.json();

        if (result.status === 'success') {
            statusMessage.textContent = result.message;
            statusMessage.style.color = 'var(--success)';
            showNotification('Ingestion complete', 'success');
        } else {
            throw new Error(result.message || 'Ingestion failed');
        }
    } catch (error) {
        statusMessage.textContent = `Error: ${error.message}`;
        statusMessage.style.color = 'var(--error)';
        showNotification(`Ingestion failed: ${error.message}`, 'error');
    } finally {
        ingestBtn.disabled = false;
        loadSystemStatus();
    }
}

// System Status
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.status === 'online') {
            serverStatus.textContent = '● Online';
            serverStatus.style.color = 'var(--success)';
            fileCount.textContent = data.files_count;
        } else {
            serverStatus.textContent = '● Offline';
            serverStatus.style.color = 'var(--error)';
        }
    } catch (error) {
        serverStatus.textContent = '● Error';
        serverStatus.style.color = 'var(--error)';
    }
}

// Notifications
function showNotification(message, type) {
    // Simple console log for now, can be enhanced with toast notifications
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Refresh status every 30 seconds
setInterval(loadSystemStatus, 30000);
