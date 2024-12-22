// Event listeners cho các nút
document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user_input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

document.getElementById('send-image-btn').addEventListener('click', () => {
    document.getElementById('image-input').click();
});

document.getElementById('toggle-voice-btn').addEventListener('click', toggleRecording);

document.getElementById('image-input').addEventListener('change', function (event) {
    sendImage(event.target.files[0]);
});

// Biến kiểm soát ghi âm
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Gửi tin nhắn văn bản
async function sendMessage() {
    const messageInput = document.getElementById('user_input');
    const message = messageInput.value.trim();

    if (message !== '') {
        const chatBox = document.getElementById('chat-box');

        // Hiển thị tin nhắn người dùng
        appendMessage('user', message, chatBox);

        // Gửi tin nhắn lên server
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ 'user_input': message })
        });

        const data = await response.json();

        // Hiển thị phản hồi của bot
        appendMessage('bot', data.response, chatBox);

        // Hiển thị phản hồi âm thanh của bot (nếu có)
        if (data.audio_url) appendAudio(data.audio_url, chatBox);

        // Xóa input
        messageInput.value = '';
    }
}

// Gửi hình ảnh
function sendImage(imageFile) {
    if (imageFile) {
        const chatBox = document.getElementById('chat-box');

        // Hiển thị ảnh người dùng
        const imageElement = document.createElement('img');
        imageElement.className = 'chat-message user';
        imageElement.src = URL.createObjectURL(imageFile);
        imageElement.style.maxWidth = '30%';
        imageElement.style.maxHeight = '30%';
        imageElement.style.borderRadius = '8px';
        imageElement.style.marginBottom = '10px';
        chatBox.appendChild(imageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Bắt đầu ghi âm
function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioChunks = [];
                sendVoiceMessage(audioBlob);
            };
            mediaRecorder.start();
            isRecording = true;
            updateRecordingButton(true);
        })
        .catch(error => console.error('Lỗi truy cập microphone:', error));
}

// Dừng ghi âm
function stopRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        isRecording = false;
        updateRecordingButton(false);
    }
}

// Chuyển đổi trạng thái ghi âm
function toggleRecording() {
    isRecording ? stopRecording() : startRecording();
}

// Gửi ghi âm giọng nói
async function sendVoiceMessage(audioBlob) {
    const formData = new FormData();
    formData.append('voice', audioBlob);

    const response = await fetch('/chat-voice', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    const chatBox = document.getElementById('chat-box');

    // Hiển thị giọng nói người dùng
    appendAudio(URL.createObjectURL(audioBlob), chatBox, true);

    // Hiển thị phản hồi văn bản của bot
    appendMessage('bot', data.response, chatBox);

    // Hiển thị giọng nói của bot (nếu có)
    if (data.audio_url) appendAudio(data.audio_url, chatBox);
}

// Tải lịch sử chat
async function loadChatHistory() {
    const response = await fetch('/chats');
    const data = await response.json();
    const chatBox = document.getElementById('chat-box');

    data.chat_history.forEach(entry => {
        const [userMessage, botMessage] = entry.split('|');
        appendMessage('user', userMessage, chatBox);
        appendMessage('bot', botMessage, chatBox);
    });
}

// Hàm tiện ích để hiển thị tin nhắn
function appendMessage(sender, message, chatBox) {
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${sender}`;
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Hàm tiện ích để hiển thị audio
function appendAudio(audioUrl, chatBox, autoplay = false) {
    const audioElement = document.createElement('audio');
    audioElement.src = audioUrl;
    audioElement.controls = true;
    audioElement.style.marginBottom = '10px';
    chatBox.appendChild(audioElement);
    chatBox.scrollTop = chatBox.scrollHeight;
    if (autoplay) audioElement.play();
}

// Cập nhật nút ghi âm
function updateRecordingButton(isRecording) {
    const button = document.getElementById('toggle-voice-btn');
    button.textContent = isRecording ? '🔴 Recording' : '🎤';
}
