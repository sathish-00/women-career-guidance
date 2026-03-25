// ==========================================
// 1. SELECTORS & INITIALIZATION
// ==========================================
const searchInput = document.getElementById('skillSearch') || document.getElementById('career-search');
const skillsItems = document.querySelectorAll('.skill-checkbox-item') || document.querySelectorAll('.interest-card-wrapper');
const noSkillsFound = document.getElementById('noSkillsFound');
const voiceBtn = document.getElementById('voiceBtn') || document.querySelector('.mic-btn-youtube');
const voiceFeedback = document.getElementById('voiceFeedback') || document.getElementById('voice-overlay');
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');

// --- Real-time Filtering Function ---
function filterSkills() {
    if (!searchInput || !skillsItems.length) return;
    const filter = searchInput.value.toLowerCase();
    let foundCount = 0;

    skillsItems.forEach(item => {
        const text = item.innerText.toLowerCase();
        if (text.includes(filter)) { 
            item.style.display = 'flex';
            foundCount++;
        } else {
            item.style.display = 'none';
        }
    });

    if (noSkillsFound) {
        noSkillsFound.style.display = foundCount === 0 ? 'block' : 'none';
    }
}

if (searchInput) {
    searchInput.addEventListener('input', filterSkills);
}

// ==========================================
// 2. AI CHATBOT LOGIC (The "Brain")
// ==========================================
async function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    // Display user message
    appendMessage("user", message);
    userInput.value = '';

    try {
        const response = await fetch('/ai_bot_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        // Convert AI response into Bold/Italics for better UI
        const formattedReply = data.reply
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') 
            .replace(/\n/g, '<br>');

        appendMessage("ai", formattedReply);
    } catch (error) {
        console.error('Error:', error);
        appendMessage("ai", "I'm having trouble connecting. Check your internet!");
    }
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;
    msgDiv.innerHTML = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom
}

function toggleChat() {
    const container = document.getElementById('chat-container');
    container.classList.toggle('minimized');
}

// ==========================================
// 3. VOICE RECOGNITION (Web Speech API)
// ==========================================
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';

    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            recognition.start();
            if (voiceFeedback) voiceFeedback.style.display = 'flex';
        });
    }

    recognition.onresult = (event) => {
        const result = event.results[0][0].transcript;
        if (searchInput) {
            searchInput.value = result;
            filterSkills();
        }
    };

    recognition.onend = () => {
        if (voiceFeedback) {
            setTimeout(() => { voiceFeedback.style.display = 'none'; }, 1000);
        }
    };
}
async function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    appendMessage("user", message);
    userInput.value = '';

    // --- START THINKING ANIMATION ---
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const response = await fetch('/ai_bot_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        // --- REMOVE THINKING ANIMATION ---
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();

        const formattedReply = data.reply
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') 
            .replace(/\n/g, '<br>');

        appendMessage("ai", formattedReply);
    } catch (error) {
        document.getElementById('typing-indicator')?.remove();
        appendMessage("ai", "System busy. Please try again!");
    }
}
// --- DRAGGABLE CHATBOT LOGIC ---
const chatContainer = document.getElementById('chat-container');
const chatHeader = document.querySelector('.chat-header');

let isDragging = false;
let offsetX, offsetY;

chatHeader.addEventListener('mousedown', (e) => {
    isDragging = true;
    // Calculate where the mouse is relative to the top-left of the chat box
    offsetX = e.clientX - chatContainer.getBoundingClientRect().left;
    offsetY = e.clientY - chatContainer.getBoundingClientRect().top;
    chatContainer.style.transition = 'none'; // Disable smooth transition while dragging
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    // Move the container to the mouse position
    let x = e.clientX - offsetX;
    let y = e.clientY - offsetY;

    // Boundary checks (Keep it inside the window)
    x = Math.max(0, Math.min(x, window.innerWidth - chatContainer.offsetWidth));
    y = Math.max(0, Math.min(y, window.innerHeight - chatContainer.offsetHeight));

    chatContainer.style.left = `${x}px`;
    chatContainer.style.top = `${y}px`;
    chatContainer.style.bottom = 'auto'; // Disable the fixed bottom/right
    chatContainer.style.right = 'auto';
});

document.addEventListener('mouseup', () => {
    isDragging = false;
    chatContainer.style.transition = 'all 0.3s ease-in-out'; // Re-enable transition
});
// Register the Service Worker
if ('serviceWorker' in navigator && 'PushManager' in window) {
    navigator.serviceWorker.register('/static/sw.js')
    .then(function(swReg) {
        console.log('Service Worker is registered', swReg);
        checkSubscription(swReg);
    })
    .catch(function(error) {
        console.error('Service Worker Error', error);
    });
}

function checkSubscription(swReg) {
    // Check if the user is already subscribed
    swReg.pushManager.getSubscription()
    .then(function(subscription) {
        if (subscription === null) {
            console.log('User is NOT subscribed. We need to ask.');
            // You can trigger this when the user clicks your "Opt-in" checkbox
        } else {
            console.log('User IS subscribed:', JSON.stringify(subscription));
        }
    });
}

// Function to call when the user clicks the "Yes, notify me" checkbox
function subscribeUser() {
    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            // This is where you'd actually connect to the push service
            console.log("Permission granted! Ready to receive jobs.");
        }
    });
}