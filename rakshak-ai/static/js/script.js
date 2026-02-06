document.addEventListener('DOMContentLoaded', function() {
    loadLogs();
    loadStats();
    initMap();

    // Poll for accident alerts
    setInterval(checkForAccident, 1000);
    // Auto refresh logs and stats
    setInterval(() => {
        loadLogs();
        loadStats();
    }, 5000);
});

function changeSource(source) {
    const img = document.querySelector('.video-section img');
    img.src = `/video_feed?source=${source}`;
}

function uploadVideo() {
    const input = document.getElementById('videoFile');
    const file = input.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('video', file);
        fetch('/upload_video', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.filename) {
                changeSource(data.filename);
            } else {
                alert('Upload failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
        });
    } else {
        alert('Please select a video file first.');
    }
}

function checkForAccident() {
    fetch('/accident_status')
        .then(response => response.json())
        .then(data => {
            if (data.accident) {
                showAlert(data.severity);
            }
        });
}

function showAlert(severity) {
    const alertPopup = document.getElementById('alert-popup');
    alertPopup.innerHTML = `<p>ACCIDENT DETECTED! Severity: ${severity}</p>`;
    alertPopup.classList.remove('hidden');
    alertPopup.classList.add('blinking');
    setTimeout(() => {
        alertPopup.classList.add('hidden');
        alertPopup.classList.remove('blinking');
    }, 5000);
}

function loadLogs() {
    fetch('/logs')
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#logs-table tbody');
            tbody.innerHTML = '';
            data.forEach(log => {
                const row = `<tr>
                    <td>${log[0]}</td>
                    <td>${log[1]}</td>
                    <td>${log[2]}</td>
                    <td>${log[3]}</td>
                    <td>${log[4]}</td>
                    <td>${log[5]}</td>
                </tr>`;
                tbody.innerHTML += row;
            });
            // Update map markers
            updateMapMarkers(data);
        });
}

function loadStats() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            const counter = document.getElementById('live-counter');
            counter.textContent = `Accidents Today: ${data.accident_count}`;
            const ctx = document.getElementById('stats-chart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Accidents'],
                    datasets: [{
                        label: 'Count',
                        data: [data.accident_count],
                        backgroundColor: '#00bcd4'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
}

let map;
let markers = [];

function initMap() {
    map = L.map('map').setView([28.6139, 77.2090], 10); // Delhi center
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

function updateMapMarkers(logs) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    logs.forEach(log => {
        if (log[2] && log[3]) { // lat and lng
            const marker = L.marker([log[2], log[3]]).addTo(map)
                .bindPopup(`<b>Time:</b> ${log[1]}<br><b>Severity:</b> ${log[4]}<br><b>Description:</b> ${log[5]}`);
            markers.push(marker);
        }
    });
}
