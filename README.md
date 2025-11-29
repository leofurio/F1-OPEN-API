# OpenF1 Driver Comparison Dashboard

Dashboard Dash per comparare la telemetria di due piloti su giri diversi usando l'API OpenF1.

## 📋 Descrizione breve
- Seleziona Anno → Circuito → Sessione → Piloti → Giro 1 / Giro 2
- Visualizza: **tracciato (location), delta time, velocità, throttle, brake, gear**
- I dati vengono cacheati con `dcc.Store` per ridurre le chiamate API
- **Click/Hover** sui grafici di telemetria per vedere la posizione sulla pista

## 📦 Dipendenze
```bash
pip install requests pandas dash plotly numpy
```

## 🚀 Avvio (Windows)
```powershell
cd "c:\F1 OPEN API"
python main.py
# apri http://127.0.0.1:8050
```

## 📁 Struttura del progetto

```
F1 OPEN API/
├── main.py                 # Entry point (app.run)
├── config.py               # Costanti (BASE_URL, COLORI, TIMEOUT)
├── api/
│   └── openf1.py          # Helper API (fetch_meetings, fetch_sessions, ecc.)
├── callbacks/
│   ├── __init__.py
│   ├── meetings.py        # Callback carica circuiti e sessioni
│   ├── drivers.py         # Callback carica piloti e giri
│   └── graphs.py          # Callback aggiorna grafici (tracciato, delta, telemetria)
├── components/
│   ├── __init__.py
│   └── layout.py          # Layout Dash HTML
├── utils/
│   ├── __init__.py
│   └── telemetry.py       # Utility: compute_delta_time, parse_time_str, ecc.
└── README.md              # Questo file
```

## 🔄 Flusso dell'applicazione

```
1. Seleziona ANNO
         ↓
2. Clicca "Carica Circuiti"
         ↓
3. Seleziona CIRCUITO (Gran Premio)
         ↓
4. Seleziona SESSIONE (FP1, FP2, Qualifiche, Gara, Sprint)
         ↓
5. Carica LAPS & DRIVERS per la sessione
         ↓
6. Seleziona PILOTA 1 → scegliRegna GIRO 1
   Seleziona PILOTA 2 → scegli GIRO 2
         ↓
7. Visualizza 6 GRAFICI comparativi:
   - Tracciato (location x-y)
   - Delta time (differenza tempo tra i due giri)
   - Velocità (km/h vs tempo)
   - Throttle (% vs tempo)
   - Brake (valore vs tempo)
   - Marcia (gear vs tempo)
```

## 🎨 Funzionalità principali

### ✅ Selezione dinamica con Dropdown
Ogni dropdown si aggiorna in base alle scelte precedenti:
- Cambio circuito → carica nuove sessioni
- Cambio sessione → carica piloti e giri
- Cambio pilota → carica giri disponibili per quel pilota

### ✅ Comparazione di giri **indipendenti**
Puoi comparare il **giro 45 del Pilota 1** con il **giro 50 del Pilota 2**.
Ogni pilota ha il suo dropdown di selezione del giro.

### ✅ Durata giro nelle leggende
Ogni traccia nei grafici mostra la durata totale del giro: `"#1 – Max Verstappen (Red Bull) – Lap 15 (durata: 1:45.234)"`

### ✅ Click/Hover interattivo
- **Hover** su un grafico di telemetria: mostra il valore
- **Click** su un grafico: aggiunge una linea verticale e un marcatore sulla pista indicando la posizione esatta del pilota in quel momento

## 📊 I 6 grafici spiegati

| Grafico | Descrizione |
|---------|------------|
| **Tracciato** | Posizione x-y sulla pista; mostra due linee colorate (una per pilota). Click/Hover aggiunge marcatori. |
| **Delta time** | Differenza di tempo tra i due giri lungo il percorso. Valore >0 = Pilota 2 è più lento. |
| **Velocità** | km/h nel corso del giro. Mostra dove ogni pilota accelera/decelera. |
| **Throttle** | Pressione acceleratore (%). Mostra aggressività e gestione. |
| **Brake** | Valore frenata. Mostra tecnica di frenata e tempistica. |
| **Marcia** | Numero di marcia inserita. Sequenza di cambiate durante il giro. |

## 🛠️ Moduli spiegati

### `config.py`
Costanti globali:
- `BASE_URL`: URL API OpenF1
- `COLOR1`, `COLOR2`: Colori fissi per i due piloti (blu, rosso)
- `API_TIMEOUT`: Timeout richieste HTTP
- `DEFAULT_LAP_DURATION_MINUTES`: Stima durata se `date_end` mancante

