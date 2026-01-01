// static/career_videos_filter.js - Voice and Filtering Logic for Skill Selection

const searchInput = document.getElementById('skillSearch');
const skillsList = document.getElementById('skillsList');
const skillsItems = document.querySelectorAll('.skill-option');
const noSkillsFound = document.getElementById('noSkillsFound');
const voiceBtn = document.getElementById('voiceBtn');
const voiceFeedback = document.getElementById('voiceFeedback');
const voiceStatus = document.getElementById('voiceStatus');
const voiceResultDisplay = document.getElementById('voiceResult');


// --- 1. Client-Side Filtering Function ---
function filterSkills() {
    const filter = searchInput.value.toLowerCase().trim();
    let foundCount = 0;

    skillsItems.forEach(item => {
        const skillName = item.dataset.skillName;
        // Check if the skill name contains the filter text
        if (skillName && skillName.includes(filter)) { 
            item.style.display = 'block'; 
            foundCount++;
        } else {
            item.style.display = 'none';
        }
    });

    // Toggle the "No matching skills found" message
    if (foundCount === 0) {
        noSkillsFound.style.display = 'block';
    } else {
        noSkillsFound.style.display = 'none';
    }
}


// --- 2. Voice Recognition Functionality (Web Speech API) ---
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false; // Use false for direct text insertion
    recognition.lang = 'en-US'; 

    voiceBtn.addEventListener('click', () => {
        try {
            recognition.start();
            // --- START LISTENING VISUAL FEEDBACK ---
            voiceFeedback.style.display = 'flex'; 
            voiceFeedback.classList.add('is-listening'); 
        } catch (e) {
             console.error("Recognition error or already started.", e);
        }
    });

    recognition.onresult = (event) => {
        const finalTranscript = event.results[0][0].transcript;
        searchInput.value = finalTranscript.trim(); // Insert text into search bar
        filterSkills(); // Immediately filter the list based on voice input
    };

    recognition.onend = () => {
        // --- END LISTENING VISUAL FEEDBACK ---
        voiceFeedback.classList.remove('is-listening');
        setTimeout(() => {
            voiceFeedback.style.display = 'none';
        }, 500); 
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        voiceFeedback.classList.remove('is-listening');
        voiceFeedback.style.display = 'none';
        alert('Voice recognition error. Please check your microphone permissions.');
    };

} else {
    // Hide voice button if the browser doesn't support the API
    voiceBtn.style.display = 'none';
}


// --- 3. Initial Load and Event Listeners ---
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to make the filter run on key up
    searchInput.addEventListener('keyup', filterSkills);
    
    // Auto-hide flash messages (from the old inline script)
    const flashContainer = document.getElementById('flash-container');
    if (flashContainer) {
        setTimeout(function() {
            flashContainer.style.opacity = '0';
            setTimeout(function() {
                flashContainer.remove();
            }, 500);
        }, 2000);
    }
});