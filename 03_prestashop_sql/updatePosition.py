# Questo script aggiorna la posizione dei prodotti all'interno delle categorie
# di PrestaShop, leggendo l'ordine desiderato da un file CSV.
#
# Caso d'uso:
#   Quando si vuole riordinare i prodotti in una categoria (es. mettere i
#   bestseller in cima), basta creare un CSV con le reference nell'ordine
#   voluto e lanciare questo script. La posizione viene assegnata in base
#   all'ordine delle righe nel file (riga 1 → position=1, riga 2 → position=2...).
#
# Funzionamento:
#   1. Legge le reference prodotto dal file CSV (una per riga)
#   2. Per ogni reference cerca l'id_product nel database
#   3. Aggiorna la posizione in ps_category_product
#   4. Salta le categorie escluse (es. categorie speciali o root)
#   5. Supporta la modalità DRY_RUN per simulare senza scrivere nel DB
#
# ⚠️  ATTENZIONE: lo script modifica le posizioni in tutte le categorie
#     del prodotto tranne quelle in ESCLUDI_CATEGORIE.
#
# 📦 Dipendenze: pymysql
#
# Installazione:
#     pip install pymysql
# ==============================================================================

import sys
import logging
import pymysql

# ─── CONFIGURAZIONE SCRIPT ────────────────────────────────────────────────────

CSV_FILE = "cat74Dritto.csv"    # File CSV con le reference nell'ordine desiderato
DRY_RUN  = False                # True = simula, False = scrive nel DB

# Lista degli ID categoria da NON aggiornare (es. categorie root, speciali, ecc.)
# Aggiungere o rimuovere ID in base alla struttura del proprio negozio
ESCLUDI_CATEGORIE = [
    96, 337, 338, 339, 340, 100, 353, 354, 355, 356,
    102, 361, 362, 99, 349, 350, 351, 352, 45, 46, 48,
    418, 419, 420, 90, 91, 92, 93, 84, 87
]

# ─── CONFIGURAZIONE DATABASE ──────────────────────────────────────────────────
# ⚠️ Non condividere mai queste credenziali pubblicamente!
# ------------------------------------------------------------------------------
DB_CONFIG = {
    "host":     "IL_TUO_HOST",       # Es. "localhost" o IP del server DB
    "user":     "IL_TUO_UTENTE",     # Es. "root"
    "password": "LA_TUA_PASSWORD",   # Password del database
    "database": "IL_TUO_DATABASE",   # Es. "prestashop"
    "charset":  "utf8mb4",
}

# ─── CONFIGURAZIONE LOGGING ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ─── CONNESSIONE DATABASE ─────────────────────────────────────────────────────

