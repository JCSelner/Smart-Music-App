function setWeatherUI(data) {
    var temp = document.querySelector(".weather-temp");
    var meta = document.querySelector(".weather-meta");
    var icon = document.querySelector(".weather-icon");
    var hint = document.querySelector(".weather-hint");
    var contextSub = document.querySelector(".context-weather__sub");
    var locationInput = document.querySelector("#location");
    var pillLoc = document.querySelector(".weather-pill__loc");
    var location = data.city || "—";
    
    if (locationInput) locationInput.value = location;
    if (pillLoc) pillLoc.textContent = location;

    if (temp) {
        temp.textContent = Math.round(data.temperature || 0) + "°";
    }
    if (meta) {
        var condition = data.conditions || "—";
        meta.innerHTML = "<span>" + condition + "</span><span class=\"dot\">·</span><span>" + location + "</span>";
    }
    if (icon) icon.textContent = weatherIconFromConditions(data.conditions);
    if (hint) hint.innerHTML = "Perfect for a <strong>" + moodFromConditions(data.conditions) + "</strong> playlist";
    if (contextSub) {
        var mood = moodFromConditions(data.conditions);
        contextSub.textContent = "Weather mood: " + mood + " (auto-adjusted sliders)";
    }

    applyWeatherToSliders(data);
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

function applyWeatherToSliders(data) {
    var condition = (data.conditions || "").toLowerCase();
    var temp = Number(data.temperature || 70);

    var values = {
        energy: 5,
        happiness: 5,
        danceability: 5
    };

    if (condition.indexOf("rain") !== -1 || condition.indexOf("storm") !== -1 || condition.indexOf("thunder") !== -1) {
        values.energy = 3;
        values.happiness = 3;
        values.danceability = 2;
    } else if (condition.indexOf("clear") !== -1 || condition.indexOf("sun") !== -1) {
        values.energy = 8;
        values.happiness = 8;
        values.danceability = 8;
    } else if (condition.indexOf("cloud") !== -1 || condition.indexOf("overcast") !== -1) {
        values.energy = 5;
        values.happiness = 5;
        values.danceability = 5;
    } else if (condition.indexOf("snow") !== -1) {
        values.energy = 4;
        values.happiness = 6;
        values.danceability = 3;
    }

    if (temp > 85) {
        values.energy = Math.min(10, values.energy + 1);
        values.danceability = Math.min(10, values.danceability + 1);
    } else if (temp < 32) {
        values.energy = Math.max(1, values.energy - 1);
    }

    setSliderValue("energy", "energyVal", values.energy);
    setSliderValue("happiness", "happyVal", values.happiness);
    setSliderValue("danceability", "danceVal", values.danceability);
    setActivityFromWeather(condition);
}

function setActivityFromWeather(condition) {
    var activityValue = "chill";

    if (condition.indexOf("clear") !== -1 || condition.indexOf("sun") !== -1) {
        activityValue = "party";
    } else if (condition.indexOf("rain") !== -1 || condition.indexOf("storm") !== -1 || condition.indexOf("thunder") !== -1) {
        activityValue = "chill";
    } else if (condition.indexOf("snow") !== -1) {
        activityValue = "focus";
    } else if (condition.indexOf("cloud") !== -1 || condition.indexOf("overcast") !== -1) {
        activityValue = "commute";
    }

    var radio = document.querySelector('input[name="activity"][value="' + activityValue + '"]');
    if (radio) {
        radio.checked = true;
    }
}

function setSliderValue(sliderId, labelId, value) {
    var slider = document.getElementById(sliderId);
    var label = document.getElementById(labelId);
    if (!slider || !label) return;

    slider.value = String(value);
    label.textContent = String(value);

    var min = Number(slider.min || 1);
    var max = Number(slider.max || 10);
    var pct = ((Number(value) - min) / (max - min)) * 100;
    slider.style.setProperty("--pct", pct + "%");
}

function loadWeather() {
    var weatherToggle = document.getElementById("use_weather");
    if (weatherToggle && !weatherToggle.checked) return;

    navigator.geolocation.getCurrentPosition(function(pos) {
        var lat = pos.coords.latitude;
        var lon = pos.coords.longitude;

        var latInput = document.getElementById("lat");
        var lonInput = document.getElementById("lon");
        if (latInput) latInput.value = String(lat);
        if (lonInput) lonInput.value = String(lon);

        fetch("/api/weather/?lat=" + lat + "&lon=" + lon)
            .then(function(r) {
                if (!r.ok) throw new Error("Weather API failed");
                return r.json();
            })
            .then(function(data) {
                if (!data || data.error) throw new Error("Weather payload invalid");
                setWeatherUI(data);
            })
            .catch(function() {});
    }, function() {
        var city = prompt("Enter city:");
        if (!city) return;

        fetch("/api/weather/?city=" + city)
            .then(function(r) {
                if (!r.ok) throw new Error("Weather API failed");
                return r.json();
            })
            .then(function(data) {
                if (!data || data.error) throw new Error("Weather payload invalid");
                setWeatherUI(data);
            })
            .catch(function() {});
    });
}

document.addEventListener("DOMContentLoaded", function() {
    loadWeather();
    var weatherToggle = document.getElementById("use_weather");
    if (weatherToggle) {
        weatherToggle.addEventListener("change", function() {
            if (weatherToggle.checked) {
                loadWeather();
            }
        });
    }
});