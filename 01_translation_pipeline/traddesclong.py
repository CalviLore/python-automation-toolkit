# ------------------------------------------------------------------------------
# Questo script traduce automaticamente le descrizioni lunghe dei prodotti
# dall'italiano verso una lingua target usando l'AI DeepSeek.
#
# Rispetto a traddescbrev.py, questo script gestisce testi più lunghi e
# complessi, quindi include:
#   - Timeout più alto per chiamata API (45s invece di default)
#   - Retry automatico fino a 3 volte in caso di errore
#   - Salvataggio automatico ogni 50 prodotti (backup di sicurezza)
#   - Pausa minima tra i thread per evitare sovraccarico dell'API
#
# Funzionamento:
#   1. Legge le descrizioni lunghe in HTML dal CSV di input
#   2. Converte HTML → Markdown per ogni prodotto
#   3. Elabora più prodotti contemporaneamente (parallelizzazione)
#   4. Riconverte il testo tradotto Markdown → HTML
#   5. Salva ogni 50 prodotti (backup) e alla fine il file completo
#
# File di input  → proddesclng.csv
# File di output → import_tradotto_desclng_XX.csv (es. _es.csv)
#
# 📦 Dipendenze: pandas, openai, markdown, markdownify
# ==============================================================================

import pandas as pd
import os
import markdown
import time
from markdownify import markdownify as md
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------------------------------------
# CONFIGURAZIONE API DEEPSEEK
# ⚠️ Non condividere mai queste credenziali pubblicamente!
# Puoi ottenere la tua API key su https://platform.deepseek.com
# ------------------------------------------------------------------------------
DEEPSEEK_API_KEY  = "LA_TUA_API_KEY"          # Sostituisci con la tua API key
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODELLO_DEEPSEEK  = "deepseek-chat"

# ------------------------------------------------------------------------------
# CONFIGURAZIONE FILE
# ------------------------------------------------------------------------------
FILE_CSV_INPUT = "proddesclng.csv"   # CSV con le descrizioni lunghe in italiano
SEPARATORE     = ";"

# ------------------------------------------------------------------------------
# IMPOSTAZIONI VELOCITÀ E SICUREZZA
# ------------------------------------------------------------------------------
MAX_WORKERS = 10    # Chiamate API simultanee
MAX_RETRIES = 3     # Tentativi prima di dichiarare un prodotto fallito
PAUSA_RIGA  = 0.3   # Pausa in secondi tra un thread e l'altro (evita rate limit)
SAVE_EVERY  = 50    # Salva il file di backup ogni N prodotti completati

# ------------------------------------------------------------------------------
# IMPOSTAZIONI LINGUA TARGET
# Cambia LINGUA_TARGET per tradurre in una lingua diversa:
#   "2" = Inglese  |  "3" = Francese  |  "4" = Tedesco  |  "5" = Spagnolo
# ------------------------------------------------------------------------------
LINGUA_TARGET = "5"

LINGUE = {
    "1": {"nome": "Italiano",  "codice": "IT"},
    "2": {"nome": "Inglese",   "codice": "EN"},
    "3": {"nome": "Francese",  "codice": "FR"},
    "4": {"nome": "Tedesco",   "codice": "DE"},
    "5": {"nome": "Spagnolo",  "codice": "ES"},
}

INFO_LINGUA = LINGUE.get(str(LINGUA_TARGET))

# Inizializza il client DeepSeek (compatibile con le API OpenAI)
client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# ------------------------------------------------------------------------------
# TRADUZIONE SINGOLA DESCRIZIONE LUNGA
# ------------------------------------------------------------------------------

def traduci_singola_riga(id_prodotto, html_originale):
    """
    Traduce la descrizione lunga di un singolo prodotto con gestione errori.

    Flusso di conversione:
        HTML originale → Markdown → Traduzione AI → HTML tradotto

    Differenze rispetto alla descrizione breve:
      - Timeout API più lungo (45s) per gestire testi corposi
      - Retry automatico fino a MAX_RETRIES volte con attesa crescente
      - Pausa PAUSA_RIGA dopo ogni traduzione riuscita

    Args:
        id_prodotto (int/str): ID del prodotto
        html_originale (str):  descrizione lunga in HTML da tradurre

    Returns:
        dict: {'id_product', 'description', 'id_lang'} se successo
        dict: {'error': messaggio} se tutti i tentativi falliscono
        None: se la descrizione è vuota
    """
    if not html_originale or pd.isna(html_originale) or str(html_originale).strip() == "":
        return None

    # Converte HTML in Markdown per una migliore elaborazione da parte dell'AI
    testo_md = md(str(html_originale), heading_style="ATX").strip()

    for tentativo in range(MAX_RETRIES):
        try:
            response = client_deepseek.chat.completions.create(
                model=MODELLO_DEEPSEEK,
                messages=[
                    {
                        "role": "system",
                        "content": "Expert technical translator for PPE safety equipment."
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate to {INFO_LINGUA['nome']}: {testo_md}\n"
                            "Rules: Keep format, keep S1P/S3/SRC/ESD. No chat."
                            # Mantieni la formattazione e le sigle di sicurezza
                        )
                    }
                ],
                temperature=0.1,
                timeout=45      # Timeout esteso per descrizioni lunghe
            )

            md_tradotto = response.choices[0].message.content.strip()

            # Riconverte Markdown tradotto in HTML e rimuove i ritorni a capo
            html_finale = markdown.markdown(md_tradotto).replace('\n', ' ').strip()

            time.sleep(PAUSA_RIGA)  # Pausa minima per non sovraccaricare l'API
            return {
                'id_product': id_prodotto,
                'description': html_finale,
                'id_lang':    LINGUA_TARGET
            }

        except Exception as e:
            if tentativo < MAX_RETRIES - 1:
                # Attesa crescente tra i tentativi: 3s, 6s, 9s...
                time.sleep((tentativo + 1) * 3)
            else:
                return {"error": f"ID {id_prodotto} FALLITO dopo {MAX_RETRIES} tentativi: {str(e)}"}


