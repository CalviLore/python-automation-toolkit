# ------------------------------------------------------------------------------
# Questo script traduce automaticamente le descrizioni brevi dei prodotti
# dall'italiano verso una lingua target usando l'AI DeepSeek.
#
# Le descrizioni sono in formato HTML: lo script le converte in Markdown
# prima di inviarle all'AI (più leggibile dal modello) e le riconverte
# in HTML dopo la traduzione.
#
# Funzionamento:
#   1. Legge le descrizioni brevi in HTML dal CSV di input
#   2. Converte HTML → Markdown per ogni prodotto
#   3. Elabora più prodotti contemporaneamente (parallelizzazione)
#   4. Riconverte il testo tradotto Markdown → HTML
#   5. Salva i risultati in un CSV pronto per l'importazione su PrestaShop
#
# File di input  → proddescbrv.csv
# File di output → import_tradotto_descbrv_XX.csv (es. _es.csv)
#
# 📦 Dipendenze: pandas, openai, markdown, markdownify
# ==============================================================================

import pandas as pd
import os
import markdown
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
# CONFIGURAZIONE FILE E PARALLELIZZAZIONE
# ------------------------------------------------------------------------------
FILE_CSV_INPUT = "proddescbrv.csv"   # CSV con le descrizioni brevi in italiano
SEPARATORE     = ";"
MAX_WORKERS    = 10                  # Chiamate API simultanee
                                     # Aumentare a 15-20 per cataloghi grandi

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

INFO_LINGUA    = LINGUE.get(str(LINGUA_TARGET))

# Inizializza il client DeepSeek (compatibile con le API OpenAI)
client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# ------------------------------------------------------------------------------
# TRADUZIONE SINGOLA DESCRIZIONE BREVE
# ------------------------------------------------------------------------------

def traduci_singola_riga(id_prodotto, html_originale):
    """
    Traduce la descrizione breve di un singolo prodotto.

    Flusso di conversione:
        HTML originale → Markdown → Traduzione AI → HTML tradotto

    Il passaggio per Markdown è necessario perché i modelli AI
    gestiscono meglio il testo strutturato rispetto all'HTML grezzo.
    Il formato (grassetto **, liste -) viene preservato nella traduzione.

    Args:
        id_prodotto (int/str): ID del prodotto
        html_originale (str):  descrizione breve in HTML da tradurre

    Returns:
        dict: {'id_product', 'description_short', 'id_lang'} se successo
        dict: {'error': messaggio} in caso di errore
        None: se la descrizione è vuota
    """
    try:
        if not html_originale or pd.isna(html_originale):
            return None

        # Converte l'HTML in Markdown per facilitare l'elaborazione dell'AI
        testo_md = md(str(html_originale), heading_style="ATX").strip()

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
                        "Rules: Keep ** and -, no chat."
                        # Mantieni grassetto (**) e liste (-), rispondi solo con il testo
                    )
                }
            ],
            temperature=0.1   # Bassa per massima fedeltà al testo originale
        )

        md_tradotto = response.choices[0].message.content.strip()

        # Riconverte il Markdown tradotto in HTML e rimuove i ritorni a capo
        html_finale = markdown.markdown(md_tradotto).replace('\n', ' ').strip()

        return {
            'id_product':        id_prodotto,
            'description_short': html_finale,
            'id_lang':           LINGUA_TARGET
        }

    except Exception as e:
        return {"error": f"ID {id_prodotto}: {str(e)}"}


# ------------------------------------------------------------------------------
# ELABORAZIONE FILE CSV CON PARALLELIZZAZIONE
# ------------------------------------------------------------------------------

def avvia():
    """
    Carica il CSV di input, traduce tutte le descrizioni brevi in parallelo
    e salva il risultato ordinato per ID prodotto.

    Gestisce anche gli ID prodotto con formato decimale (es. "1.234")
    convertendoli nel numero intero corretto tramite logica sequenziale.

    Output CSV → colonne: id_product | description_short | id_lang
    """
    print(f"\n{'=' * 65}")
    print(f"🚀 START: {FILE_CSV_INPUT} → {INFO_LINGUA['nome']}")
    print(f"{'=' * 65}", flush=True)

    if not os.path.exists(FILE_CSV_INPUT):
        print("❌ File non trovato!")
        return

    df = pd.read_csv(FILE_CSV_INPUT, sep=SEPARATORE, encoding='utf-8-sig', dtype=str)

    # Ricerca automatica delle colonne ID e descrizione
    col_id   = next((c for c in df.columns if c.lower() in ['id_prod', 'id_product']), None)
    col_desc = next((c for c in df.columns if c.lower() in ['meta_description', 'description_short']), None)

    if not col_id or not col_desc:
        print(f"❌ Colonne non trovate. Trovate: {df.columns.tolist()}")
        return

    # ------------------------------------------------------------------
    # NORMALIZZAZIONE ID
    # PrestaShop può esportare ID come "1.234" → va ricostruito come 1234
    # La logica sequenziale garantisce la corretta interpretazione
    # ------------------------------------------------------------------
    ids_puliti        = []
    last_id_processed = 0

    for _, row in df.iterrows():
        raw_id = str(row[col_id]).strip()
        try:
            if '.' in raw_id:
                p    = raw_id.split('.')
                i_p  = int(p[0])
                i_g  = int(p[0] + p[1].ljust(3, '0'))
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

    print(f"📦 Prodotti da elaborare: {total_rows}", flush=True)
    print(f"⚙️  Thread simultanei: {MAX_WORKERS}", flush=True)
    print(f"{'-' * 65}\n", flush=True)

    results = []
    count   = 0

    # Elaborazione parallela: MAX_WORKERS traduzioni contemporanee
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

            # Riepilogo progressi ogni 20 prodotti
            if count % 20 == 0:
                print(f"\n--- 📈 PROGRESSO: {(count / total_rows * 100):.1f}% ---\n", flush=True)

    # Salvataggio file di output ordinato per ID prodotto
    if results:
        df_out     = pd.DataFrame(results).sort_values(by='id_product')
        nome_output = f"import_tradotto_descbrv_{INFO_LINGUA['codice'].lower()}.csv"
        df_out.to_csv(nome_output, index=False, sep=SEPARATORE, encoding='utf-8-sig')
        print(f"\n{'=' * 65}")
        print(f"🏆 COMPLETATO! Salvato in: {nome_output}")
        print(f"{'=' * 65}")


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    avvia()