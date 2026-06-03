import logging
import requests
import pandas as pd
from urllib.parse import urlencode
from datetime import timedelta
import time
from datetime import timedelta
from urllib.parse import urlencode

import pandas as pd
import requests

from config import (
    API_MAX_RETRIES,
    API_RETRY_BACKOFF_SECONDS,
    API_TIMEOUT,
    BASE_URL,
    DEFAULT_LAP_DURATION_MINUTES,
    MAX_DRIVER_NUMBER,
    MAX_MEETING_KEY,
    MAX_SESSION_KEY,
    MIN_SUPPORTED_YEAR,
)
from utils.cache import get_cache_key, load_from_cache, save_to_cache
from utils.security import coerce_int

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


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
    sanitized_params = {key: value for key, value in params.items() if value is not None}
    cache_key = get_cache_key(endpoint, **sanitized_params, cache_suffix=cache_suffix or "base")
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        return cached_data

    url = f"{BASE_URL}/{endpoint.strip('/')}"
    attempts = API_MAX_RETRIES + 1
    last_error = None

    for attempt in range(1, attempts + 1):
        if cache_suffix:
            query_string = urlencode(sanitized_params)
            separator = "&" if query_string else ""
            full_url = f"{url}?{query_string}{separator}{cache_suffix}"
            resp = requests.get(full_url, timeout=API_TIMEOUT)
        else:
            resp = requests.get(url, params=sanitized_params, timeout=API_TIMEOUT)

        if resp.status_code == 404:
            logger.info(
                "OpenF1 returned 404 for endpoint=%s params=%s",
                endpoint,
                sanitized_params,
            )
            return []

        if resp.status_code != 429:
            resp.raise_for_status()
            data = resp.json()
            save_to_cache(cache_key, data)
            return data

        last_error = requests.HTTPError(
            f"429 Too Many Requests for {resp.url}",
            response=resp,
        )
        if attempt >= attempts:
            break

        retry_after = resp.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            wait_seconds = float(retry_after)
        else:
            wait_seconds = API_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
        logger.warning(
            "Rate limit on %s: attempt %s/%s. Waiting %.1fs.",
            endpoint,
            attempt,
            attempts,
            wait_seconds,
        )
        time.sleep(wait_seconds)

    raise requests.HTTPError(
        "OpenF1 ha risposto con 429 (Too Many Requests). "
        "Riprova tra poco o riduci la frequenza delle richieste."
    ) from last_error


def fetch_meetings(year: int | None = None) -> pd.DataFrame:
    """Recupera i meeting (Gran Premi) per anno."""
    params = {}
    if year is not None:
        params["year"] = coerce_int(year, field_name="year", minimum=MIN_SUPPORTED_YEAR)
    data = _fetch_json("meetings", params=params)
    return _build_dataframe(data, ["meeting_key", "year", "country_name", "meeting_name"])


def fetch_sessions(meeting_key: int) -> pd.DataFrame:
    """Recupera le sessioni per un meeting."""
    params = {"meeting_key": coerce_int(meeting_key, field_name="meeting_key", minimum=1, maximum=MAX_MEETING_KEY)}
    data = _fetch_json("sessions", params=params)
    return _build_dataframe(data, ["session_key", "session_name", "session_type"])


def fetch_laps(session_key: int) -> pd.DataFrame:
    """Recupera i giri per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("laps", params=params)
    return _build_dataframe(data, ["driver_number", "lap_number", "date_start", "date_end"])


def fetch_drivers(session_key: int) -> pd.DataFrame:
    """Recupera i piloti per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("drivers", params=params)
    df = _build_dataframe(
        data,
        [
            "driver_number",
            "full_name",
            "name_acronym",
            "team_name",
            "broadcast_name",
            "first_name",
            "last_name",
        ],
    )

    if df.empty:
        return df

    df["driver_number"] = pd.to_numeric(df["driver_number"], errors="coerce")
    df = df.dropna(subset=["driver_number"]).copy()
    df["driver_number"] = df["driver_number"].astype(int)

    missing_full_name = df["full_name"].isna() | (df["full_name"].astype(str).str.strip() == "")
    combined = (
        df["first_name"].fillna("").astype(str).str.strip()
        + " "
        + df["last_name"].fillna("").astype(str).str.strip()
    ).str.strip()
    df.loc[missing_full_name, "full_name"] = (
        combined.where(combined != "", None)
        .fillna(df["broadcast_name"])
        .fillna(df["name_acronym"])
    )

    return df