# ------------------------------------------------------------------------------
# ELABORAZIONE FILE CSV CON PARALLELIZZAZIONE E BACKUP AUTOMATICO
# ------------------------------------------------------------------------------

def avvia():
    """
    Carica il CSV di input, traduce tutte le descrizioni lunghe in parallelo
    con salvataggio automatico ogni SAVE_EVERY prodotti.

    Il backup periodico è fondamentale per i cataloghi grandi: in caso di
    interruzione, i progressi già completati non vanno persi.

    Gestisce anche gli ID prodotto con formato decimale (es. "1.234")
    convertendoli nel numero intero corretto tramite logica sequenziale.

    Output CSV → colonne: id_product | description | id_lang
    """
    print(f"\n{'=' * 65}")
    print(f"🚀 START ({MAX_WORKERS} THREAD): {FILE_CSV_INPUT} → {INFO_LINGUA['nome']}")
    print(f"💾 Salvataggio automatico ogni {SAVE_EVERY} prodotti")
    print(f"{'=' * 65}\n", flush=True)

    if not os.path.exists(FILE_CSV_INPUT):
        print("❌ File non trovato!")
        return

    df = pd.read_csv(FILE_CSV_INPUT, sep=SEPARATORE, encoding='utf-8-sig', dtype=str)
    # Pulizia intestazioni colonne da virgolette e spazi
    df.columns = [c.strip().replace('"', '').replace("'", "") for c in df.columns]

    # Ricerca automatica delle colonne ID e descrizione
    col_id   = next((c for c in df.columns if c.lower() in ['id_prod', 'id_product']), None)
    col_desc = next((c for c in df.columns if c.lower() in ['description', 'meta_description']), None)

    if col_id is None or col_desc is None:
        print(f"❌ Colonne non trovate. Trovate: {df.columns.tolist()}")
        return

    # ------------------------------------------------------------------
    # NORMALIZZAZIONE ID
    # PrestaShop può esportare ID come "1.234" → va ricostruito come 1234
    # ------------------------------------------------------------------
    ids_puliti        = []
    last_id_processed = 0

    for _, row in df.iterrows():
        raw_id = str(row[col_id]).strip()
        try:
            if '.' in raw_id:
                p   = raw_id.split('.')
                i_p = int(p[0])
                i_g = int(p[0] + p[1].ljust(3, '0'))
                category_id = i_p if (last_id_processed < 999 and i_p > last_id_processed) else i_g
            else:
                category_id = int(raw_id)
                if category_id < 100 and last_id_processed > 999:
                    category_id *= 1000
            last_id_processed = category_id
        except Exception:
            category_id = raw_id   # Fallback: usa il valore grezzo
        ids_puliti.append(category_id)

    df['id_target'] = ids_puliti
    total_rows      = len(df)
    results         = []
    count           = 0
    out_name        = f"import_tradotto_desclng_{INFO_LINGUA['codice'].lower()}.csv"

    # Elaborazione parallela con backup automatico
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = {
            executor.submit(traduci_singola_riga, row['id_target'], row[col_desc]): row['id_target']
            for _, row in df.iterrows()
        }

        for future in as_completed(tasks):
            count += 1
            res   = future.result()

            if res and "error" not in res:
                results.append(res)
                print(f"✅ [{count}/{total_rows}] ID {res['id_product']} completato", flush=True)
            elif res and "error" in res:
                print(f"❌ [{count}/{total_rows}] {res['error']}", flush=True)

            # ----------------------------------------------------------
            # SALVATAGGIO PARZIALE DI SICUREZZA
            # Ogni SAVE_EVERY prodotti salva i progressi sul file CSV.
            # Utile per cataloghi grandi: se lo script si interrompe,
            # i prodotti già tradotti non vanno persi.
            # ----------------------------------------------------------
            if count % SAVE_EVERY == 0 and results:
                df_temp = pd.DataFrame(results).sort_values(by='id_product')
                df_temp.to_csv(out_name, index=False, sep=SEPARATORE, encoding='utf-8-sig')
                print(f"\n💾 [BACKUP] Salvati {len(results)} prodotti → {out_name}\n", flush=True)

    # Salvataggio finale completo
    if results:
        df_out = pd.DataFrame(results).sort_values(by='id_product')
        df_out.to_csv(out_name, index=False, sep=SEPARATORE, encoding='utf-8-sig')
        print(f"\n{'=' * 65}")
        print(f"🏆 COMPLETATO! File finale: {out_name}")
        print(f"{'=' * 65}")


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    avvia()