# Questo script analizza gli ordini dei clienti e assegna ogni email
# al settore merceologico prevalente, in base ai prodotti acquistati.
#
# Caso d'uso:
#   Permette di segmentare la lista clienti per settore (Ristorazione,
#   Estetica, Sanitario, Edilizia, ecc.) per inviare comunicazioni
#   commerciali mirate solo ai clienti del settore interessato.
#
# Funzionamento:
#   1. Carica il catalogo prodotti e le loro categorie da CSV
#   2. Per ogni ordine calcola i settori dei prodotti acquistati
#   3. Per ogni cliente somma le quantità acquistate per settore
#   4. Assegna ogni email al settore con più acquisti (settore dominante)
#   5. Genera un file CSV separato per ogni settore
#
# File di input:
#   - PRODOTTI-VARIANTI.csv  → reference + id_product
#   - PRODOTTI-CATEGORIE.csv → id_product + id_category
#   - ORDINE.csv             → IdOrdine + CodiceVariante + Qta
#   - CLIENTE.csv            → Email + IdOrdine
#
# File di output:
#   - SETTORE_A.csv → email clienti Ristorazione/HoReCa
#   - SETTORE_B.csv → email clienti Estetica/Pulizie
#   - SETTORE_C.csv → email clienti Sanitario
#   - SETTORE_E.csv → email clienti Edilizia/Logistica
#   - SETTORE_F.csv → email clienti Industria
#   - SETTORE_G.csv → email clienti Agricoltura
#   - SETTORE_ALTRO.csv → email clienti non classificabili
#
# 📦 Dipendenze: csv (libreria standard Python)
# ==============================================================================

import csv

# ------------------------------------------------------------------------------
# MAPPATURA CATEGORIE → SETTORI
# Associa ogni ID categoria PrestaShop al settore merceologico corrispondente.
# Aggiungere o modificare gli ID in base alla struttura del proprio negozio.
# ------------------------------------------------------------------------------
mappa_settori = {
    # SETTORE A — RISTORAZIONE / HORECA
    '96': ['A'],
    '337': ['A'], '338': ['A'], '339': ['A'], '340': ['A'],

    # SETTORE B — ESTETICA / PULIZIE
    '99': ['B'], '102': ['B'],
    '349': ['B'], '350': ['B'], '351': ['B'], '352': ['B'],   # Estetico
    '361': ['B'], '362': ['B'], '363': ['B'], '364': ['B'],   # Pulizie

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
    '345': ['G'], '346': ['G'], '347': ['G'], '348': ['G']
}


# ------------------------------------------------------------------------------
# FUNZIONE DI PULIZIA ID
# ------------------------------------------------------------------------------

def super_clean(val):
    """
    Pulisce un valore rimuovendo punti, virgole e spazi.
    Necessario perché PrestaShop può esportare gli ID in formati diversi
    (es. "1.234" oppure "1,234") a seconda della versione o del browser.

    Esempio: "1.234" → "1234"
    """
    if not val:
        return ""
    return str(val).replace('.', '').replace(',', '').strip()


# ------------------------------------------------------------------------------
# FASE 1 — Caricamento catalogo prodotti
# Costruisce un dizionario: reference variante → id_product
# ------------------------------------------------------------------------------
print("📂 Fase 1: Caricamento database prodotti...")

variante_a_prod = {}
try:
    with open('PRODOTTI-VARIANTI.csv', mode='r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            variante_a_prod[super_clean(r.get('reference'))] = super_clean(r.get('id_product'))
except FileNotFoundError:
    print("⚠️  PRODOTTI-VARIANTI.csv non trovato, si prosegue senza.")

# Costruisce un dizionario: id_product → id_category
prod_a_cat = {}
with open('PRODOTTI-CATEGORIE.csv', mode='r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter=';'):
        # Gestisce sia 'id_product' che 'id_prodotti' come nome colonna
        p_id = super_clean(r.get('id_product') or r.get('id_prodotti'))
        prod_a_cat[p_id] = super_clean(r.get('id_category'))

# ------------------------------------------------------------------------------
# FASE 2 — Analisi acquisti per ordine
# Per ogni ordine calcola quante unità sono state acquistate per settore
# ------------------------------------------------------------------------------
print("🔍 Fase 2: Analisi acquisti per ordine...")

ordini_pesi = {}   # { id_ordine: { settore: quantità_totale } }

with open('ORDINE.csv', mode='r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter=';'):
        id_ord  = super_clean(r['IdOrdine'])
        cod_var = super_clean(r['CodiceVariante'])
        qta     = int(str(r['Qta']).replace('.', '').replace(',', '')) if r['Qta'] else 1

        # Risale dall'ID variante all'ID prodotto, poi alla categoria
        id_p   = variante_a_prod.get(cod_var, cod_var)
        cat_id = prod_a_cat.get(id_p, "Sconosciuto")

        # Trova i settori associati alla categoria del prodotto
        settori = mappa_settori.get(cat_id, ["Sconosciuto"])

        ordini_pesi.setdefault(id_ord, {})
        for s in settori:
            ordini_pesi[id_ord][s] = ordini_pesi[id_ord].get(s, 0) + qta

# ------------------------------------------------------------------------------
# FASE 3 — Raggruppamento email e calcolo settore dominante
# Per ogni cliente somma le quantità acquistate per settore su tutti gli ordini
# ------------------------------------------------------------------------------
print("👥 Fase 3: Raggruppamento email e calcolo settore dominante...")

clienti_finali = {}   # { email: { settore: quantità_totale } }

with open('CLIENTE.csv', mode='r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f, delimiter=';'):
        email  = r['Email'].strip().lower()
        id_ord = super_clean(r['IdOrdine'])

        if not email:
            continue

        clienti_finali.setdefault(email, {})

        if id_ord in ordini_pesi:
            for s, qta in ordini_pesi[id_ord].items():
                clienti_finali[email][s] = clienti_finali[email].get(s, 0) + qta

# ------------------------------------------------------------------------------
# FASE 4 — Generazione file CSV per settore
# Ogni email viene assegnata al settore con il maggior numero di acquisti
# ------------------------------------------------------------------------------
print("💾 Fase 4: Generazione file CSV settoriali...")

lettere      = ['A', 'B', 'C', 'E', 'F', 'G']
output_data  = {l: [] for l in lettere}
output_data['ALTRO'] = []   # Clienti non classificabili

for email, punteggi in clienti_finali.items():
    # Esclude le categorie non classificate dal calcolo del vincitore
    validi = {k: v for k, v in punteggi.items() if k != "Sconosciuto"}

    if not validi:
        output_data['ALTRO'].append(email)
    else:
        # Il settore dominante è quello con la quantità totale più alta
        vincitore = max(validi, key=validi.get)
        if vincitore in output_data:
            output_data[vincitore].append(email)
        else:
            output_data['ALTRO'].append(email)

# Scrive un file CSV per ogni settore
for l, lista in output_data.items():
    filename = f'SETTORE_{l}.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Email'])
        for mail in lista:
            writer.writerow([mail])
    print(f"✅ Generato {filename}: {len(lista)} email.")

print("\n🎉 Missione Compiuta! I file sono pronti per l'invio.")
