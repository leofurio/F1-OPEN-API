import requests
import pandas as pd
from urllib.parse import urlencode
from datetime import timedelta
from config import BASE_URL, API_TIMEOUT, DEFAULT_LAP_DURATION_MINUTES


def fetch_meetings(year: int | None = None) -> pd.DataFrame:
    """Recupera i meeting (Gran Premi) per anno."""
    params = {}
    if year:
        params["year"] = year
    url = f"{BASE_URL}/meetings"
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["meeting_key", "year", "country_name", "meeting_name"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_sessions(meeting_key: int) -> pd.DataFrame:
    """Recupera le sessioni per un meeting."""
    params = {"meeting_key": meeting_key}
    url = f"{BASE_URL}/sessions"
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["session_key", "session_name", "session_type"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_laps(session_key: int) -> pd.DataFrame:
    """Recupera i giri per una sessione."""
    params = {"session_key": session_key}
    url = f"{BASE_URL}/laps"
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["driver_number", "lap_number", "date_start", "date_end"]:
        if col not in df.columns:
            df[col] = None
    return df


def fetch_drivers(session_key: int) -> pd.DataFrame:
    """Recupera i piloti per una sessione."""
    params = {"session_key": session_key}
    url = f"{BASE_URL}/drivers"
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for col in ["driver_number", "full_name", "name_acronym", "team_name"]:
        if col not in df.columns:
            df[col] = None
    return df


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

    url = f"{BASE_URL}/car_data"
    query_string = urlencode(params)
    query_string += f"&date>{date_start}&date<{date_end}"
    full_url = f"{url}?{query_string}"
    print(f"🔗 Query URL (car_data): {full_url}")

    resp = requests.get(full_url, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

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

    url = f"{BASE_URL}/location"
    query_string = urlencode(params)
    query_string += f"&date>{date_start}&date<{date_end}"
    full_url = f"{url}?{query_string}"
    print(f"🔗 Query URL (location): {full_url}")

    resp = requests.get(full_url, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
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
