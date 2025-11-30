import pandas as pd
import numpy as np


def compute_delta_time(df1: pd.DataFrame,
                       df2: pd.DataFrame,
                       n_points: int = 200):
    """Calcola il delta time tra due giri."""
    if df1.empty or df2.empty:
        return None, None

    df1 = df1.sort_values("t_rel_s").copy()
    df2 = df2.sort_values("t_rel_s").copy()

    df1["progress"] = np.linspace(0.0, 1.0, len(df1))
    df2["progress"] = np.linspace(0.0, 1.0, len(df2))

    grid = np.linspace(0.0, 1.0, n_points)

    t1_interp = np.interp(grid, df1["progress"], df1["t_rel_s"])
    t2_interp = np.interp(grid, df2["progress"], df2["t_rel_s"])

    delta = t2_interp - t1_interp
    return grid, delta


def parse_time_str(s):
    """Converte stringa tempo (mm:ss.s o hh:mm:ss.s) a secondi."""
    try:
        if s is None:
            return None
        if isinstance(s, (int, float, np.number)):
            return float(s)
        s = str(s).strip()
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 3:
                h = int(parts[0]); m = int(parts[1]); sec = float(parts[2])
                return h * 3600 + m * 60 + sec
            if len(parts) == 2:
                m = int(parts[0]); sec = float(parts[1])
                return m * 60 + sec
        return float(s)
    except Exception:
        return None


def fmt_duration(s: float | None) -> str:
    """Formatta durata da secondi a hh:mm:ss.sss (millisecondi, 3 cifre)."""
    if s is None:
        return "N/A"
    try:
        total_ms = int(round(float(s) * 1000))
    except Exception:
        return "N/A"

    hours = total_ms // 3_600_000
    rem = total_ms % 3_600_000
    minutes = rem // 60_000
    rem = rem % 60_000
    seconds = rem // 1000
    milliseconds = rem % 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def lap_duration_seconds_from_row(lap_row: pd.Series, df: pd.DataFrame):
    """Estrae durata del lap dai dati, con fallback progressivi."""
    for key in ("lap_duration", "lap_time", "lap_time_s", "lap_time_seconds", "duration"):
        val = lap_row.get(key) if lap_row is not None else None
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            parsed = parse_time_str(val)
            if parsed is not None:
                return parsed

    ds = lap_row.get("date_start")
    de = lap_row.get("date_end")
    if ds and de:
        try:
            return (pd.to_datetime(de) - pd.to_datetime(ds)).total_seconds()
        except Exception:
            pass

    if not df.empty and "t_rel_s" in df.columns:
        try:
            return float(df["t_rel_s"].max())
        except Exception:
            pass
    return None