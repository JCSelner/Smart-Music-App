(function () {
    const STORAGE_KEY = "theme";
    const root = document.documentElement;

    function getSavedTheme() {
        return localStorage.getItem(STORAGE_KEY) || "dark";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        localStorage.setItem(STORAGE_KEY, theme);

        const btn = document.getElementById("theme-toggle");
        if (btn) {
            btn.textContent = theme === "dark" ? "☀️ Light" : "🌙 Dark";
            btn.setAttribute(
                "aria-label",
                theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            );
        }
    }

    function toggleTheme() {
        const current = root.getAttribute("data-theme") || "dark";
        applyTheme(current === "dark" ? "light" : "dark");
    }

    function ensureToggleButton() {
        if (document.getElementById("theme-toggle")) return;

        const button = document.createElement("button");
        button.id = "theme-toggle";
        button.className = "theme-toggle";
        button.type = "button";
        button.addEventListener("click", toggleTheme);

        document.body.appendChild(button);
        applyTheme(getSavedTheme());
    }

    applyTheme(getSavedTheme());

    document.addEventListener("DOMContentLoaded", ensureToggleButton);
})();