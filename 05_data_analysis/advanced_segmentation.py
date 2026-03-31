# ------------------------------------------------------------------------------
# Questo script segmenta i clienti per settore merceologico usando un approccio
# avanzato basato su K-Means clustering implementato da zero (senza librerie ML).
#
# Differenza rispetto a distinzione_settori.py:
#   distinzione_settori.py   → assegna ogni cliente al settore con più acquisti
#   advanced_segmentation.py → raggruppa i clienti in cluster comportamentali
#                              e permette l'assegnazione a PIÙ settori contemporaneamente
#
# Funzionamento:
#   1. Carica il catalogo prodotti e mappa ogni variante al suo settore
#   2. Per ogni ordine calcola il peso per settore (quantità acquistate)
#   3. Costruisce un vettore di profilo per ogni cliente (es. [A:3, B:0, C:1...])
#   4. Classifica ogni cliente nei settori che superano la soglia (SOGLIA_MULTI)
#   5. Raggruppa i clienti in N_CLUSTER cluster tramite K-Means
#   6. Genera i file CSV per settore + un report dettagliato con i cluster
#
# File di input:
#   - PRODOTTI-VARIANTI.csv   → reference + id_category
#   - PRODOTTI-CATEGORIE.csv  → reference + id_category (fonte alternativa)
#   - ORDINE.csv              → IdOrdine + CodiceVariante + Qta
#   - CLIENTE.csv             → Email + IdOrdine
#
# File di output:
#   - SETTORE_X.csv      → email clienti per ogni settore (A/B/C/E/F/G/ALTRO)
#   - CLUSTER_REPORT.csv → report dettagliato con cluster, settori e pesi per cliente
#
# 📁 Cartella: 05_data_analysis/
# 📦 Dipendenze: csv, math, random (solo librerie standard Python)
# ==============================================================================

import csv
import math
import random

# ─────────────────────────────────────────────
# CONFIGURAZIONE
# ─────────────────────────────────────────────

# Mappatura ID categoria PrestaShop → settore merceologico
# Aggiungere o modificare gli ID in base alla struttura del proprio negozio
mappa_settori = {
    # SETTORE A — RISTORAZIONE / HORECA
    '96': ['A'],
    '337': ['A'], '338': ['A'], '339': ['A'], '340': ['A'],

    # SETTORE B — ESTETICA / PULIZIE
    '99': ['B'], '102': ['B'],
    '349': ['B'], '350': ['B'], '351': ['B'], '352': ['B'],
    '361': ['B'], '362': ['B'], '363': ['B'], '364': ['B'],

    # SETTORE C — SANITARIO
    '100': ['C'],
    '353': ['C'], '354': ['C'], '355': ['C'], '356': ['C'],

    # SETTORE E — EDILIZIA / LOGISTICA
    '94': ['E'], '97': ['E'], '98': ['E'],
    '328': ['E'], '329': ['E'], '330': ['E'], '331': ['E'], '336': ['E'],
    '341': ['E'], '342': ['E'], '343': ['E'], '344': ['E'],

    # SETTORE F — INDUSTRIA
    '95': ['F'], '101': ['F'],
    '332': ['F'], '333': ['F'], '334': ['F'], '335': ['F'],

    # SETTORE G — AGRICOLTURA
    '345': ['G'], '346': ['G'], '347': ['G'], '348': ['G'],
}

SETTORI     = ['A', 'B', 'C', 'E', 'F', 'G']
SOGLIA_MULTI = 0.25   # Un settore viene assegnato se rappresenta almeno il 25%
                      # degli acquisti totali del cliente
N_CLUSTER   = 6       # Numero di cluster K-Means (uno per settore di default)
RANDOM_SEED = 42      # Seme per la riproducibilità dei risultati


# ─────────────────────────────────────────────
# FUNZIONI DI UTILITÀ
# ─────────────────────────────────────────────

