# 📡 04_inventory_sync_ftp — Sincronizzazione Giacenze via FTP

Questa cartella contiene lo script per sincronizzare automaticamente
le giacenze di magazzino tra il fornitore e il negozio PrestaShop.

Lo script combina tre tecnologie in un unico flusso automatico:
**FTP** per scaricare il file dal fornitore, **CSV** per leggerlo
e **API REST PrestaShop** per aggiornare le quantità.

---

## 📁 Script

| Script | Input | Descrizione |
|---|---|---|
| `update_stock_ftp.py` | File FTP `giacenze.csv` | Scarica le giacenze via FTP e aggiorna le quantità su PrestaShop via API REST |

---

## 📋 Flusso
```
FTP Fornitore
     ↓
giacenze.csv (scaricato in locale)
     ↓
Lettura per codice / colore / taglia
     ↓
Costruzione referenza → <PREFISSO><codice>/<colore>/<taglia>
     ↓
Ricerca ID variante nel DB
     ↓
API REST PrestaShop → aggiornamento quantità
```

---

## ⚙️ Configurazione
```python
# Credenziali FTP fornitore
FTP_HOST     = "IL_TUO_HOST_FTP"
FTP_USER     = "IL_TUO_UTENTE_FTP"
FTP_PASSWORD = "LA_TUA_PASSWORD_FTP"

# API PrestaShop
SHOP_URL = "https://tuosito.com/api"
API_KEY  = "LA_TUA_API_KEY"

# Prefisso referenza articolo (es. se le tue referenze sono "ART001/NERO/M")
PREFISSO_REFERENZA = "IL_TUO_PREFISSO"
```

---

## 📄 Formato file CSV giacenze

Il file `giacenze.csv` (separatore `;`) deve avere questa struttura:
```
codice ; ... ; colore ; XS ; S ; M ; L ; XL ; XXL ; 3XL ; 4XL
ABC001 ; ... ; NERO   ;  2 ; 5 ; 3 ; 1 ;  0 ;   0 ;   0 ;   0
ABC001 ; ... ; BIANCO ;  0 ; 2 ; 4 ; 3 ;  1 ;   0 ;   0 ;   0
```

> Le prime 2 righe sono intestazioni e vengono saltate automaticamente.

---

## 📦 Dipendenze
```bash
pip install ftputil requests mysql-connector-python
```
