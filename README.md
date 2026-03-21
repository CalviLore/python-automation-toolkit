# 🐍 python-automation-toolkit

Raccolta di script Python per l'automazione di operazioni su **PrestaShop**,
gestione di file **CSV**, traduzione automatica con **AI**, sincronizzazione
dati via **FTP** e analisi/segmentazione clienti.

Gli script sono stati sviluppati per automatizzare operazioni ripetitive
su un e-commerce nel settore **DPI (Dispositivi di Protezione Individuale)**,
riducendo il lavoro manuale e minimizzando gli errori umani.

---

## 📁 Struttura del progetto

```
python-automation-toolkit/
│
├── 01_translation_pipeline/     # Traduzione automatica contenuti con AI
├── 02_order_management/         # Gestione e trasformazione ordini
├── 03_prestashop_api/           # Aggiornamenti prezzi, posizioni e stato prodotti
├── 04_inventory_sync_ftp/       # Pulizia, validazione e gestione CSV contatti
├── 05_data_analysis/            # Segmentazione clienti per settore merceologico
└── 06_utilities/                # Strumenti di supporto (backup automatico)
```

| Cartella | Descrizione | Tecnologie |
|---|---|---|
| [01_translation_pipeline](./01_translation_pipeline/) | Traduzione H1, meta tag e descrizioni prodotto con DeepSeek AI | DeepSeek API, pandas |
| [02_order_management](./02_order_management/) | Download ordini, espansione KIT, generazione file cassa | MySQL, csv |
| [03_prestashop_api](./03_prestashop_api/) | Aggiornamento prezzi, posizioni, giacenze e stato prodotti | MySQL, pymysql, FTP |
| [04_inventory_sync_ftp](./04_inventory_sync_ftp/) | Pulizia indirizzi, deduplicazione, blacklist spedizioni | csv, re |
| [05_data_analysis](./05_data_analysis/) | Segmentazione email clienti per settore dominante di acquisto | csv |
| [06_utilities](./06_utilities/) | Backup automatico cartelle utente con barra di avanzamento | shutil, tqdm |

---

## 🛠️ Tecnologie utilizzate

- **Python 3.10+**
- **MySQL / PrestaShop DB** — aggiornamento diretto delle tabelle `ps_*`
- **DeepSeek AI** — traduzione e ottimizzazione SEO dei contenuti prodotto
- **FTP** — sincronizzazione automatica file giacenze da fornitore
- **CSV** — lettura, pulizia, validazione e trasformazione dati
- **ThreadPoolExecutor** — parallelizzazione chiamate API per performance

---

## ⚙️ Installazione

Clona il repository:

```bash
git clone https://github.com/tuo-utente/python-automation-toolkit.git
cd python-automation-toolkit
```

Ogni cartella ha il proprio `README.md` con le dipendenze specifiche.
Per installare tutte le dipendenze in una volta:

```bash
pip install pandas openai markdown markdownify mysql-connector-python pymysql ftputil requests prestapyt tqdm
```

---

## 🔐 Credenziali e sicurezza

Tutti gli script richiedono credenziali (DB, API key, FTP) che
**non devono mai essere committate** nel repository.

Sostituisci i placeholder nei file prima di usarli:

```python
# Database
DB_HOST     = "IL_TUO_HOST"
DB_USER     = "IL_TUO_UTENTE"
DB_PASSWORD = "LA_TUA_PASSWORD"
DB_NAME     = "IL_TUO_DATABASE"

# API DeepSeek (https://platform.deepseek.com)
DEEPSEEK_API_KEY = "LA_TUA_API_KEY"

# FTP
FTP_HOST     = "IL_TUO_HOST_FTP"
FTP_USER     = "IL_TUO_UTENTE_FTP"
FTP_PASSWORD = "LA_TUA_PASSWORD_FTP"
```

> 💡 Per una gestione sicura in produzione usa variabili d'ambiente
> o un file `.env` con la libreria `python-dotenv`:
> ```bash
> pip install python-dotenv
> ```

---

## 🔄 DRY_RUN — modalità simulazione

Gli script che modificano il database supportano la modalità **DRY_RUN**:
simulano le operazioni senza scrivere nulla, utile per verificare
i risultati prima di applicarli realmente.

```python
DRY_RUN = True    # Simula — nessuna modifica al DB
DRY_RUN = False   # Applica le modifiche reali
```

> ⚠️ Usa sempre `DRY_RUN = True` al primo utilizzo su dati reali.

---

## 📄 Licenza

Progetto personale — uso libero con attribuzione.
