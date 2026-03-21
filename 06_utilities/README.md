# 🔧 05_utilities — Strumenti di Supporto

Questa cartella contiene strumenti generici di supporto e automazione
non legati direttamente a PrestaShop o alla gestione dei contatti.

---

## 📁 Script

| Script | Descrizione |
|---|---|
| `scriptbackup.py` | Backup automatico delle cartelle principali del PC |

---

## 📄 scriptbackup.py

Esegue una copia di sicurezza delle cartelle utente principali
(Scrivania, Documenti, Download, Musica, Foto, Video) in una cartella
di archivio con data e ora nel nome.

**Caratteristiche:**
- Mostra una barra di avanzamento durante la copia
- Funziona sia come script `.py` che come eseguibile `.exe` (PyInstaller)
- Preserva le date di modifica originali dei file (`shutil.copy2`)
- Salta i file in uso e li registra in un log leggibile
- Pensato per utenti non tecnici

**Output:**
```
<posizione_script>/
└── I miei Backup del PC/
    └── Copia del GG-MM-AAAA_ore_HH-MM/
        ├── Scrivania/
        ├── Documenti/
        ├── Download/
        ├── Musica/
        ├── Foto/
        └── Video/
```

---

## 📦 Dipendenze

```bash
pip install tqdm
```

> 💡 Per compilarlo in un `.exe` standalone (senza Python installato):
> ```bash
> pip install pyinstaller
> pyinstaller --onefile scriptbackup.py
> ```
