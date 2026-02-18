function loadWeather() {
    navigator.geolocation.getCurrentPosition(function(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        
        fetch(`/api/weather/?lat=${lat}&lon=${lon}`)
            .then(r => r.json())
            .then(data => {
                document.getElementById("weather-info").innerHTML = `
                    <strong>${data.city}</strong><br>
                    <strong>${data.temperature}°F</strong><br>
                    ${data.conditions}<br>
                    Humidity: ${data.humidity}%<br>
                    Wind: ${data.wind_speed} mph
                `;
            })
            .catch(err => {
                document.getElementById("weather-info").innerHTML = "Could not fetch weather";
            });
    }, function() {
        const city = prompt("Enter city (e.g., Detroit,US):");
        if (city) {
            fetch(`/api/weather/?city=${city}`)
                .then(r => r.json())
                .then(data => {
                    document.getElementById("weather-info").innerHTML = `
                        <strong>${data.city}</strong><br>
                        <strong>${data.temperature}°F</strong><br>
                        ${data.conditions}
                    `;
                });
        }
    });
}

document.addEventListener("DOMContentLoaded", loadWeather);