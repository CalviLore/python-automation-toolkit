# 🗄️ 03_database_sql — Operazioni SQL su PrestaShop

Questa cartella contiene script per aggiornamenti diretti al database
MySQL di PrestaShop: prezzi e posizioni prodotti.

Tutti gli script supportano la modalità **DRY_RUN** per simulare
le modifiche prima di applicarle realmente.

---

## 📁 Script

| Script | Input | Descrizione |
|---|---|---|
| `updatePrice.py` | `listino1.csv` + `cat74.csv` | Aggiorna i prezzi in `ps_product_shop` solo per i prodotti presenti in una categoria specifica |
| `updatePosition.py` | `cat74Dritto.csv` | Riordina i prodotti in categoria assegnando la posizione in base all'ordine del CSV |

---

## 🔄 Modalità DRY_RUN
```python
DRY_RUN = True    # Simula — mostra cosa verrebbe modificato senza toccare il DB
DRY_RUN = False   # Applica le modifiche reali
```

> ⚠️ Usa sempre `DRY_RUN = True` al primo utilizzo su dati reali.

---

## ⚙️ Configurazione

**updatePrice.py:**
```python
DB_HOST     = "IL_TUO_HOST"
DB_NAME     = "IL_TUO_DATABASE"
DB_USER     = "IL_TUO_UTENTE"
DB_PASSWORD = "LA_TUA_PASSWORD"
```

**updatePosition.py:**
```python
DB_CONFIG = {
    "host":     "IL_TUO_HOST",
    "user":     "IL_TUO_UTENTE",
    "password": "LA_TUA_PASSWORD",
    "database": "IL_TUO_DATABASE",
}

# Categorie da NON aggiornare (es. root, speciali)
ESCLUDI_CATEGORIE = [96, 337, 338, ...]
```

---

## 📄 Formato file CSV

**listino1.csv** — reference + prezzo:
```
reference;final_price
ABC123;29,90
```

**cat74.csv** — reference della categoria da filtrare:
```
reference
ABC123
DEF456
```

**cat74Dritto.csv** — reference nell'ordine desiderato:
```
ABC123
DEF456
GHI789
```

## 📦 Dipendenze
```bash
pip install mysql-connector-python pymysql
```
```
