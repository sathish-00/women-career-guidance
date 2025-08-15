function startVoiceSearch() {
    console.log("Mic clicked. Listening...");
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US"; // Set language
    recognition.start();

    recognition.onstart = function() {
        console.log("Microphone is active.");
    };

    recognition.onresult = function(event) {
        const voiceInput = event.results[0][0].transcript;
        console.log("Captured text:", voiceInput);
        document.getElementById("searchBar").value = voiceInput;
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
    };
}
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