def super_clean(val):
    """
    Pulisce un valore rimuovendo punti, virgole e spazi.
    Necessario perché PrestaShop può esportare gli ID in formati diversi.
    Es: "1.234" → "1234"
    """
    if not val:
        return ""
    return str(val).replace('.', '').replace(',', '').strip()


def normalizza(vettore):
    """
    Normalizza un vettore dividendo ogni valore per la somma totale.
    Converte le quantità assolute in percentuali (valori tra 0 e 1).
    Es: [3, 0, 1, 0, 0, 0] → [0.75, 0, 0.25, 0, 0, 0]
    """
    totale = sum(vettore)
    if totale == 0:
        return vettore[:]
    return [v / totale for v in vettore]


def distanza_euclidea(a, b):
    """
    Calcola la distanza euclidea tra due vettori.
    Usata nel K-Means per trovare il centroide più vicino a ogni cliente.
    """
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def intestazioni(filepath):
    """Stampa le colonne di un file CSV per debug e verifica."""
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            cols = csv.DictReader(f, delimiter=';').fieldnames or []
            print(f"  [DEBUG] {filepath} → colonne: {cols}")
    except FileNotFoundError:
        print(f"  [WARN] {filepath} non trovato")


# ─────────────────────────────────────────────
# FASE 1 — Caricamento prodotti
# ─────────────────────────────────────────────

print("📂 Fase 1: Caricamento database prodotti...")
intestazioni('PRODOTTI-VARIANTI.csv')
intestazioni('PRODOTTI-CATEGORIE.csv')
intestazioni('ORDINE.csv')
intestazioni('CLIENTE.csv')

# Dizionario: reference variante → set di categorie mappate
# Un prodotto può appartenere a più categorie, teniamo solo quelle mappate ai settori
variante_a_cats = {}

def carica_cat_file(filepath):
    """
    Legge un file CSV e popola variante_a_cats con le categorie mappate.
    Ignora le categorie generiche non presenti in mappa_settori.
    """
    trovate = 0
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f, delimiter=';'):
                ref = super_clean(r.get('reference'))
                cat = super_clean(r.get('id_category'))
                if ref and cat and cat in mappa_settori:
                    variante_a_cats.setdefault(ref, set()).add(cat)
                    trovate += 1
        print(f"  {filepath}: {trovate} righe con categoria mappata")
    except FileNotFoundError:
        print(f"  [WARN] {filepath} non trovato")

carica_cat_file('PRODOTTI-CATEGORIE.csv')
carica_cat_file('PRODOTTI-VARIANTI.csv')
print(f"  Varianti con almeno un settore noto: {len(variante_a_cats)}")


# ─────────────────────────────────────────────
# FASE 2 — Analisi ordini → peso per settore
# ─────────────────────────────────────────────

print("\n🔍 Fase 2: Analisi acquisti per ordine...")

# Dizionario: id_ordine → { settore: quantità_totale }
ordini_pesi = {}
righe_tot = righe_match = 0

