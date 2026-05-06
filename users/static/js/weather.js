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

    // Use saved location if available — no prompt needed
    var savedLocation = document.getElementById("saved_location");
    if (savedLocation && savedLocation.value.trim()) {
        fetch("/api/weather/?city=" + encodeURIComponent(savedLocation.value.trim()))
            .then(function(r) { return r.ok ? r.json() : Promise.reject(); })
            .then(function(data) { if (data && !data.error) setWeatherUI(data); })
            .catch(function() {});
        return;
    }

    // Don't re-prompt if the user already denied this session
    if (sessionStorage.getItem("geo_denied") === "1") return;

    function onDenied() {
        sessionStorage.setItem("geo_denied", "1");
    }

    function requestLocation() {
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
            onDenied();
        });
    }

    // Check permission state first — skip prompt entirely if already denied
    if (navigator.permissions) {
        navigator.permissions.query({ name: "geolocation" }).then(function(result) {
            if (result.state === "denied") {
                onDenied();
                return;
            }
            requestLocation();
        }).catch(function() {
            requestLocation();
        });
    } else {
        requestLocation();
    }
}

function initLocationAutocomplete() {
    var locationInput = document.getElementById("location");
    var suggestionsEl = document.getElementById("locationSuggestions");
    var latInput = document.getElementById("lat");
    var lonInput = document.getElementById("lon");

    if (!locationInput || !suggestionsEl) return;

    var debounceTimer = null;
    var activeIndex = -1;
    var currentItems = [];
    var requestToken = 0;

    function clearSuggestions() {
        currentItems = [];
        activeIndex = -1;
        suggestionsEl.innerHTML = "";
        suggestionsEl.classList.remove("is-open");
        locationInput.setAttribute("aria-expanded", "false");
    }

    function setActive(index) {
        var buttons = suggestionsEl.querySelectorAll(".location-suggestion-btn");
        for (var i = 0; i < buttons.length; i += 1) {
            buttons[i].classList.toggle("is-active", i === index);
        }
        activeIndex = index;
    }

    function applySuggestion(item) {
        locationInput.value = item.city || item.label;
        if (latInput) latInput.value = String(item.lat);
        if (lonInput) lonInput.value = String(item.lon);
        clearSuggestions();

        if (!document.querySelector(".weather-icon")) return;

        fetch("/api/weather/?lat=" + encodeURIComponent(item.lat) + "&lon=" + encodeURIComponent(item.lon))
            .then(function(r) {
                if (!r.ok) throw new Error("Weather API failed");
                return r.json();
            })
            .then(function(data) {
                if (!data || data.error) throw new Error("Weather payload invalid");
                setWeatherUI(data);
            })
            .catch(function() {});
    }

    function renderSuggestions(items) {
        currentItems = items;
        activeIndex = -1;
        suggestionsEl.innerHTML = "";

        if (!items.length) {
            clearSuggestions();
            return;
        }

        for (var i = 0; i < items.length; i += 1) {
            var li = document.createElement("li");
            li.setAttribute("role", "option");

            var button = document.createElement("button");
            button.type = "button";
            button.className = "location-suggestion-btn";
            button.textContent = items[i].label;
            button.addEventListener("click", (function(item) {
                return function() {
                    applySuggestion(item);
                };
            })(items[i]));

            li.appendChild(button);
            suggestionsEl.appendChild(li);
        }

        suggestionsEl.classList.add("is-open");
        locationInput.setAttribute("aria-expanded", "true");
    }

    function fetchSuggestions(query) {
        requestToken += 1;
        var currentToken = requestToken;

        fetch("/api/location-suggest/?q=" + encodeURIComponent(query))
            .then(function(r) {
                if (!r.ok) throw new Error("Location suggest API failed");
                return r.json();
            })
            .then(function(data) {
                if (currentToken !== requestToken) return;
                renderSuggestions((data && data.suggestions) || []);
            })
            .catch(function() {
                if (currentToken !== requestToken) return;
                clearSuggestions();
            });
    }

    locationInput.addEventListener("input", function() {
        var query = locationInput.value.trim();
        if (latInput) latInput.value = "";
        if (lonInput) lonInput.value = "";

        if (query.length < 2) {
            clearSuggestions();
            return;
        }

        if (debounceTimer) {
            window.clearTimeout(debounceTimer);
        }

        debounceTimer = window.setTimeout(function() {
            fetchSuggestions(query);
        }, 220);
    });

    locationInput.addEventListener("keydown", function(e) {
        if (!currentItems.length) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((activeIndex + 1) % currentItems.length);
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((activeIndex - 1 + currentItems.length) % currentItems.length);
        } else if (e.key === "Enter") {
            if (activeIndex < 0) return;
            e.preventDefault();
            applySuggestion(currentItems[activeIndex]);
        } else if (e.key === "Escape") {
            clearSuggestions();
        }
    });

    document.addEventListener("click", function(e) {
        if (!suggestionsEl.classList.contains("is-open")) return;
        if (e.target === locationInput || suggestionsEl.contains(e.target)) return;
        clearSuggestions();
    });
}

document.addEventListener("DOMContentLoaded", function() {
    loadWeather();
    initLocationAutocomplete();
    var weatherToggle = document.getElementById("use_weather");
    if (weatherToggle) {
        weatherToggle.addEventListener("change", function() {
            if (weatherToggle.checked) {
                loadWeather();
            }
        });
    }
});