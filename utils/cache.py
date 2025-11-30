import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("cache")
CACHE_EXPIRY_HOURS = 2  # cache scade dopo 2 ore


def init_cache():
    """Crea la cartella cache se non esiste."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_key(endpoint: str, **params) -> str:
    """Genera una chiave unica per il cache basata su endpoint e parametri."""
    param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    key = f"{endpoint.strip('/').replace('/', '_')}_{param_str}"
    # pulizia caratteri non sicuri
    return "".join(c for c in key if c.isalnum() or c in "-_=.").rstrip("_")


def get_cache_path(cache_key: str) -> Path:
    """Ritorna il percorso del file cache."""
    init_cache()
    return CACHE_DIR / f"{cache_key}.json"


def is_cache_valid(cache_path: Path) -> bool:
    """Controlla se il cache è ancora valido (non scaduto)."""
    if not cache_path.exists():
        return False
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    return datetime.now() < (file_time + timedelta(hours=CACHE_EXPIRY_HOURS))


def load_from_cache(cache_key: str):
    """Carica dati dal cache se disponibili e validi, altrimenti None."""
    cache_path = get_cache_path(cache_key)
    if not is_cache_valid(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Cache HIT: {cache_key}")
        return data
    except Exception as e:
        print(f"⚠ Errore lettura cache {cache_key}: {e}")
        return None


def save_to_cache(cache_key: str, data) -> None:
    """Salva dati nel cache (lista/dict)."""
    cache_path = get_cache_path(cache_key)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Cache SAVE: {cache_key}")
    except Exception as e:
        print(f"⚠ Errore salvataggio cache {cache_key}: {e}")


def clear_cache() -> None:
    """Cancella tutti i file cache."""
    init_cache()
    try:
        for file in CACHE_DIR.glob("*.json"):
            file.unlink()
        print(f"🗑️ Cache svuotato ({CACHE_DIR})")
    except Exception as e:
        print(f"⚠ Errore svuotamento cache: {e}")


def cache_size_mb() -> float:
    """Ritorna la dimensione totale del cache in MB."""
    if not CACHE_DIR.exists():
        return 0.0
    total_size = sum(f.stat().st_size for f in CACHE_DIR.glob("*.json"))
    return total_size / (1024 * 1024)