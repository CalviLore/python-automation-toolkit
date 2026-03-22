# 🛒 03_prestashop_api — Operazioni su PrestaShop

Questa cartella contiene gli script per aggiornare direttamente il database
PrestaShop: prezzi, posizioni, stato prodotti, giacenze e buoni sconto.

Tutti gli script supportano la modalità **DRY_RUN** (simulazione) per
verificare le modifiche prima di applicarle realmente.

---

## 📁 Script

| Script | Input | Descrizione |
|---|---|---|
| `Buonisconto.py` | `giftcard.csv` | Crea buoni sconto (cart_rule) su PrestaShop via API |
| `fixdb.py` | `cateprodmiss.csv` | Rimuove associazioni categoria-prodotto orfane dal DB |
| `updatePrice.py` | `fixcat.csv` | Aggiorna prezzi su `ps_product_shop` per tutti i prodotti |
| `updateDescription.py` | `listino1.csv` + `cat74.csv` | Aggiorna prezzi solo per i prodotti di una categoria specifica |
| `updatePosition.py` | `cat74Dritto.csv` | Riordina i prodotti in categoria in base all'ordine del CSV |
| `updateError.py` | `activeprodu.csv` | Attiva o disattiva prodotti (campo `active`) in massa |
| `changequantityjrc.py` | Via FTP + `giacenze_jrc.csv` | Scarica le giacenze via FTP e aggiorna le quantità via API |

---

## ⚙️ Configurazione

```python
# Credenziali database
DB_HOST     = "IL_TUO_HOST"
DB_USER     = "IL_TUO_UTENTE"
DB_PASSWORD = "LA_TUA_PASSWORD"
DB_NAME     = "IL_TUO_DATABASE"

# Modalità simulazione (consigliato prima di ogni esecuzione reale)
DRY_RUN = True   # Cambia in False per applicare le modifiche
```

---

## 🔄 Modalità DRY_RUN

Tutti gli script con DRY_RUN mostrano cosa verrebbe modificato **senza toccare il database**. Usala sempre al primo utilizzo:

```
DRY_RUN = True   → simula e mostra il log
DRY_RUN = False  → applica le modifiche reali
```

---

## 📦 Dipendenze

```bash
pip install mysql-connector-python pymysql prestapyt ftputil requests
```
