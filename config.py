BASE_URL = "https://api.openf1.org/v1"

# Colori fissi per i due piloti (coerenti su tutti i grafici)
COLOR1 = "#e10600"   # F1 red   — Pilota 1
COLOR2 = "#0090d0"   # sky blue — Pilota 2

# Timeout API
API_TIMEOUT = 30
API_MAX_ITEMS = 20000
MIN_SUPPORTED_YEAR = 2018
MAX_DRIVER_NUMBER = 999
MAX_SESSION_KEY = 999999
MAX_MEETING_KEY = 999999
MAX_LAP_NUMBER = 500

# Gestione rate-limit OpenF1
API_MAX_RETRIES = 3
API_RETRY_BACKOFF_SECONDS = 1.5

# Default per stima data_end se mancante (minuti)
DEFAULT_LAP_DURATION_MINUTES = 2
