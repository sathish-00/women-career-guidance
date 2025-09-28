// This file handles the voice search functionality

document.addEventListener('DOMContentLoaded', function() {
    const micIcon = document.getElementById('micIcon');
    const searchInput = document.getElementById('searchBar');
    const speechBox = document.getElementById('speechBox');
    
    // Check for browser support of the Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Web Speech API not supported in this browser.');
        micIcon.style.display = 'none'; // Hide microphone icon if not supported
        return;
    }

    function startVoiceSearch() {
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
            micIcon.classList.add('blinking');
            speechBox.classList.remove('hidden');
            speechBox.textContent = 'Listening...';
        };

        recognition.onresult = function(event) {
            const speechResult = event.results[0][0].transcript;
            searchInput.value = speechResult;
            speechBox.textContent = 'Heard: ' + speechResult;
            searchVideos(); // Calls the search function defined in the HTML script block
        };

        recognition.onend = function() {
            micIcon.classList.remove('blinking');
            speechBox.classList.add('hidden');
        };

        recognition.onerror = function(event) {
            micIcon.classList.remove('blinking');
            speechBox.classList.remove('hidden');
            speechBox.textContent = 'Error: ' + event.error;
            console.error('Speech recognition error:', event.error);
        };

        try {
            recognition.start();
        } catch (e) {
            console.error("Recognition already started or error:", e);
        }
    }

    // Attach the voice search function globally (needed because it's called from onclick in HTML)
    window.startVoiceSearch = startVoiceSearch;
});

// Add blinking animation to CSS if not already present
// NOTE: You should have this in your career_videos.css
/*
@keyframes blinking {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
.blinking {
    animation: blinking 1s infinite;
}
*/