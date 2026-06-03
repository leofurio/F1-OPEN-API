import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_EXPIRY_HOURS = 6


def init_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_key(endpoint: str, **params) -> str:
    param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    key = f"{endpoint.strip('/').replace('/', '_')}_{param_str}"
    return "".join(c for c in key if c.isalnum() or c in "-_=.").rstrip("_")


def get_cache_path(cache_key: str) -> Path:
    init_cache()
    return CACHE_DIR / f"{cache_key}.json"


def is_cache_valid(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    return datetime.now() < (file_time + timedelta(hours=CACHE_EXPIRY_HOURS))


def load_from_cache(cache_key: str):
    cache_path = get_cache_path(cache_key)
    if not is_cache_valid(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug("Cache HIT: %s", cache_key)
        return data
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Errore lettura cache %s: %s", cache_key, e)
        return None


def save_to_cache(cache_key: str, data) -> None:
    cache_path = get_cache_path(cache_key)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug("Cache SAVE: %s", cache_key)
    except OSError as e:
        logger.warning("Errore salvataggio cache %s: %s", cache_key, e)


def clear_cache() -> None:
    init_cache()
    try:
        for file in CACHE_DIR.glob("*.json"):
            file.unlink()
        logger.info("Cache svuotato (%s)", CACHE_DIR)
    except OSError as e:
        logger.warning("Errore svuotamento cache: %s", e)


def cache_size_mb() -> float:
    if not CACHE_DIR.exists():
        return 0.0
    return sum(f.stat().st_size for f in CACHE_DIR.glob("*.json")) / (1024 * 1024)
