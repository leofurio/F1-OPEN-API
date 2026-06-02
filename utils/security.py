import logging
import math
import os

logger = logging.getLogger(__name__)

SAFE_ERROR_MESSAGE = "Si e verificato un errore durante il caricamento dei dati."


def is_debug_enabled() -> bool:
    """Enable debug only through an explicit environment variable."""
    value = os.getenv("DASH_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def sanitize_error_message(_error: Exception | None = None) -> str:
    """Return a generic user-facing error while logging the detailed exception."""
    if _error is not None:
        logger.exception("Unhandled application error", exc_info=_error)
    return SAFE_ERROR_MESSAGE


def coerce_int(
    value,
    *,
    field_name: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Validate user-provided numeric values before using them in remote requests."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value is None:
        raise ValueError(f"{field_name} is required")

    try:
        if isinstance(value, float):
            if not math.isfinite(value) or not value.is_integer():
                raise ValueError
            parsed = int(value)
        else:
            text = str(value).strip()
            if not text:
                raise ValueError
            parsed = int(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc

    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field_name} must be <= {maximum}")
    return parsed