### `api/openf1.py`
Helper per le API:
- `fetch_meetings(year)`: Circuiti per anno
- `fetch_sessions(meeting_key)`: Sessioni per circuito
- `fetch_laps(session_key)`: Giri della sessione
- `fetch_drivers(session_key)`: Piloti + nomi/team
- `fetch_car_data_for_lap()`: Telemetria (speed, throttle, brake, gear)
- `fetch_location_for_lap()`: Posizione (x, y) sulla pista

### `utils/telemetry.py`
Utility:
- `compute_delta_time()`: Calcola differenza tempo tra due giri
- `parse_time_str()`: Converte "mm:ss.s" → secondi
- `fmt_duration()`: Formatta secondi → "mm:ss.s"
- `lap_duration_seconds_from_row()`: Estrae durata da dati lap (con fallback)

### `callbacks/meetings.py`
Callback:
1. `load_meetings()`: Carica circuiti anno selezionato
2. `load_sessions()`: Carica sessioni del circuito

### `callbacks/drivers.py`
Callback:
1. `load_laps_and_drivers()`: Carica giri e piloti della sessione
2. `update_lap_dropdowns()`: Aggiorna giri disponibili per pilota selezionato

### `callbacks/graphs.py`
Callback:
1. `update_graphs()`: Genera i 6 grafici (principale)
2. `update_selected_time()`: Cattura click/hover dai grafici e aggiorna markers sulla pista

### `components/layout.py`
Struttura HTML/Dash dell'interfaccia.

## ⚙️ Dettagli tecnici

### Gestione `date_end` mancante
L'API OpenF1 a volte non fornisce `date_end` per i giri.  
**Soluzione**: Se `date_end` è `None`, si stima automaticamente un intervallo di **2 minuti** (durata tipica giro F1).

```python
if not date_end:
    start_dt = pd.to_datetime(date_start)
    date_end = (start_dt + timedelta(minutes=2)).isoformat()
```

### Normalizzazione tempo relativo
I dati grezzi hanno timestamp assoluti. Vengono normalizzati a "tempo relativo da inizio giro" (in secondi):

```python
t0 = df["date"].min()
df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
```

Così i grafici iniziano sempre da `t=0` indipendentemente dall'orario reale.

### Delta time con interpolazione
Per comparare due giri di lunghezza diversa, il delta time viene calcolato con interpolazione lineare a 200 punti:

```python
progress = np.linspace(0.0, 1.0, n_points)  # 0% → 100% del giro
delta_time = interp(progress, giro2) - interp(progress, giro1)
```

## 🐛 Troubleshooting

| Problema | Soluzione |
|----------|----------|
| "Nessun car_data trovato" | L'API potrebbe non avere telemetria per quella sessione/giro; controlla i log nel terminale (URL di query stampati). |
| Dropdown vuoti | Aspetta il caricamento, a volte ci vogliono secondi. Controlla la connessione internet. |
| Errore timeout | La connessione API è lenta; prova di nuovo o usa una sessione più recente. |
| Grafici non si aggiornano | Assicurati che session_key, piloti e giri siano tutti selezionati e non `None`. |
| Click sulla pista non aggiunge marcatori | Deve essere un click su uno dei grafici di telemetria (speed, throttle, brake, gear), non sul tracciato. |
| Durata giro mostra "N/A" | I dati del lap non contengono il campo durata; il sistema fallback a calcoli interni. |

## 💡 Suggerimenti per migliorare

- **Esporta dati**: Aggiungi pulsante per scaricare CSV con i dati grezzi
- **Analisi statistiche**: Media velocità, velocità max, delta medio
- **Multi-lap**: Confronta più di 2 giri contemporaneamente
- **Salvataggio locale**: Cache il risultato di query API già fatte
- **Dark mode**: Aggiungi tema scuro

## 🔗 API OpenF1

Endpoint utilizzati:
- `GET /meetings?year=YYYY` - List of Grand Prix
- `GET /sessions?meeting_key=X` - List of sessions
- `GET /laps?session_key=X` - List of laps
- `GET /drivers?session_key=X` - Driver info
- `GET /car_data?session_key=X&driver_number=Y&date>A&date<B` - Telemetry data
- `GET /location?session_key=X&driver_number=Y&date>A&date<B` - Location data

**Base URL**: `https://api.openf1.org/v1`

Documentazione: https://openf1.org

## 📝 Note finali

- **Timezone**: Tutti i timestamp sono in UTC come fornito da OpenF1
- **Performance**: I dati vengono cacheati nei `dcc.Store` per ridurre le chiamate API
- **Debug**: Guarda i print nel terminale per tracciare le query API
- **License**: Rispetta i termini d'uso dell'API OpenF1

---

**Autore**: Leonardo Furio  
**Ultimo aggiornamento**: 29 novembre 2025  
**Versione**: 1.0 (modularizzata)
