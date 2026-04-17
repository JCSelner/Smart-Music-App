from django import template
 
register = template.Library()
 
# Maps every activity .
MOOD_COLORS = {
    "chill":   "#7FDBFF",
    "workout": "#FF4136",
    "study":   "#2ECC40",
    "party":   "#FFD700",
    "commute": "#FF851B",
    "sleep":   "#B10DC9",
    "cooking": "#01FF70",
    "focus":   "#0074D9",
}
_DEFAULT_COLOR = "#888888"
 
 
@register.filter
def mood_color(mood):
    """Return the hex color for a given mood/activity string."""
    return MOOD_COLORS.get((mood or "").lower(), _DEFAULT_COLOR)