def get_connection():
    """
    Apre e restituisce una connessione al database MySQL.
    Termina lo script con errore se la connessione fallisce.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        log.debug(f"Connesso al database '{DB_CONFIG['database']}'")
        return conn
    except pymysql.MySQLError as e:
        log.error(f"Connessione al DB fallita: {e}")
        sys.exit(1)


# ─── LETTURA FILE CSV ─────────────────────────────────────────────────────────

def leggi_csv(filepath: str) -> list[str]:
    """
    Legge le reference prodotto dal file CSV, una per riga.

    Il file non richiede intestazioni. Vengono ignorati:
      - Righe vuote
      - L'eventuale intestazione "reference" (se presente)
      - Tutto ciò che segue il primo separatore ";" o ","

    Esempio di file valido:
        REF001
        REF002
        REF003

    Args:
        filepath (str): percorso del file CSV

    Returns:
        list[str]: lista ordinata delle reference prodotto
    """
    references = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                ref = line.strip()
                # Salta righe vuote e intestazione
                if not ref or ref.lower() == "reference":
                    continue
                # Prende solo la prima colonna se ci sono separatori
                ref_pulita = ref.split(';')[0].split(',')[0].strip()
                if ref_pulita:
                    references.append(ref_pulita)

    except FileNotFoundError:
        log.error(f"File non trovato: {filepath}")
        sys.exit(1)

    log.info(f"Lette {len(references)} reference dal file.")
    return references


# ─── RICERCA PRODOTTO ─────────────────────────────────────────────────────────

def get_id_product(cursor, reference: str) -> int | None:
    """
    Cerca l'ID prodotto nel database tramite la reference.

    Args:
        cursor:         cursore MySQL attivo
        reference (str): codice reference del prodotto

    Returns:
        int: id_product se trovato, None altrimenti
    """
    cursor.execute(
        "SELECT id_product FROM ps_product WHERE reference = %s LIMIT 1",
        (reference,)
    )
    row = cursor.fetchone()
    return row["id_product"] if row else None


# ─── AGGIORNAMENTO POSIZIONI ──────────────────────────────────────────────────

def aggiorna_posizioni(conn, references: list[str], categorie_escluse: list[int], dry_run: bool = False):
    """
    Aggiorna la posizione di ogni prodotto in ps_category_product.

    La posizione è determinata dall'ordine nel CSV:
      - Prima reference → position = 1
      - Seconda reference → position = 2
      - ecc.

    Le categorie presenti in ESCLUDI_CATEGORIE vengono saltate.

    In modalità DRY_RUN mostra cosa verrebbe fatto senza scrivere nel DB.
    Al termine stampa un riepilogo: aggiornati / non trovati / errori.

    Args:
        conn:                 connessione MySQL attiva
        references (list):    reference nell'ordine desiderato
        categorie_escluse (list): ID categoria da non modificare
        dry_run (bool):       True = simula, False = scrive
    """
    # Costruisce il filtro SQL per le categorie escluse
    if categorie_escluse:
        escluse_placeholder = ", ".join(["%s"] * len(categorie_escluse))
        where_escludi = f"AND id_category NOT IN ({escluse_placeholder})"
    else:
        where_escludi = ""

    update_sql = f"""
        UPDATE ps_category_product
        SET    position = %s
        WHERE  id_product = %s
          {where_escludi}
    """

    not_found   = []   # Reference non trovate nel DB
    no_category = []   # Prodotti senza categorie valide (già aggiornati o esclusi)
    updated     = []   # Prodotti aggiornati con successo
    errors      = []   # Prodotti con errori SQL

    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        for i, reference in enumerate(references):
            position   = i + 1   # La posizione parte da 1

            id_product = get_id_product(cursor, reference)
            if id_product is None:
                log.debug(f"Reference non trovata nel DB: '{reference}'")
                not_found.append(reference)
                continue

            params = [position, id_product] + categorie_escluse

            if dry_run:
                # In DRY_RUN mostra le categorie che verrebbero aggiornate
                select_sql = f"""
                    SELECT id_category FROM ps_category_product
                    WHERE  id_product = %s {where_escludi}
                """
                cursor.execute(select_sql, [id_product] + categorie_escluse)
                cats = [r["id_category"] for r in cursor.fetchall()]
                if cats:
                    log.info(f"[DRY-RUN] '{reference}' (ID={id_product}) → position={position}")
                    updated.append(reference)
                else:
                    log.debug(f"[DRY-RUN] '{reference}' (ID={id_product}) → nessuna categoria valida")
                    no_category.append(reference)
            else:
                try:
                    cursor.execute(update_sql, params)
                    rows_affected = cursor.rowcount
                    if rows_affected == 0:
                        log.debug(f"'{reference}' (ID={id_product}) → già aggiornato o nessuna categoria valida")
                        no_category.append(reference)
                    else:
                        log.info(f"✔ '{reference}' (ID={id_product}) → position={position} ({rows_affected} righe)")
                        updated.append(reference)
                except pymysql.MySQLError as e:
                    log.error(f"Errore su '{reference}' (ID={id_product}): {e}")
                    errors.append(reference)

        # Commit unico alla fine per tutte le modifiche
        if not dry_run:
            conn.commit()
            log.debug("💾 Commit eseguito.")

    # ── Riepilogo finale ──────────────────────────────────────────────────────
    log.info("═" * 50)
    log.info("RIEPILOGO " + ("(DRY-RUN)" if dry_run else "(REALE)"))
    log.info("═" * 50)
    log.info(f"  Aggiornati                  : {len(updated)}")
    log.info(f"  Reference non trovate       : {len(not_found)}")
    log.info(f"  Nessuna cat. valida/già agg.: {len(no_category)}")
    log.info(f"  Errori                      : {len(errors)}")

    if errors:
        log.error(f"  Reference con errori SQL    : {errors}")
    if dry_run:
        log.info("  Dry-run completato. Imposta DRY_RUN = False per applicare.")


# ─── FUNZIONE PRINCIPALE ──────────────────────────────────────────────────────

def main():
    """
    Punto di ingresso dello script.
    Legge il CSV, apre la connessione e avvia l'aggiornamento delle posizioni.
    """
    log.info("=" * 50)
    log.info("  UPDATE POSIZIONI ps_category_product")
    log.info("=" * 50)

    if DRY_RUN:
        log.info("⚠️  Modalità DRY-RUN attiva: nessuna modifica verrà salvata.")
    if ESCLUDI_CATEGORIE:
        log.info(f"🚫 Categorie escluse: {ESCLUDI_CATEGORIE}")

    references = leggi_csv(CSV_FILE)
    conn       = get_connection()

    try:
        aggiorna_posizioni(conn, references, ESCLUDI_CATEGORIE, dry_run=DRY_RUN)
    finally:
        conn.close()
        log.debug("Connessione chiusa.")


# ─── PUNTO DI AVVIO ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
