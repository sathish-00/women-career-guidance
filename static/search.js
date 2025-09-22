function startVoiceSearch() {
    console.log("Mic clicked. Listening...");
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
<<<<<<< HEAD
    recognition.lang = "en-US";
=======
    recognition.lang = "en-US"; // Set language
>>>>>>> 005e43991de0473e54b734e957cb8331c9975876
    recognition.start();

    recognition.onstart = function() {
        console.log("Microphone is active.");
    };

    recognition.onresult = function(event) {
        const voiceInput = event.results[0][0].transcript;
        console.log("Captured text:", voiceInput);
        document.getElementById("searchBar").value = voiceInput;
<<<<<<< HEAD
        searchVideos(); // Call searchVideos after voice input is added to the search bar
=======
>>>>>>> 005e43991de0473e54b734e957cb8331c9975876
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
    };
}
<<<<<<< HEAD
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
=======
    function searchVideos() {
    let query = document.getElementById("searchBar").value.trim();

    if (query === "") {
        alert("Please enter a search term!");
        return;
    }

    console.log("Searching for:", query); // ✅ Debugging check
    // Perform the actual search (modify as needed)
    window.location.href = `/search?query=${encodeURIComponent(query)}`;
}
>>>>>>> 005e43991de0473e54b734e957cb8331c9975876
