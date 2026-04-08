import pandas as pd
import os

_df = None

# Per-activity overrides: dance tolerance, tempo range (BPM), acousticness target
# dance_tol: how strictly to filter danceability (None = use default tol)
# tempo: (min, max) BPM range, None = no filter
# acousticness: target value, None = no filter
ACTIVITY_CONSTRAINTS = {
    "sleep":   {"dance_tol": 0.10, "tempo": (40,  90),  "acousticness": 0.8},
    "study":   {"dance_tol": 0.10, "tempo": (60,  120), "acousticness": 0.5},
    "focus":   {"dance_tol": 0.10, "tempo": (60,  120), "acousticness": 0.5},
    "workout": {"dance_tol": 0.25, "tempo": (120, 180), "acousticness": None},
    "party":   {"dance_tol": 0.20, "tempo": (110, 180), "acousticness": None},
    "chill":   {"dance_tol": 0.25, "tempo": None,       "acousticness": None},
    "commute": {"dance_tol": 0.25, "tempo": None,       "acousticness": None},
    "cooking": {"dance_tol": 0.20, "tempo": None,       "acousticness": None},
}

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


def get_audio_baseline(track_list):
    """
    Given a list of (track_name, artist) tuples from recently played,
    find matches in the dataset and return average audio features.
    Returns None if fewer than 5 matches are found.
    """
    df = _load()
    energies, valences, dances = [], [], []

    for track_name, artist in track_list:
        mask = (
            df["track_name"].str.lower() == track_name.lower()
        ) & (
            df["artists"].str.lower().str.contains(artist.lower(), regex=False)
        )
        rows = df[mask]
        if not rows.empty:
            row = rows.iloc[0]
            energies.append(row["energy"])
            valences.append(row["valence"])
            dances.append(row["danceability"])

    if len(energies) < 5:
        return None

    return {
        "energy": sum(energies) / len(energies),
        "valence": sum(valences) / len(valences),
        "danceability": sum(dances) / len(dances),
    }


def _map_user_genres(user_genres, dataset_genres):
    """
    Map Spotify artist genre strings (e.g. 'indie pop') to dataset genre
    tags (e.g. 'indie-pop') using substring matching after normalization.
    """
    matched = set()
    for ug in user_genres:
        normalized = ug.lower().replace(" ", "-")
        for dg in dataset_genres:
            if dg == normalized or dg in normalized or normalized in dg:
                matched.add(dg)
    return list(matched)


def recommend_tracks(energy, happiness, danceability, activity="chill",
                     weather_features=None, limit=80,
                     user_genres=None, baseline=None, exclude_tracks=None):
    """
    Returns a list of (track_name, artist) tuples filtered by audio features.
    energy, happiness, danceability are 1-10 integer sliders.

    If baseline is provided (avg audio features from recently played),
    sliders act as adjustments (5 = neutral, each point = ±0.05).
    If user_genres is provided, they are used to bias the genre filter.
    If exclude_tracks is provided (set of lowercased track names), those
    tracks are removed from results.
    """
    df = _load()
    constraints = ACTIVITY_CONSTRAINTS.get(activity, {})

    if baseline:
        target_energy  = max(0.0, min(1.0, baseline["energy"]       + (energy       - 5) * 0.05))
        target_valence = max(0.0, min(1.0, baseline["valence"]      + (happiness    - 5) * 0.05))
        target_dance   = max(0.0, min(1.0, baseline["danceability"] + (danceability - 5) * 0.05))
    else:
        target_energy  = energy / 10
        target_valence = happiness / 10
        target_dance   = danceability / 10

    # Adjust targets based on weather
    if weather_features:
        weather_str = str(weather_features).lower()
        if "rain" in weather_str or "storm" in weather_str:
            target_valence = max(0.0, target_valence - 0.15)
            target_energy  = max(0.0, target_energy  - 0.10)
            acousticness_boost = 0.3
        elif "clear" in weather_str or "sun" in weather_str:
            target_valence = min(1.0, target_valence + 0.10)
            acousticness_boost = 0.0
        elif "snow" in weather_str or "cold" in weather_str:
            target_energy  = max(0.0, target_energy  - 0.10)
            acousticness_boost = 0.2
        else:
            acousticness_boost = 0.0
    else:
        acousticness_boost = 0.0

    tol = 0.25
    dance_tol = constraints.get("dance_tol", tol)

    audio_mask = (
        df["energy"].between(max(0.0, target_energy  - tol),       min(1.0, target_energy  + tol)) &
        df["valence"].between(max(0.0, target_valence - tol),      min(1.0, target_valence + tol)) &
        df["danceability"].between(max(0.0, target_dance - dance_tol), min(1.0, target_dance + dance_tol))
    )

    # Tempo filter
    tempo_range = constraints.get("tempo")
    if tempo_range:
        audio_mask &= df["tempo"].between(tempo_range[0], tempo_range[1])

    # Acousticness filter
    acousticness_target = constraints.get("acousticness")
    if acousticness_target is not None or acousticness_boost > 0:
        ac_target = min(1.0, (acousticness_target or 0.0) + acousticness_boost)
        audio_mask &= df["acousticness"].between(max(0.0, ac_target - 0.3), min(1.0, ac_target + 0.3))

    activity_genres = ACTIVITY_GENRES.get(activity, [])

    if user_genres:
        dataset_genres = set(df["track_genre"].unique())
        matched = _map_user_genres(user_genres, dataset_genres)

        filtered = df[audio_mask & df["track_genre"].isin(matched)]
        if len(filtered) < 20:
            combined = list(set(matched + activity_genres))
            filtered = df[audio_mask & df["track_genre"].isin(combined)]
            if len(filtered) < 20:
                filtered = df[audio_mask]
    elif activity_genres:
        filtered = df[audio_mask & df["track_genre"].isin(activity_genres)]
        if len(filtered) < 20:
            filtered = df[audio_mask]
    else:
        filtered = df[audio_mask]

    # Exclude top played tracks
    if exclude_tracks:
        filtered = filtered[~filtered["track_name"].str.lower().isin(exclude_tracks)]

    # Sample broadly first for variety, then sort by popularity within sample
    sample_size = min(limit * 4, len(filtered))
    sampled = filtered.sample(sample_size, random_state=None) if sample_size > 0 else filtered
    top = sampled.nlargest(limit, "popularity")

    return list(zip(top["track_name"], top["artists"]))