with open('ORDINE.csv', mode='r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter=';'):
        righe_tot += 1
        id_ord  = super_clean(r['IdOrdine'])
        cod_var = super_clean(r['CodiceVariante'])
        qta     = int(str(r['Qta']).replace('.', '').replace(',', '')) if r.get('Qta') else 1

        # Recupera le categorie associate alla variante
        cats = variante_a_cats.get(cod_var, set())
        if cats:
            righe_match += 1
        else:
            cats = {'Sconosciuto'}   # Variante non classificata

        ordini_pesi.setdefault(id_ord, {})
        for cat in cats:
            for s in mappa_settori.get(cat, []):
                ordini_pesi[id_ord][s] = ordini_pesi[id_ord].get(s, 0) + qta

print(f"  Righe: {righe_tot} | Riconosciute: {righe_match} | Ordini unici: {len(ordini_pesi)}")


# ─────────────────────────────────────────────
# FASE 3 — Aggregazione per email
# ─────────────────────────────────────────────

print("\n👥 Fase 3: Costruzione vettori profilo cliente...")

# Dizionario: email → { settore: quantità_totale su tutti gli ordini }
clienti_raw = {}

with open('CLIENTE.csv', mode='r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter=';'):
        email  = r['Email'].strip().lower()
        id_ord = super_clean(r['IdOrdine'])
        if not email:
            continue
        clienti_raw.setdefault(email, {})
        if id_ord in ordini_pesi:
            for s, qta in ordini_pesi[id_ord].items():
                clienti_raw[email][s] = clienti_raw[email].get(s, 0) + qta

clienti_con_acquisti = sum(1 for v in clienti_raw.values() if any(v.values()))
print(f"  Email totali: {len(clienti_raw)} | Con acquisto mappato: {clienti_con_acquisti}")

# Costruisce la lista di email e la matrice di vettori profilo
emails  = list(clienti_raw.keys())
vettori = [[clienti_raw[e].get(s, 0) for s in SETTORI] for e in emails]


# ─────────────────────────────────────────────
# FASE 4 — Classificazione multi-settore
# ─────────────────────────────────────────────

print("\n🏷️  Fase 4: Classificazione multi-settore con soglia relativa...")

def settori_cliente(vec):
    """
    Restituisce la lista dei settori che superano la SOGLIA_MULTI.
    Un cliente può essere assegnato a più settori contemporaneamente.

    Es: vettore [10, 0, 3, 0, 0, 0] con soglia 0.25:
        A = 10/13 = 77% ✅  C = 3/13 = 23% ❌
        → assegnato solo a [A]
    """
    totale = sum(vec)
    if totale == 0:
        return []
    return [SETTORI[i] for i, v in enumerate(vec) if v / totale >= SOGLIA_MULTI]

assegnazioni_multi = [settori_cliente(v) for v in vettori]


# ─────────────────────────────────────────────
# FASE 5 — K-Means Clustering
# ─────────────────────────────────────────────

print(f"\n🔬 Fase 5: K-Means clustering con K={N_CLUSTER}...")

vettori_norm = [normalizza(v) for v in vettori]
idx_attivi   = [i for i, v in enumerate(vettori_norm) if sum(v) > 0]

def kmeans(dati, k, seed=42, max_iter=100):
    """
    Implementazione K-Means da zero senza librerie ML esterne.

    Algoritmo:
      1. Sceglie K centroidi casuali tra i dati
      2. Assegna ogni punto al centroide più vicino (distanza euclidea)
      3. Ricalcola i centroidi come media dei punti del cluster
      4. Ripete finché le assegnazioni non cambiano (o raggiunge max_iter)

    Args:
        dati (list):    lista di vettori normalizzati
        k (int):        numero di cluster
        seed (int):     seme per riproducibilità
        max_iter (int): numero massimo di iterazioni

    Returns:
        tuple: (assegnazioni, centroidi)
    """
    random.seed(seed)
    centroidi    = [dati[i][:] for i in random.sample(range(len(dati)), k)]
    assegnazione = [0] * len(dati)

    for _ in range(max_iter):
        # Assegna ogni punto al centroide più vicino
        nuova_ass = [
            min(range(k), key=lambda j: distanza_euclidea(p, centroidi[j]))
            for p in dati
        ]
        if nuova_ass == assegnazione:
            break   # Convergenza raggiunta
        assegnazione = nuova_ass

        # Ricalcola i centroidi come media dei punti nel cluster
        for j in range(k):
            pts = [dati[i] for i, a in enumerate(assegnazione) if a == j]
            if pts:
                centroidi[j] = [
                    sum(p[d] for p in pts) / len(pts)
                    for d in range(len(dati[0]))
                ]

    return assegnazione, centroidi

dati_attivi = [vettori_norm[i] for i in idx_attivi]
k_effettivo = min(N_CLUSTER, len(dati_attivi))

if k_effettivo == 0:
    print("  ⚠️  Nessun cliente attivo, clustering saltato.")
    labels_attivi, centroidi = [], []
else:
    if k_effettivo < N_CLUSTER:
        print(f"  [WARN] Solo {len(dati_attivi)} clienti attivi — K ridotto a {k_effettivo}")
    labels_attivi, centroidi = kmeans(dati_attivi, k_effettivo, seed=RANDOM_SEED)

cluster_map = {idx: labels_attivi[pos] for pos, idx in enumerate(idx_attivi)}


# ─────────────────────────────────────────────
# FASE 6 — Generazione CSV settoriali
# ─────────────────────────────────────────────

print("\n💾 Fase 6: Generazione file CSV settoriali...")

output_data = {l: [] for l in SETTORI}
output_data['ALTRO'] = []

for i, email in enumerate(emails):
    settori_ass = assegnazioni_multi[i]
    if not settori_ass:
        output_data['ALTRO'].append(email)
    else:
        for s in settori_ass:
            if s in output_data:
                output_data[s].append(email)   # Un cliente può essere in più settori

for l, lista in output_data.items():
    lista_unica = sorted(set(lista))            # Rimuove eventuali duplicati
    filename    = f'SETTORE_{l}.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Email'])
        for mail in lista_unica:
            writer.writerow([mail])
    print(f"  ✅ {filename}: {len(lista_unica)} email")


