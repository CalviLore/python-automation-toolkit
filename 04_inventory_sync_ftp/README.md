# 📋 04_inventory_sync_ftp — Pulizia e Gestione Contatti CSV

Questa cartella contiene gli script per pulire, validare, deduplicare
e filtrare file CSV di contatti aziendali, usati per le spedizioni
di cataloghi e comunicazioni commerciali.

---

## 📋 Flusso consigliato

```
1. distinzione iva e non.py   →  Pulisce e separa aziende da privati
2. removeDuplicate.py         →  Rimuove i duplicati dai file generati
3. RemovefixIndirizzi.py      →  Valida e corregge gli indirizzi
4. creazioneblacklist.py      →  Genera la blacklist per le spedizioni
```

---

## 📁 Script

| Script | Input | Output | Descrizione |
|---|---|---|---|
| `distinzione iva e non.py` | `lista_nominativi.csv` + `INDIRIZZI DA SPEDIRE.csv` | `estrapolato_aziende.csv` + `estrapolato_privati.csv` | Pulisce e separa i contatti in base alla presenza della P.IVA |
| `removeDuplicate.py` | `estrapolato_aziende.csv` + `estrapolato_privati.csv` | `*_univoco.csv` | Rimuove i duplicati confrontando ragione sociale + indirizzo + CAP |
| `RemovefixIndirizzi.py` | `lista_nominativi.csv` | `estrapolato.csv` + `errori.csv` | Valida CAP, provincia e indirizzo — separa i record validi dagli errori |
| `creazioneblacklist.py` | `estrapolato_aziende.csv` + file indirizzi da escludere | `blacklist.csv` | Genera la lista delle aziende da escludere dalle spedizioni |

---

## 🧹 Cosa viene pulito

Gli script gestiscono automaticamente:
- Numeri di telefono nel testo (TEL, FAX, CELL)
- Caratteri speciali e virgolette
- CAP non validi (tenta correzione automatica dall'indirizzo)
- Province non valide (tenta correzione dalla città)
- Duplicati (stessa ragione sociale + indirizzo + CAP)
- P.IVA nascosta nel testo libero

---

## 📦 Dipendenze

```bash
# Nessuna dipendenza esterna — usa solo librerie standard Python
# csv, re, os
```
