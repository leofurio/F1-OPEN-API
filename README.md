# OpenF1 Driver Comparison Dashboard

Una dashboard interattiva Dash per comparare la telemetria di due piloti di Formula 1 su giri diversi, utilizzando l'API OpenF1.

## 📋 Descrizione

Questo progetto permette di:
- Selezionare un anno e un Gran Premio (Meeting)
- Scegliere una sessione (FP1, FP2, Qualifiche, Gara, Sprint)
- Comparare due piloti su giri **diversi**
- Visualizzare 4 grafici con telemetria in tempo reale:
  - **Velocità** vs tempo relativo
  - **Throttle** (acceleratore) vs tempo relativo
  - **Brake** (freno) vs tempo relativo
  - **Marcia (Gear)** vs tempo relativo

## 🚀 Flusso dell'applicazione

```
Seleziona Anno
    ↓
Carica Meetings per quell'anno
    ↓
Seleziona Meeting (Gran Premio)
    ↓
Carica Sessions per quel meeting
    ↓
Seleziona Session (FP1, Qualifiche, Gara, ecc.)
    ↓
Carica Laps e Drivers per quella sessione
    ↓
Seleziona Pilota 1 e Pilota 2
    ↓
Seleziona Giro 1 e Giro 2 (indipendenti!)
    ↓
Visualizza 4 grafici comparativi
```

## 📦 Dipendenze

```bash
pip install requests pandas dash plotly
```

## 🔧 Installazione e avvio

1. **Clona il repository** (o salva il file)
   ```bash
   cd "c:\Users\l_o_w\F1 OPEN API"
   ```

2. **Installa le dipendenze**
   ```bash
   pip install -r requirements.txt
   ```
   O manualmente:
   ```bash
   pip install requests pandas dash plotly
   ```

3. **Avvia l'app**
   ```bash
   python openf1_driver_comparison_meetings.py
   ```

4. **Apri il browser**
   - Naviga a `http://127.0.0.1:8050`

## 📊 Funzionalità principali

### 1. **Selezione dinamica con Dropdown**
- Ogni dropdown si aggiorna in base alle scelte precedenti
- I giri disponibili cambiano quando selezioni un pilota diverso
- Non devi ricaricare manualmente i dati

### 2. **Comparazione di giri indipendenti**
- Puoi comparare il giro 45 del Pilota 1 con il giro 50 del Pilota 2
- Ogni pilota ha il suo dropdown di selezione del giro
- I grafici mostrano sempre entrambi i dataset sovrapposti

### 3. **Telemetria multicanale**
- **Velocità (km/h)**: trend di velocità nel corso del giro
- **Throttle (%)**: utilizzo dell'acceleratore
- **Brake**: pressione/valore del freno
- **Marcia (Gear)**: sequenza di marce utilizzate

### 4. **Store locale (cache)**
- `meetings-store`: cache dei meeting caricati
- `sessions-store`: cache delle sessioni
- `laps-store`: cache dei giri (usato dai callback)
- `drivers-store`: cache dei piloti (nomi, team)

## 🏗️ Struttura del codice

### Helper API (`fetch_*` functions)

| Funzione | Descrizione |
|----------|------------|
| `fetch_meetings(year)` | Recupera i Gran Premi per un anno |
| `fetch_sessions(meeting_key)` | Recupera le sessioni per un meeting |
| `fetch_laps(session_key)` | Recupera i giri per una sessione |
| `fetch_drivers(session_key)` | Recupera i piloti e i loro dati |
| `fetch_car_data_for_lap()` | Recupera la telemetria per un giro specifico |

### Callbacks Dash

| Callback | Trigger | Output |
|----------|---------|--------|
| `load_meetings()` | Click bottone "Carica meetings" | Popola dropdown meeting |
| `load_sessions()` | Cambio meeting | Popola dropdown session |
| `load_laps_and_drivers()` | Cambio session | Popola dropdown piloti |
| `update_lap_dropdowns()` | Cambio pilota 1 o 2 | Popola dropdown giri indipendenti |
| `update_graphs()` | Cambio giro 1, giro 2 o pilota | Aggiorna i 4 grafici |

## 🔗 API OpenF1

Endpoint utilizzati:
- `GET /meetings?year=2024` - List of Grand Prix
- `GET /sessions?meeting_key=X` - List of sessions
- `GET /laps?session_key=X` - List of laps
- `GET /drivers?session_key=X` - Driver info
- `GET /car_data?session_key=X&driver_number=Y&date>A&date<B` - Telemetry data

**Base URL**: `https://api.openf1.org/v1`

## ⚙️ Dettagli tecnici

### Gestione del timestamp mancante
L'API OpenF1 a volte non fornisce `date_end` per i giri.  
**Soluzione**: Se `date_end` è `None`, si stima automaticamente un intervallo di **2 minuti** (durata tipica di un giro F1).

```python
if not date_end:
    from datetime import timedelta
    start_dt = pd.to_datetime(date_start)
    date_end = (start_dt + timedelta(minutes=2)).isoformat()
```

### Normalizzazione del tempo relativo
I dati grezzi hanno timestamp assoluti. Vengono normalizzati a "tempo relativo da inizio giro" (in secondi):

```python
t0 = df["date"].min()
df["t_rel_s"] = (df["date"] - t0).dt.total_seconds()
```

Così i grafici iniziano sempre da `t=0` indipendentemente dall'orario reale.

## 📈 Esempi di utilizzo

### Comparare due giri di Max Verstappen
1. Seleziona: 2024 → Monaco → Qualifiche
2. Pilota 1: Max Verstappen (Car 1) → Giro 14
3. Pilota 2: Max Verstappen (Car 1) → Giro 16
4. Osserva come varia la velocità max, throttle, frenata tra due tentativi di qualifica

### Comparare due piloti su giri diversi
1. Seleziona: 2024 → Monza → Gara
2. Pilota 1: Charles Leclerc → Giro 35
3. Pilota 2: Carlos Sainz → Giro 42
4. Vedi le differenze nel passo gara e nella gestione dei freni

## 🐛 Troubleshooting

| Problema | Soluzione |
|----------|----------|
| "Nessun car_data trovato" | L'API OpenF1 potrebbe non avere dati per quella sessione |
| Dropdown vuoti dopo selezione | Aspetta il caricamento della pagina, a volte ci vogliono secondi |
| Errore timeout | La connessione API è lenta, prova di nuovo o usa una sessione più recente |
| Grafici non si aggiornano | Verifica che session, piloti e giri siano tutti selezionati |

## 📝 Note

- **Intervallo di tempo**: L'app usa il `session_key` per identificare univocamente una sessione F1
- **Nomi piloti**: Vengono recuperati dall'endpoint `/drivers` con nome completo e team
- **Performance**: I dati vengono cacheati nei `dcc.Store` per ridurre le chiamate API
- **Timezone**: Tutti i timestamp sono in UTC (come fornito da OpenF1)

## 🎨 Personalizzazioni possibili

- Aggiungere più grafici (RPM, DRS, ecc.)
- Importare i dati in CSV per analisi offline
- Aggiungere filtri per circuito specifico
- Calcolare delta time tra i due giri

## 📄 License

Questo progetto utilizza l'API OpenF1, che è open source. Rispetta i termini di utilizzo.

---

**Autore**: Leonardo Furio
**Ultima modifica**: 28 novembre 2025