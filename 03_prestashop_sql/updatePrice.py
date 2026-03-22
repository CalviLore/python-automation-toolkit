# Questo script aggiorna i prezzi dei prodotti su PrestaShop, ma solo per
# i prodotti presenti in una categoria specifica (filtro per reference).
#
# Differenza rispetto a UpdatePrice.py:
#   UpdatePrice.py  → aggiorna TUTTI i prodotti del CSV
#   Questo script   → aggiorna SOLO i prodotti presenti anche in cat74.csv
#                     (utile per aggiornare i prezzi di una sola categoria)
#
# Funzionamento:
#   1. Legge cat74.csv → costruisce la lista delle reference da aggiornare
#   2. Legge listino1.csv → per ogni riga controlla se la reference è in cat74
#   3. Se sì: aggiorna il prezzo in ps_product_shop
#   4. Stampa a video SOLO i prodotti effettivamente aggiornati
#   5. Supporta DRY_RUN per simulare senza scrivere nel DB
#   6. Salva un log su file (update_prices.log)
#
# File di input:
#   - listino1.csv → reference + prezzo (separatore ";")
#   - cat74.csv    → reference dei prodotti della categoria (una per riga)
#
# 📦 Dipendenze: mysql-connector-python
#
# Installazione:
#     pip install mysql-connector-python
# ==============================================================================

import csv
import sys
import logging
import mysql.connector
from mysql.connector import Error
from decimal import Decimal, InvalidOperation

# ─── CONFIGURAZIONE DATABASE ──────────────────────────────────────────────────
# ⚠️ Non condividere mai queste credenziali pubblicamente!
# ------------------------------------------------------------------------------
DB_HOST     = "IL_TUO_HOST"       # Es. "localhost" o IP del server DB
DB_NAME     = "IL_TUO_DATABASE"   # Es. "prestashop"
DB_USER     = "IL_TUO_UTENTE"     # Es. "root"
DB_PASSWORD = "LA_TUA_PASSWORD"   # Password del database
DB_PREFIX   = "ps_"               # Prefisso tabelle PrestaShop (default: "ps_")

# ─── CONFIGURAZIONE SCRIPT ────────────────────────────────────────────────────
CSV_DELIMITER = ";"     # Separatore CSV (cambia in "," se necessario)
DRY_RUN       = False   # True = simula, False = scrive nel DB

