# OpenF1 Driver Comparison Dashboard

Dashboard Dash per comparare la telemetria di due piloti su giri diversi usando l'API OpenF1.

## Descrizione breve
- Selezionare l'anno - Circuito → Session → Piloti → Giro 1 / Giro 2
- Visualizza: tracciato (location), delta time, velocità, throttle, brake, gear
- I dati vengono cacheati con `dcc.Store` per ridurre le chiamate API.

## Dipendenze
```bash
pip install requests pandas dash plotly
```

## Avvio (Windows)
```powershell
cd "c:\Users\l_o_w\F1 OPEN API"
python openf1_driver_comparison_meetings.py
# apri http://127.0.0.1:8050
```

## File principali
- `openf1_driver_comparison_meetings.py` — applicazione Dash + helper API
- `README.md` — questo file


```python
// filepath: c:\Users\l_o_w\F1 OPEN API\openf1_driver_comparison_meetings.py
# ...existing code...
# return must match Output order: track, delta, speed, throttle, brake, gear
return track_fig, delta_fig, speed_fig, throttle_fig, brake_fig, gear_fig
# ...existing code...
```

Alternativa: modifica la lista `Output(...)` per riflettere l'ordine delle variabili ritornate. Qualsiasi modifica richiede che la posizione degli elementi di `Output` corrisponda esattamente alla tupla restituita dalla funzione.
## Flusso rapido
1. Scegli anno/circuito/sessione  
2. Carica laps & drivers  
3. Seleziona driver1, lap1, driver2, lap2  
4. Visualizza 6 grafici: tracciato, delta, velocità, throttle, brake, gear

## Nota importante: mapping dei grafici (ordine Output)
Nel callback che aggiorna i grafici (`update_graphs`) gli Output sono dichiarati in questo ordine:

1. `track-graph`
2. `delta-graph`
3. `speed-graph`
4. `throttle-graph`
5. `brake-graph`
6. `gear-graph`

La funzione `update_graphs` è stata aggiornata per restituire le figure nello stesso ordine, quindi il mapping è ora coerente:

- track-graph ← track_fig  
- delta-graph ← delta_fig  
- speed-graph ← speed_fig  
- throttle-graph ← throttle_fig  
- brake-graph ← brake_fig  
- gear-graph ← gear_fig

Se in futuro modifichi l'ordine di ritorno delle figure, assicurati che la tupla restituita corrisponda esattamente all'ordine degli `Output`.

## Comportamento e dettagli tecnici
- Se `date_end` di un lap è `None`, lo script stima un intervallo (default: +2 minuti) per tentare di recuperare telemetria.
- Se le query con filtro `date>`/`date<` non restituiscono nulla, lo script può recuperare tutti i `car_data` per session+driver e filtrare lato client.
- I timestamp sono normalizzati in "tempo relativo" (t_rel_s) rispetto al primo record del dataset.

## Troubleshooting rapido
- "Nessun car_data trovato": verificare sessione/driver/giro e controllare i log (vengono stampati gli URL di query).
- `date_end` mancante: lo script stima 2 minuti se `date_end` è `None`.
- Callback errors sui duplicate outputs: assicurati che ogni id.prop compaia in una sola lista di Output o usa `allow_duplicate=True`.

## Note finali
- I timestamp sono gestiti in UTC così come forniti dall'API.
- Per debug, guarda i print nel terminale dove avvii lo script (VS Code integrated terminal consigliato).
- Se vuoi che aggiorni il README con più esempi o traduca sezioni in inglese, dimmi quali parti aggiungere.

- "Nessun car_data trovato": la API potrebbe non avere telemetria per quella sessione/giro; controlla i log/URL di query stampati nel terminale.
- Errori callback su output duplicati: assicurati che ogni id.prop compaia in una sola lista `Output` o usa `allow_duplicate=True` con attenzione.
- Grafici vuoti: verifica che session_key, driver e lap siano tutti selezionati e che `laps-store` contenga dati.

## Suggerimenti rapidi
- Per debug, guarda il terminale dove avvii lo script (VS Code integrated terminal consigliato).
- Per migliorare performance, estendi la cache o salva localmente i risultati API.

## License
Rispetta i termini d'uso dell'API OpenF1.

---  
Autore: Leonardo Furio  
Ultima modifica: 28 novembre 2025