# ─────────────────────────────────────────────
# FASE 7 — Report dettagliato
# ─────────────────────────────────────────────

print("\n📊 Fase 7: Generazione CLUSTER_REPORT.csv...")

def descrivi_cluster(centroide):
    """Restituisce una descrizione leggibile del cluster in base al settore prevalente."""
    idx_max = centroide.index(max(centroide))
    return f"Prevalente {SETTORI[idx_max]}" if max(centroide) > 0 else "Misto"

with open('CLUSTER_REPORT.csv', mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(
        ['Email', 'Cluster', 'Settori_Assegnati', 'Settore_Dominante', 'Tot_Acquisti']
        + [f'Peso_{s}' for s in SETTORI]
        + [f'%_{s}' for s in SETTORI]
    )
    for i, email in enumerate(emails):
        vec         = vettori[i]
        vec_norm    = vettori_norm[i]
        totale      = sum(vec)
        cluster     = cluster_map.get(i, -1)
        settori_ass = assegnazioni_multi[i]
        settore_dom = SETTORI[vec.index(max(vec))] if totale > 0 else 'N/A'

        writer.writerow(
            [email,
             cluster if cluster >= 0 else 'N/A',
             '|'.join(settori_ass) if settori_ass else 'ALTRO',
             settore_dom,
             int(totale)]
            + [int(v) for v in vec]
            + [f"{v * 100:.1f}" for v in vec_norm]
        )

print("  ✅ CLUSTER_REPORT.csv generato")


# ─────────────────────────────────────────────
# RIEPILOGO FINALE
# ─────────────────────────────────────────────

print("\n── Riepilogo cluster ──────────────────────")
conteggi = {}
for i in idx_attivi:
    c = cluster_map[i]
    conteggi[c] = conteggi.get(c, 0) + 1

for c in sorted(conteggi):
    profilo = ' | '.join(
        f"{SETTORI[j]}:{centroidi[c][j] * 100:.0f}%"
        for j in range(len(SETTORI))
        if centroidi[c][j] > 0.05
    )
    print(f"  Cluster {c} ({descrivi_cluster(centroidi[c])}): {conteggi[c]} clienti — {profilo}")

print(f"  Senza acquisti noti: {len(output_data['ALTRO'])} clienti → SETTORE_ALTRO.csv")
print("\n🎉 Missione Compiuta!")
for l in list(SETTORI) + ['ALTRO']:
    print(f"  → SETTORE_{l}.csv")
print("  → CLUSTER_REPORT.csv")