# ─── CONFIGURAZIONE LOGGING ───────────────────────────────────────────────────
# I log vengono scritti sia su console che su file (update_prices.log)
# Livello INFO: mostra solo i prodotti aggiornati e il riepilogo finale
# Livello DEBUG: mostra anche i prodotti ignorati e non trovati
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("update_prices.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ─── CONNESSIONE DATABASE ─────────────────────────────────────────────────────

def get_connection():
    """Apre e restituisce una connessione al database MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
    )


# ─── LETTURA REFERENCE CATEGORIA ─────────────────────────────────────────────

def carica_reference_cat(filepath: str) -> set:
    """
    Legge un file CSV e restituisce un set con tutte le reference prodotto.
    Usato per caricare la lista dei prodotti della categoria da filtrare.

    Args:
        filepath (str): percorso del file CSV (es. cat74.csv)

    Returns:
        set: insieme delle reference trovate nel file
    """
    reference_set = set()
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=CSV_DELIMITER)
        for row in reader:
            if row and row[0].strip():
                reference_set.add(row[0].strip())
    log.debug(f"Caricate {len(reference_set)} reference da '{filepath}'")
    return reference_set


# ─── ELABORAZIONE LISTINO E AGGIORNAMENTO PREZZI ─────────────────────────────

def process_csv(listino: str, cat: str, dry_run: bool = False):
    """
    Legge il listino prezzi e aggiorna solo i prodotti presenti nella categoria.

    Per ogni riga del listino:
      1. Verifica che la reference sia presente nel file categoria (cat74.csv)
      2. Valida il prezzo (deve essere un numero positivo)
      3. Cerca il prodotto nel DB tramite la reference
      4. Aggiorna il prezzo in ps_product_shop

    In modalità DRY_RUN simula le operazioni senza scrivere nel DB.
    Stampa a video SOLO i prodotti effettivamente aggiornati (o che
    verrebbero aggiornati in DRY_RUN).

    Args:
        listino (str):  percorso del CSV con reference + prezzo
        cat (str):      percorso del CSV con le reference della categoria
        dry_run (bool): True = simula, False = scrive
    """
    if dry_run:
        log.info("=" * 50)
        log.info("  MODALITÀ DRY-RUN: nessuna modifica al DB")
        log.info("=" * 50)

    # Carica le reference della categoria da filtrare
    try:
        reference_cat = carica_reference_cat(cat)
    except FileNotFoundError:
        log.error(f"File categoria non trovato: {cat}")
        sys.exit(1)

    # Connessione al database
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        log.debug(f"Connesso al database '{DB_NAME}'")
    except Error as e:
        log.error(f"Impossibile connettersi al database: {e}")
        sys.exit(1)

    product_table      = f"{DB_PREFIX}product"
    product_shop_table = f"{DB_PREFIX}product_shop"

    ok       = 0   # Prodotti aggiornati con successo
    ignorati = 0   # Prodotti non presenti nella categoria (saltati)
    not_found= 0   # Prodotti non trovati nel DB o già aggiornati
    errors   = 0   # Righe con prezzo non valido
    total    = 0   # Totale righe elaborate (esclusi gli ignorati)

    try:
        with open(listino, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.reader(csvfile, delimiter=CSV_DELIMITER)

            for line_num, row in enumerate(reader, start=1):

                # Salta righe vuote o con dati insufficienti
                if not row or len(row) < 2:
                    log.debug(f"Riga {line_num}: ignorata (dati insufficienti)")
                    continue

                reference = row[0].strip()
                raw_price = row[1].strip().replace(",", ".")

                if not reference:
                    log.debug(f"Riga {line_num}: reference vuota, ignorata")
                    continue

                # Filtra: processa solo le reference presenti in cat74.csv
                if reference not in reference_cat:
                    log.debug(f"Riga {line_num}: '{reference}' non in categoria → ignorata")
                    ignorati += 1
                    continue

                # Valida il prezzo (deve essere un numero decimale positivo)
                try:
                    price = Decimal(raw_price)
                    if price < 0:
                        raise ValueError("prezzo negativo")
                except (InvalidOperation, ValueError) as e:
                    log.error(f"Riga {line_num}: prezzo non valido '{raw_price}' per '{reference}' → {e}")
                    errors += 1
                    total  += 1
                    continue

                total += 1

                if dry_run:
                    # Simula: verifica solo se il prodotto esiste nel DB
                    cursor.execute(
                        f"SELECT id_product FROM {product_table} WHERE reference = %s LIMIT 1",
                        (reference,),
                    )
                    if not cursor.fetchone():
                        log.debug(f"[DRY-RUN] '{reference}' NON trovata in DB")
                        not_found += 1
                    else:
                        log.info(f"[DRY-RUN] Riga {line_num}: '{reference}' → verrebbe aggiornata a {price}")
                        ok += 1
                else:
                    # Aggiorna il prezzo in ps_product_shop tramite subquery sulla reference
                    cursor.execute(
                        f"""
                        UPDATE {product_shop_table}
                        SET price = %s
                        WHERE id_product IN (
                            SELECT id_product FROM {product_table} WHERE reference = %s
                        )
                        """,
                        (float(price), reference),
                    )

                    if cursor.rowcount == 0:
                        # Prodotto non trovato nel DB o prezzo già identico
                        log.debug(f"Riga {line_num}: '{reference}' non trovata o prezzo già aggiornato")
                        not_found += 1
                    else:
                        conn.commit()
                        log.info(f"✔ Riga {line_num}: '{reference}' → prezzo aggiornato a {price}")
                        ok += 1

    except FileNotFoundError:
        log.error(f"File listino non trovato: {listino}")
        sys.exit(1)
    except KeyboardInterrupt:
        log.warning("⚠️  Interrotto dall'utente. Rollback in corso...")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    # ── Riepilogo finale ──────────────────────────────────────────────────────
    modalita = "DRY-RUN" if dry_run else "REALE"
    log.info("─" * 50)
    log.info(f"Riepilogo [{modalita}]")
    log.info(f"  Totale righe elaborate : {total}")
    log.info(f"  ✔ Aggiornati           : {ok}")
    log.info(f"  ⏭ Ignorati (no cat74)  : {ignorati}")
    log.info(f"  ✘ Non trovati/già agg. : {not_found}")
    log.info(f"  ⚠ Errori               : {errors}")
    log.info("─" * 50)

    if dry_run:
        log.info("Dry-run completato. Imposta DRY_RUN = False per applicare.")


# ─── PUNTO DI AVVIO ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    process_csv("listino1.csv", "cat74.csv", dry_run=DRY_RUN)
