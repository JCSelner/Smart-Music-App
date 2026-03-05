function setWeatherUI(data) {
    var temp = document.querySelector(".weather-temp");
    var meta = document.querySelector(".weather-meta");
    var icon = document.querySelector(".weather-icon");
    var hint = document.querySelector(".weather-hint");
    var locationInput = document.querySelector("#location");
    var pillLoc = document.querySelector(".weather-pill__loc");
    var location = data.city || "—";
    
    if (locationInput) locationInput.value = location;
    if (pillLoc) pillLoc.textContent = location;

    if (temp) temp.textContent = Math.round(data.temperature || 0) + "°";
    if (meta) {
        var condition = data.conditions || "—";
        meta.innerHTML = "<span>" + condition + "</span><span class=\"dot\">·</span><span>" + location + "</span>";
    }
    if (icon) icon.textContent = weatherIconFromConditions(data.conditions);
    if (hint) hint.innerHTML = "Perfect for a <strong>" + moodFromConditions(data.conditions) + "</strong> playlist";
}

function weatherIconFromConditions(conditions) {
    if (!conditions) return "🌤️";
    var c = conditions.toLowerCase();
    if (c.indexOf("rain") !== -1) return "🌧️";
    if (c.indexOf("snow") !== -1) return "❄️";
    if (c.indexOf("cloud") !== -1) return "☁️";
    if (c.indexOf("clear") !== -1) return "☀️";
    if (c.indexOf("storm") !== -1 || c.indexOf("thunder") !== -1) return "⛈️";
    return "🌤️";
}

function moodFromConditions(conditions) {
    if (!conditions) return "chill";
    var c = conditions.toLowerCase();
    if (c.indexOf("rain") !== -1) return "rainy";
    if (c.indexOf("snow") !== -1) return "cozy";
    if (c.indexOf("clear") !== -1) return "upbeat";
    if (c.indexOf("cloud") !== -1) return "laid-back";
    return "chill";
}

function loadWeather() {
    navigator.geolocation.getCurrentPosition(function(pos) {
        var lat = pos.coords.latitude;
        var lon = pos.coords.longitude;

        fetch("/api/weather/?lat=" + lat + "&lon=" + lon)
            .then(function(r) { return r.json(); })
            .then(function(data) { setWeatherUI(data); })
            .catch(function() {});
    }, function() {
        // Geolocation denied — user can type their city in the location field
    });
}

document.addEventListener("DOMContentLoaded", loadWeather);