def fetch_stints(session_key: int) -> pd.DataFrame:
    """Recupera le info stint (compound, lap start/end) per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("stints", params=params)
    return _build_dataframe(
        data,
        ["driver_number", "stint_number", "compound", "lap_start", "lap_end", "tyre_life", "new"],
    )


def fetch_pitstops(session_key: int) -> pd.DataFrame:
    """Recupera i pit stop per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("pit", params=params)
    return _build_dataframe(data, ["driver_number", "lap_number", "pit_duration", "pit_duration_ms"])


def fetch_race_control(session_key: int) -> pd.DataFrame:
    """Recupera gli eventi race control per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("race_control", params=params)
    return _build_dataframe(
        data,
        [
            "category",
            "date",
            "driver_number",
            "flag",
            "lap_number",
            "meeting_key",
            "message",
            "scope",
            "sector",
            "session_key",
        ],
    )


def fetch_weather(session_key: int) -> pd.DataFrame:
    """Recupera i dati meteo di una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("weather", params=params)
    return _build_dataframe(
        data,
        [
            "air_temperature",
            "date",
            "humidity",
            "meeting_key",
            "pressure",
            "rainfall",
            "session_key",
            "track_temperature",
            "wind_direction",
            "wind_speed",
        ],
    )


def fetch_position(session_key: int) -> pd.DataFrame:
    """Recupera la timeline delle posizioni per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("position", params=params)
    return _build_dataframe(
        data,
        [
            "date",
            "driver_number",
            "meeting_key",
            "position",
            "session_key",
        ],
    )


def fetch_overtakes(session_key: int) -> pd.DataFrame:
    """Recupera i sorpassi per una sessione."""
    params = {"session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY)}
    data = _fetch_json("overtakes", params=params)
    return _build_dataframe(
        data,
        [
            "date",
            "meeting_key",
            "overtaken_driver_number",
            "overtaking_driver_number",
            "position",
            "session_key",
        ],
    )


def _estimate_date_end(date_start) -> str | None:
    if not date_start:
        return None

    start_dt = pd.to_datetime(date_start, errors="coerce", utc=True)
    if pd.isna(start_dt):
        return None
    return (start_dt + timedelta(minutes=DEFAULT_LAP_DURATION_MINUTES)).isoformat()


def fetch_car_data_for_lap(session_key: int, driver_number: int, lap_row: pd.Series) -> pd.DataFrame:
    """Recupera i dati di telemetria /car_data per un singolo giro."""
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end") or _estimate_date_end(date_start)

    if not date_start or not date_end:
        return pd.DataFrame()

    if not date_end:
        start_dt = pd.to_datetime(date_start, errors="coerce", utc=True)
        if pd.isna(start_dt):
            return pd.DataFrame()
        date_end = (start_dt + timedelta(minutes=DEFAULT_LAP_DURATION_MINUTES)).isoformat()
        logger.warning("date_end era None per driver %d, usando stima: %s", driver_number, date_end)

    params = {
        "session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY),
        "driver_number": coerce_int(driver_number, field_name="driver_number", minimum=1, maximum=MAX_DRIVER_NUMBER),
    }
    date_filter = f"date>{date_start}&date<{date_end}"
    logger.debug("Query URL (car_data): %s/car_data?%s&%s", BASE_URL, urlencode(params), date_filter)

    data = _fetch_json("car_data", params=params, cache_suffix=date_filter)

    if not data:
        logger.warning("Nessun car_data trovato per driver %d", driver_number)
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


def fetch_location_for_lap(session_key: int, driver_number: int, lap_row: pd.Series) -> pd.DataFrame:
    """Recupera i dati di posizione /location per un singolo giro."""
    date_start = lap_row.get("date_start")
    date_end = lap_row.get("date_end") or _estimate_date_end(date_start)

    if not date_start or not date_end:
        return pd.DataFrame()

    if not date_end:
        start_dt = pd.to_datetime(date_start, errors="coerce", utc=True)
        if pd.isna(start_dt):
            return pd.DataFrame()
        date_end = (start_dt + timedelta(minutes=DEFAULT_LAP_DURATION_MINUTES)).isoformat()
        logger.warning("(location) date_end era None per driver %d, usando stima: %s", driver_number, date_end)

    params = {
        "session_key": coerce_int(session_key, field_name="session_key", minimum=1, maximum=MAX_SESSION_KEY),
        "driver_number": coerce_int(driver_number, field_name="driver_number", minimum=1, maximum=MAX_DRIVER_NUMBER),
    }
    date_filter = f"date>{date_start}&date<{date_end}"
    logger.debug("Query URL (location): %s/location?%s&%s", BASE_URL, urlencode(params), date_filter)

    data = _fetch_json("location", params=params, cache_suffix=date_filter)
    if not data:
        logger.warning("Nessun location trovato per driver %d", driver_number)
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
