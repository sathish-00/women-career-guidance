// static/career_interests.js - COMPLETE CODE FOR SEARCH AND VOICE FEEDBACK

const searchInput = document.getElementById('skillSearch');
const skillsListWrapper = document.getElementById('skillsListWrapper');
const skillsItems = document.querySelectorAll('.skill-checkbox-item');
const noSkillsFound = document.getElementById('noSkillsFound');
const voiceBtn = document.getElementById('voiceBtn');
const voiceFeedback = document.getElementById('voiceFeedback');
const voiceStatus = document.getElementById('voiceStatus');
const voiceResultDisplay = document.getElementById('voiceResult');


// --- 1. Real-time Filtering Function ---
function filterSkills() {
    const filter = searchInput.value.toLowerCase();
    let foundCount = 0;

    skillsItems.forEach(item => {
        const skillName = item.dataset.skillName;
        if (skillName.includes(filter)) { 
            item.style.display = 'flex';
            foundCount++;
        } else {
            item.style.display = 'none';
        }
    });

    if (foundCount === 0) {
        noSkillsFound.style.display = 'block';
    } else {
        noSkillsFound.style.display = 'none';
    }
}


// --- 2. Event Listeners for Checkbox Toggling ---
skillsItems.forEach(item => {
    item.addEventListener('click', function(event) {
        const checkbox = this.querySelector('input[type="checkbox"]');
        if (checkbox && event.target !== checkbox && event.target !== checkbox.nextElementSibling) {
            checkbox.checked = !checkbox.checked;
        }
    });
});


// --- 3. Voice Recognition Functionality (Web Speech API) ---
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true; 
    recognition.lang = 'en-US'; 

    voiceBtn.addEventListener('click', () => {
        try {
            recognition.start();
            // --- START LISTENING VISUAL FEEDBACK (Show the pulsing indicator) ---
            voiceFeedback.style.display = 'flex'; 
            voiceFeedback.classList.add('is-listening'); 
            voiceStatus.textContent = 'Listening...';
            voiceResultDisplay.textContent = '';
            voiceBtn.innerHTML = '<i class="fas fa-microphone fa-beat" style="color: red;"></i>'; 
        } catch (e) {
             console.error("Recognition already started or permission denied.", e);
             voiceStatus.textContent = 'Speech already started or permission error.';
        }
    });

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            } else {
                interimTranscript += event.results[i][0].transcript;
            }
        }
        
        // Update the content (even though it's hidden, it processes the text)
        voiceResultDisplay.textContent = finalTranscript || interimTranscript + ' . . .';
    };

    recognition.onend = () => {
        // --- END LISTENING VISUAL FEEDBACK (Removes pulsing and hides indicator) ---
        const finalResult = voiceResultDisplay.textContent;
        searchInput.value = finalResult; 
        filterSkills();

        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>'; 
        
        // Hide the box visually by removing the animation class
        voiceFeedback.classList.remove('is-listening');
        
        // Fully hide the box from layout after the transition
        setTimeout(() => {
            voiceFeedback.style.display = 'none';
        }, 500); 
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        voiceFeedback.classList.remove('is-listening');
        voiceFeedback.style.display = 'none';
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    };

} else {
    // Hide voice button if the browser doesn't support the API
    voiceBtn.style.display = 'none';
    console.warn("Web Speech API not supported in this browser.");
}

// Run initial filtering 
filterSkills();