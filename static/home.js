// 1. Setup the Ear (Recognition)
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-IN';

// 2. The Dynamic Flow Trigger
function toggleAssistant() {
    const bubble = document.getElementById('assistant-chat-bubble');
    bubble.classList.toggle('hidden');

    if (!bubble.classList.contains('hidden')) {
        // Step A: Natural Greeting
        speakAndThenListen("Welcome back! I am ready to help. What are you looking for today?");
    }
}

// 3. The Continuous Loop: Speak -> Listen -> Act
function speakAndThenListen(text) {
    const status = document.getElementById('assistant-text');
    status.innerText = text;

    const msg = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    msg.voice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira')) || voices[0];

    // THE DYNAMIC TRIGGER: When she finishes talking, she starts listening automatically
    msg.onend = () => {
        status.innerHTML = "<span style='color:#e84393;'>● I am listening...</span>";
        recognition.start();
    };

    window.speechSynthesis.speak(msg);
}

// 4. Processing the Voice Dynamic Input
recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript.toLowerCase();
    const output = document.getElementById('user-speech-output');
    output.innerText = "Current Request: " + transcript;

    // Dynamic Navigation & Info Logic
    if (transcript.includes("show me") || transcript.includes("job") || transcript.includes("career")) {
        speakAndThenListen("I am pulling up the latest career guidance for you right now.");
        setTimeout(() => window.location.href = "/career_options", 2500);
    } 
    else if (transcript.includes("help") || transcript.includes("stuck")) {
        speakAndThenListen("Don't worry. I can guide you to the contact page to talk to a human assistant.");
        setTimeout(() => window.location.href = "/contact", 2500);
    }
    else {
        // If it doesn't understand, it asks again DYNAMICALLY
        speakAndThenListen("I heard you say " + transcript + ". Could you please repeat that using keywords like jobs or help?");
    }
};

// Inside your recognition.onresult function:
recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript.toLowerCase();
    
    // 1. Show the thinking dots
    document.getElementById('assistant-thinking').classList.remove('hidden');
    document.getElementById('user-speech-output').innerText = "Processing: " + transcript;

    // 2. Small delay to simulate "Thinking" (Good for UX)
    setTimeout(() => {
        // Hide dots and process the command
        document.getElementById('assistant-thinking').classList.add('hidden');
        processDynamicResponse(transcript);
    }, 1500);
};

function processDynamicResponse(command) {
    // Your logic to speak and redirect
    if (command.includes("job")) {
        speakAndThenListen("I am finding jobs for you...");
    } else {
        speakAndThenListen("I heard you, but can you say 'jobs' or 'help'?");
    }
}

function changeLanguage(langCode) {
    const selectEl = document.querySelector('.goog-te-combo');
    if (selectEl) {
        selectEl.value = langCode;
        selectEl.dispatchEvent(new Event('change'));
        
        // Sync the Voice Assistant NLP language too!
        if (langCode === 'te') {
            recognition.lang = 'te-IN';
        } else {
            recognition.lang = 'en-IN';
        }
    }
}