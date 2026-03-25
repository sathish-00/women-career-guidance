// static/sw.js
self.addEventListener('push', function(event) {
    const data = event.data ? event.data.json() : { title: 'New Job!', body: 'Check out the new opening!' };
    
    const options = {
        body: data.body,
        icon: '/static/icons/job-icon.png', // Path to your briefcase or logo icon
        badge: '/static/icons/badge.png',   // Small icon for the status bar
        vibrate: [100, 50, 100],            // Vibrate pattern for mobile
        data: {
            url: data.url || '/'            // The link to open when clicked
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// When the user clicks the notification, take them to the job page
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
self.registration.showNotification("New Job Alert!", {
    body: "New vacancy: Data Entry. Apply shortly!",
    icon: "/static/icon.png",
    requireInteraction: true // <--- This keeps it on screen longer!
});