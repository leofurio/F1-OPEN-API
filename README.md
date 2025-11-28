# OpenF1 Driver Comparison Dashboard

Dashboard Dash per comparare la telemetria di due piloti su giri diversi usando l'API OpenF1.

## Descrizione breve
- Seleziona Meeting → Session → Piloti → Giro 1 / Giro 2
- Visualizza: tracciato (location), delta time, velocità, throttle, brake, gear
- I dati vengono cacheati con `dcc.Store` per ridurre le chiamate API.

## Dipendenze
```bash
pip install requests pandas dash plotly numpy
```

## Avvio
```bash
cd "c:\F1 OPEN API"
python openf1_driver_comparison_meetings.py
# poi aprire http://127.0.0.1:8050
```

## File principali
- `openf1_driver_comparison_meetings.py` — applicazione Dash e helper per chiamate API
- `README.md` — questo file


```python
// filepath: c:\Users\l_o_w\F1 OPEN API\openf1_driver_comparison_meetings.py
# ...existing code...
# return must match Output order: track, delta, speed, throttle, brake, gear
return track_fig, delta_fig, speed_fig, throttle_fig, brake_fig, gear_fig
# ...existing code...
```

Alternativa: modifica la lista `Output(...)` per riflettere l'ordine delle variabili ritornate. Qualsiasi modifica richiede che la posizione degli elementi di `Output` corrisponda esattamente alla tupla restituita dalla funzione.

## Troubleshooting rapido
- "Nessun car_data trovato": verificare sessione/driver/giro e controllare i log (vengono stampati gli URL di query).
- `date_end` mancante: lo script stima 2 minuti se `date_end` è `None`.
- Callback errors sui duplicate outputs: assicurati che ogni id.prop compaia in una sola lista di Output o usa `allow_duplicate=True`.

## Note finali
- I timestamp sono gestiti in UTC così come forniti dall'API.
- Per debug, guarda i print nel terminale dove avvii lo script (VS Code integrated terminal consigliato).
- Se vuoi che aggiorni il README con più esempi o traduca sezioni in inglese, dimmi quali parti aggiungere.
