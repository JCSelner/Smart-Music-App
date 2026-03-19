import pandas as pd
import os

_df = None

ACTIVITY_GENRES = {
    "chill":   ["chill", "ambient", "acoustic", "singer-songwriter", "folk", "new-age", "sleep"],
    "workout": ["work-out", "hip-hop", "edm", "power-pop", "dance", "electronic", "hardstyle", "hard-rock"],
    "study":   ["study", "classical", "ambient", "piano", "new-age", "idm"],
    "party":   ["party", "dance", "edm", "pop", "hip-hop", "club", "dancehall", "disco"],
    "commute": ["road-trip", "alternative", "pop", "indie", "rock", "indie-pop"],
    "sleep":   ["sleep", "ambient", "classical", "piano", "new-age"],
    "cooking": ["funk", "soul", "groove", "pop", "r-n-b", "reggae"],
    "focus":   ["study", "classical", "ambient", "piano", "new-age", "idm"],
}


def _load():
    global _df
    if _df is None:
        path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "spotify_dataset.csv")
        )
        _df = pd.read_csv(path)
    return _df


def recommend_tracks(energy, happiness, danceability, activity="chill", weather_features=None, limit=80):
    """
    Returns a list of (track_name, artist) tuples filtered by audio features.
    energy, happiness, danceability are 1-10 integer sliders.
    """
    df = _load()

    # Normalize sliders (1-10) to 0.0-1.0
    target_energy   = energy / 10
    target_valence  = happiness / 10
    target_dance    = danceability / 10

    # Adjust targets based on weather
    if weather_features:
        weather_str = str(weather_features).lower()
        if "rain" in weather_str or "storm" in weather_str:
            target_valence = max(0.0, target_valence - 0.15)
            target_energy  = max(0.0, target_energy  - 0.10)
        elif "clear" in weather_str or "sun" in weather_str:
            target_valence = min(1.0, target_valence + 0.10)
        elif "snow" in weather_str or "cold" in weather_str:
            target_energy  = max(0.0, target_energy  - 0.10)

    tol = 0.25

    audio_mask = (
        df["energy"].between(max(0.0, target_energy  - tol), min(1.0, target_energy  + tol)) &
        df["valence"].between(max(0.0, target_valence - tol), min(1.0, target_valence + tol)) &
        df["danceability"].between(max(0.0, target_dance - tol), min(1.0, target_dance + tol))
    )

    genres = ACTIVITY_GENRES.get(activity, [])
    if genres:
        filtered = df[audio_mask & df["track_genre"].isin(genres)]
        if len(filtered) < 20:
            filtered = df[audio_mask]
    else:
        filtered = df[audio_mask]

    # Take top by popularity then sample for variety
    top = filtered.nlargest(limit * 2, "popularity")
    sampled = top.sample(min(limit, len(top)), random_state=None)

    return list(zip(sampled["track_name"], sampled["artists"]))
