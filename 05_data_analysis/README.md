# 📊 05_data_analysis — Analisi Dati e Segmentazione Clienti

Questa cartella contiene script di analisi dati applicata all'e-commerce:
segmentazione clienti, classificazione comportamentale e preparazione
di dataset per campagne di marketing mirato.

---

## 📁 Script

| Script | Input | Output | Descrizione |
|---|---|---|---|
| `distinzione_settori.py` | `PRODOTTI-VARIANTI.csv` `PRODOTTI-CATEGORIE.csv` `ORDINE.csv` `CLIENTE.csv` | `SETTORE_X.csv` | Segmenta i clienti per settore merceologico in base agli acquisti |

---

## 🧠 Come funziona la segmentazione

Lo script applica una logica di **classificazione per settore dominante**:
```
Acquisti cliente → Categoria prodotto → Settore merceologico → Peso (quantità)
```

Ogni cliente viene assegnato al settore in cui ha acquistato **di più**
(in termini di quantità), non semplicemente al primo acquisto.

**Esempio:**
```
Cliente mario@esempio.it:
  - 3 paia di scarpe da cantiere  → Settore E (Edilizia)
  - 1 grembiule da cucina         → Settore A (Ristorazione)
  → Assegnato a: SETTORE_E.csv ✅
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

**PRODOTTI-VARIANTI.csv** — collega reference variante a ID prodotto:
```
reference;id_product
ABC123;456
```

**PRODOTTI-CATEGORIE.csv** — collega ID prodotto a ID categoria:
```
id_product;id_category
456;96
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

## ⚙️ Personalizzazione settori

Per aggiungere o modificare la mappatura categoria → settore,
modifica il dizionario `mappa_settori` in cima allo script:
```python
mappa_settori = {
    '96':  ['A'],   # ID categoria PrestaShop → Settore
    '337': ['A'],
    # aggiungi qui i tuoi ID...
}
```

---

## 📦 Dipendenze
```bash
# Nessuna dipendenza esterna — usa solo librerie standard Python
# csv
