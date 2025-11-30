# OpenF1 Driver Comparison Dashboard

Dashboard Dash per comparare la telemetria di due piloti su giri diversi usando l'API OpenF1.

> ⚠️ Nota: durante le sessioni attive (FP, Qualifiche, Gara) l'API OpenF1 nasconde i dati live: servirebbe un abbonamento per vederli in tempo reale. I dati tornano disponibili a sessione conclusa.

## Cosa fa
- Flusso: Anno → Circuito → Sessione → Pilota/Giro 1 e 2 → Grafici.
- Sei grafici sincronizzati: Tracciato, Delta tempo, Velocità, Throttle, Brake, Marcia.
- **Click** sui grafici di telemetria aggiunge linea verticale, aggiorna tutti i grafici e piazza un marker sul tracciato (tempo mostrato come hh:mm:ss.sss).
- Ordine grafici personalizzabile (radio + pulsanti su/giu/reset) con rendering dinamico.
- Cache locale delle risposte API; pulsante per svuotare la cache con stato mostrato.
- Spinner di caricamento sui grafici durante gli update.

## Dipendenze
```bash
pip install -r requirements.txt
# oppure
pip install requests pandas dash plotly numpy
```

## Avvio rapido (Windows)
```powershell
cd "c:\F1 OPEN API"
python main.py
# poi apri http://127.0.0.1:8050
```

## Struttura
```
main.py                 # Entry point Dash
config.py               # Costanti (colori, base URL, timeout)
api/openf1.py           # Wrapper API OpenF1
components/layout.py    # Layout HTML e componenti (store, controlli, grafici)
callbacks/meetings.py   # Caricamento circuiti e sessioni
callbacks/drivers.py    # Caricamento piloti e giri; sync dropdown
callbacks/graphs.py     # Genera 6 grafici + selezione tempo via hover/click
callbacks/cache.py      # Stato e reset cache
callbacks/graph_order.py# Gestione ordine grafici e rendering dinamico
utils/telemetry.py      # Calcolo delta, durata, formattazione
utils/cache.py          # Cache file-based JSON
utils/graph_order.py    # Ordine grafici e titoli
```

## Come usarla
1) Inserisci l'anno e clicca "Carica Circuiti".  
2) Scegli circuito e sessione.  
3) Seleziona Pilota 1 e 2 e i rispettivi giri.  
4) Click su speed/throttle/brake/gear per fissare un tempo: si aggiorna la linea verticale, compaiono i marker sul tracciato e gli altri grafici si allineano (tempo formattato hh:mm:ss.sss).  
5) Cambia l'ordine dei grafici con il radio e i pulsanti su/giu/reset; la pagina si aggiorna istantaneamente.  
6) Pulisci la cache con il pulsante dedicato se vuoi ricaricare dati freschi.

## Grafici (titolo legenda)
- Tracciato · P1 vs P2  
- Delta tempo · P2 vs P1  
- Velocità · …  
- Throttle · …  
- Brake · …  
- Marcia · …

## Note tecniche
- Dati normalizzati con tempo relativo da inizio giro (`t_rel_s`).
- Delta tempo interpolato a 200 punti per giri di durata diversa.
- Se `date_end` manca viene stimata (fallback 2 minuti) per calcolare la durata giro.
- I `dcc.Store` mantengono state e cache locale; `utils/cache.py` gestisce pulizia e dimensione.
- Spinner via `dcc.Loading` su container e singoli grafici.

## Troubleshooting
- Nessun car_data trovato: l'API non ha telemetria per quella sessione/giro; prova un'altra sessione.
- Dropdown vuoti/lenti: attendi qualche secondo; controlla la connessione.
- Marker non appare: il click/hover deve avvenire su speed/throttle/brake/gear, non sul tracciato.
- Errore “nonexistent object … speed-graph”: usa la versione con seed grafici nel layout.

---
Autore: Leonardo Furio  
Ultimo aggiornamento: 30 novembre 2025  
Versione: 1.2 (spinner e sincronizzazione click)
