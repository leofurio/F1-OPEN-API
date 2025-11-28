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

## Note importanti sul funzionamento dei grafici (mapping corrente)
Nel file `openf1_driver_comparison_meetings.py` il callback che aggiorna i grafici dichiara gli Output in questo ordine:
1. `track-graph`
2. `delta-graph`
3. `speed-graph`
4. `throttle-graph`
5. `brake-graph`
6. `gear-graph`

Tuttavia la funzione ritorna i grafici in questo ordine (variabili generate nello script):
- `speed_fig, track_fig, throttle_fig, brake_fig, gear_fig, delta_fig`

Quindi, con il codice così com'è, il contenuto dei grafici viene assegnato alle componenti Dash seguendo la posizione nella lista degli Output; il mapping effettivo diventa:

- track-graph ← speed_fig  
- delta-graph ← track_fig  
- speed-graph ← throttle_fig  
- throttle-graph ← brake_fig  
- brake-graph ← gear_fig  
- gear-graph ← delta_fig

Se preferisci mantenere l'ordine visivo attuale dei container Dash ma mostrare esplicitamente quale figura è generata da quale variabile, questo README documenta il comportamento corrente. Se vuoi invece correggere il comportamento così che ogni container mostri la figura con lo stesso nome logico, vedi la sezione Fix sotto.

## Fix consigliato (opzionale)
Per far corrispondere le figure alla dichiarazione degli Output (track → track_fig, delta → delta_fig, ...), modifica l'ultima riga del callback `update_graphs` in:

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