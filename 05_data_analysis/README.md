# 📊 05_data_analysis — Analisi Dati e Segmentazione Clienti

Questa cartella contiene script di analisi dati applicata all'e-commerce:
segmentazione clienti, classificazione comportamentale e preparazione
di dataset per campagne di marketing mirato.

---

## 📁 Script

| Script | Input | Output | Descrizione |
|---|---|---|---|
| `distinzione_settori.py` | `PRODOTTI-VARIANTI.csv` `PRODOTTI-CATEGORIE.csv` `ORDINE.csv` `CLIENTE.csv` | `SETTORE_X.csv` | Segmentazione semplice — assegna ogni cliente al settore con più acquisti |
| `advanced_segmentation.py` | `PRODOTTI-VARIANTI.csv` `PRODOTTI-CATEGORIE.csv` `ORDINE.csv` `CLIENTE.csv` | `SETTORE_X.csv` + `CLUSTER_REPORT.csv` | Segmentazione avanzata — K-Means clustering + assegnazione multi-settore |

---

## 🧠 Due approcci a confronto

### 📌 distinzione_settori.py — Approccio semplice
Ogni cliente viene assegnato al **settore dominante**, cioè quello con
il maggior numero di acquisti. Veloce e diretto.
```
Acquisti cliente → Categoria prodotto → Settore → Settore con più acquisti → 1 file CSV
```

**Esempio:**
```
Cliente mario@esempio.it:
  - 3 paia di scarpe da cantiere  → Settore E (Edilizia)
  - 1 grembiule da cucina         → Settore A (Ristorazione)
  → Assegnato a: SETTORE_E.csv ✅
```

---

### 🔬 advanced_segmentation.py — Approccio avanzato
Ogni cliente viene **profilato** con un vettore di acquisti per settore,
può essere assegnato a **più settori contemporaneamente** (se supera la
soglia del 25%) e viene raggruppato in **cluster comportamentali** tramite
K-Means implementato da zero.
```
Acquisti cliente → Vettore profilo → Soglia multi-settore → K-Means → CSV + Report
```

**Esempio:**
```
Cliente mario@esempio.it:
  - Settore E: 60% acquisti → ✅ supera soglia 25%
  - Settore A: 30% acquisti → ✅ supera soglia 25%
  - Settore C: 10% acquisti → ❌ sotto soglia
  → Assegnato a: SETTORE_E.csv + SETTORE_A.csv
  → Cluster 2 (Prevalente E) nel CLUSTER_REPORT.csv
```

---

## 🏭 Settori supportati

| Codice | Settore | Uso tipico |
|---|---|---|
| `A` | Ristorazione / HoReCa | Grembiuli, divise cucina, calzature food |
| `B` | Estetica / Pulizie | Divise estetiste, abbigliamento pulizie |
| `C` | Sanitario | Camici, DPI medicali |
| `E` | Edilizia / Logistica | Scarpe antinfortunistiche, tute da lavoro |
| `F` | Industria | DPI industriali, guanti, occhiali |
| `G` | Agricoltura | Abbigliamento e protezioni per il campo |
| `ALTRO` | Non classificato | Clienti con acquisti non mappati |

---

## 📋 Formato file di input

Entrambi gli script usano gli stessi 4 file di input:

**PRODOTTI-VARIANTI.csv** — collega reference variante a ID categoria:
```
reference;id_category
ABC123;96
```

**PRODOTTI-CATEGORIE.csv** — fonte alternativa per la stessa mappatura:
```
reference;id_category
ABC123;96
```

**ORDINE.csv** — dettaglio righe ordine:
```
IdOrdine;CodiceVariante;Qta
1001;ABC123;2
```

**CLIENTE.csv** — collega email cliente a ID ordine:
```
Email;IdOrdine
mario@esempio.it;1001
```

---

## ⚙️ Personalizzazione

**Mappatura categoria → settore** (uguale in entrambi gli script):
```python
mappa_settori = {
    '96':  ['A'],   # ID categoria PrestaShop → Settore
    '337': ['A'],
    # aggiungi qui i tuoi ID...
}
```

**Parametri avanzati** (solo `advanced_segmentation.py`):
```python
SOGLIA_MULTI = 0.25   # Soglia minima per assegnare un settore (25%)
N_CLUSTER    = 6      # Numero di cluster K-Means
RANDOM_SEED  = 42     # Seme per risultati riproducibili
```

---

## 📦 Dipendenze
```bash
# Nessuna dipendenza esterna — usa solo librerie standard Python
# csv, math, random
```
