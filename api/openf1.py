import requests
import pandas as pd
from urllib.parse import urlencode
from datetime import timedelta
from config import BASE_URL, API_TIMEOUT, DEFAULT_LAP_DURATION_MINUTES
from utils.cache import get_cache_key, load_from_cache, save_to_cache


def _build_dataframe(data, required_columns: list[str]) -> pd.DataFrame:
    """Converte il payload API in DataFrame garantendo le colonne richieste."""
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    return df


def _fetch_json(endpoint: str, params: dict | None = None, cache_suffix: str | None = None):
    """Recupera un endpoint OpenF1 usando cache file-based."""
    params = params or {}
    cache_key = get_cache_key(endpoint, **params, cache_suffix=cache_suffix or "base")
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        return cached_data

    url = f"{BASE_URL}/{endpoint.strip('/')}"
    if cache_suffix:
        query_string = urlencode(params)
        separator = '&' if query_string else ''
        full_url = f"{url}?{query_string}{separator}{cache_suffix}"
        resp = requests.get(full_url, timeout=API_TIMEOUT)
    else:
        resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    save_to_cache(cache_key, data)
    return data


def fetch_meetings(year: int | None = None) -> pd.DataFrame:
    """Recupera i meeting (Gran Premi) per anno."""
    params = {}
    if year:
        params["year"] = year
    data = _fetch_json("meetings", params=params)
    return _build_dataframe(data, ["meeting_key", "year", "country_name", "meeting_name"])


def fetch_sessions(meeting_key: int) -> pd.DataFrame:
    """Recupera le sessioni per un meeting."""
    params = {"meeting_key": meeting_key}
    data = _fetch_json("sessions", params=params)
    return _build_dataframe(data, ["session_key", "session_name", "session_type"])


def fetch_laps(session_key: int) -> pd.DataFrame:
    """Recupera i giri per una sessione."""
    params = {"session_key": session_key}
    data = _fetch_json("laps", params=params)
    return _build_dataframe(data, ["driver_number", "lap_number", "date_start", "date_end"])


def fetch_drivers(session_key: int) -> pd.DataFrame:
    """Recupera i piloti per una sessione."""
    params = {"session_key": session_key}
    data = _fetch_json("drivers", params=params)
    return _build_dataframe(data, ["driver_number", "full_name", "name_acronym", "team_name"])


def fetch_stints(session_key: int) -> pd.DataFrame:
    """Recupera le info stint (compound, lap start/end) per una sessione."""
    params = {"session_key": session_key}
    data = _fetch_json("stints", params=params)
    return _build_dataframe(
        data,
        ["driver_number", "stint_number", "compound", "lap_start", "lap_end", "tyre_life", "new"],
    )


def fetch_pitstops(session_key: int) -> pd.DataFrame:
    """Recupera i pit stop per una sessione."""
    params = {"session_key": session_key}
    data = _fetch_json("pit", params=params)
    return _build_dataframe(data, ["driver_number", "lap_number", "pit_duration", "pit_duration_ms"])


def fetch_car_data_for_lap(session_key: int,
                           driver_number: int,
                           lap_row: pd.Series) -> pd.DataFrame:
    """Recupera i dati di telemetria /car_data per un singolo giro."""
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end")

    if not date_start:
        return pd.DataFrame()

    if not date_end:
        start_dt = pd.to_datetime(date_start, errors="coerce", utc=True)
        if pd.isna(start_dt):
            return pd.DataFrame()
        date_end = (start_dt + timedelta(minutes=DEFAULT_LAP_DURATION_MINUTES)).isoformat()
        print(f"⚠ date_end era None, usando stima: {date_end}")

    params = {
        "session_key": session_key,
        "driver_number": driver_number,
    }
    date_filter = f"date>{date_start}&date<{date_end}"
    full_url = f"{BASE_URL}/car_data?{urlencode(params)}&{date_filter}"
    print(f"🔗 Query URL (car_data): {full_url}")

    data = _fetch_json("car_data", params=params, cache_suffix=date_filter)

    if not data:
        print(f"⚠ Nessun car_data trovato per driver {driver_number}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        df = df.dropna(subset=["date"]).sort_values("date")
        if df.empty:
            return pd.DataFrame()
        t0 = df["date"].min()
        df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
    else:
        df["t_rel_s"] = range(len(df))

    for col in ["speed", "throttle", "brake", "n_gear"]:
        if col not in df.columns:
            df[col] = None

    return df


def fetch_location_for_lap(session_key: int,
                           driver_number: int,
                           lap_row: pd.Series) -> pd.DataFrame:
    """Recupera i dati di posizione /location per un singolo giro."""
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end")

    if not date_start:
        return pd.DataFrame()

    if not date_end:
        start_dt = pd.to_datetime(date_start, errors="coerce", utc=True)
        if pd.isna(start_dt):
            return pd.DataFrame()
        date_end = (start_dt + timedelta(minutes=DEFAULT_LAP_DURATION_MINUTES)).isoformat()
        print(f"⚠ (location) date_end era None, usando stima: {date_end}")

    params = {
        "session_key": session_key,
        "driver_number": driver_number,
    }
    date_filter = f"date>{date_start}&date<{date_end}"
    full_url = f"{BASE_URL}/location?{urlencode(params)}&{date_filter}"
    print(f"🔗 Query URL (location): {full_url}")

    data = _fetch_json("location", params=params, cache_suffix=date_filter)
    if not data:
        print(f"⚠ Nessun location trovato per driver {driver_number}")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
        df = df.dropna(subset=["date"]).sort_values("date")
        if df.empty:
            return pd.DataFrame()
        t0 = df["date"].min()
        df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
    else:
        df["t_rel_s"] = range(len(df))

    for col in ["x", "y", "z"]:
        if col not in df.columns:
            df[col] = None

    return df
