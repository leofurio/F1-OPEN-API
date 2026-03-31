BASE_URL = "https://api.openf1.org/v1"

# Colori fissi per i due piloti (coerenti su tutti i grafici)
COLOR1 = "#1f77b4"   # blu
COLOR2 = "#d62728"   # rosso

# Timeout API
API_TIMEOUT = 30

# Gestione rate-limit OpenF1
API_MAX_RETRIES = 3
API_RETRY_BACKOFF_SECONDS = 1.5

# Default per stima data_end se mancante (minuti)
DEFAULT_LAP_DURATION_MINUTES = 2
