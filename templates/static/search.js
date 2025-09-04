function startVoiceSearch() {
    console.log("Mic clicked. Listening...");
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onstart = function() {
        console.log("Microphone is active.");
    };

    recognition.onresult = function(event) {
        const voiceInput = event.results[0][0].transcript;
        console.log("Captured text:", voiceInput);
        document.getElementById("searchBar").value = voiceInput;
        searchVideos(); // Call searchVideos after voice input is added to the search bar
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
    };
}
function searchVideos() {
    const searchBar = document.getElementById("searchBar");
    const videoItems = document.querySelectorAll('.video-item');
    const query = searchBar.value.toLowerCase();

    videoItems.forEach(item => {
        const title = item.querySelector('p').textContent.toLowerCase();
        if (title.includes(query)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}
document.addEventListener('DOMContentLoaded', function() {
    const searchBar = document.getElementById("searchBar");
    searchBar.addEventListener('keyup', searchVideos);
});