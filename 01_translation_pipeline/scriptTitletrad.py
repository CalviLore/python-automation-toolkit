# ------------------------------------------------------------------------------
# Questo script traduce automaticamente i nomi prodotto (H1) dall'italiano
# verso una lingua target usando l'AI DeepSeek.
#
# Il modello è ottimizzato per il settore DPI (Dispositivi di Protezione
# Individuale): mantiene le sigle di sicurezza (S1P, S3, SRC, ESD...),
# non traduce i brand (Diadora, U-Power, Cofra...) e usa la terminologia
# tecnica corretta nella lingua di destinazione.
#
# Funzionamento:
#   1. Legge i nomi prodotto dal file CSV di input
#   2. Per ogni riga invia il nome all'API DeepSeek per la traduzione
#   3. Salva i risultati in un CSV pronto per l'importazione su PrestaShop
#
# File di input  → productfixmeta.csv
# File di output → h1_mancanti_XX.csv  (es. h1_mancanti_fr.csv)
#
# 📦 Dipendenze: pandas, openai
# ==============================================================================

import pandas as pd
import time
import os
import csv
from openai import OpenAI

# ------------------------------------------------------------------------------
# DISATTIVAZIONE PROXY DI RETE
# Evita che richieste passino attraverso proxy aziendali che potrebbero
# bloccare le chiamate verso l'API esterna di DeepSeek
# ------------------------------------------------------------------------------
os.environ['HTTP_PROXY']  = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy']  = ''
os.environ['https_proxy'] = ''

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
FILE_CSV_INPUT     = "productfixmeta.csv"  # CSV con i nomi prodotto in italiano
SEPARATORE         = ";"
RETRY_PAUSA_INIZIALE = 3                   # Secondi di attesa al primo errore API

# ------------------------------------------------------------------------------
# IMPOSTAZIONI LINGUA TARGET
# Cambia LINGUA_TARGET per tradurre in una lingua diversa:
#   "2" = Inglese  |  "3" = Francese  |  "4" = Tedesco  |  "5" = Spagnolo
# ------------------------------------------------------------------------------
LINGUA_TARGET = "3"

LINGUE = {
    "1": {"nome": "Italiano",  "codice": "IT"},
    "2": {"nome": "Inglese",   "codice": "EN"},
    "3": {"nome": "Francese",  "codice": "FR"},
    "4": {"nome": "Tedesco",   "codice": "DE"},
    "5": {"nome": "Spagnolo",  "codice": "ES"},
}

INFO_LINGUA            = LINGUE.get(str(LINGUA_TARGET))
CODICE_NUMERICO_TARGET = str(LINGUA_TARGET)

# Inizializza il client DeepSeek (compatibile con le API OpenAI)
client_deepseek = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, http_client=None)


# ------------------------------------------------------------------------------
# TRADUZIONE NOME PRODOTTO (H1)
# ------------------------------------------------------------------------------

def genera_h1_deepseek(product_name, lang_info):
    """
    Invia il nome di un prodotto all'AI DeepSeek e restituisce la traduzione.

    Il prompt è ottimizzato per il settore DPI:
      - Usa terminologia tecnica corretta (es. "Safety shoes", "work trousers")
      - Mantiene invariate le sigle di sicurezza (S1P, S3, SRC, ESD, HRO...)
      - Non traduce i brand (Diadora, U-Power, Base, Cofra, ecc.)
      - Rimuove termini marketing (Offerta, Promo, Prezzo basso)

    In caso di errore API riprova fino a 5 volte con attesa crescente.

    Args:
        product_name (str): nome prodotto in italiano
        lang_info (dict):   dizionario con 'nome' e 'codice' della lingua target

    Returns:
        str: nome prodotto tradotto, oppure il nome originale in caso di fallimento
    """
    if pd.isna(product_name) or str(product_name).strip() == "":
        return ""

    nome_lingua = lang_info['nome']

    prompt_sistema = (
        f"Sei un esperto traduttore tecnico e SEO specializzato in DPI "
        f"(Dispositivi di Protezione Individuale) per il mercato {nome_lingua}."
    )
    prompt_utente = (
        f"Traduci accuratamente il seguente nome prodotto dall'ITALIANO al {nome_lingua.upper()}.\n\n"
        f"Prodotto: {product_name}\n\n"
        "REGOLE TASSATIVE:\n"
        "1. TERMINOLOGIA: Usa i termini tecnici corretti del settore (es. Safety shoes, work trousers).\n"
        "2. STANDARD: Mantieni invariate le sigle di sicurezza (S1P, S3, SRC, ESD, HRO, HI, CI).\n"
        "3. BRAND: NON tradurre i nomi dei marchi (Diadora, U-Power, Base, Cofra, ecc.).\n"
        "4. PULIZIA: Rimuovi termini marketing come 'Offerta', 'Prezzo basso' o 'Promo'.\n"
        "5. OUTPUT: Restituisci SOLO il testo tradotto. No spiegazioni, no virgolette."
    )

    retry_delay = RETRY_PAUSA_INIZIALE
    attempt     = 1
    row_start_time = time.time()

    while True:
        try:
            response = client_deepseek.chat.completions.create(
                model=MODELLO_DEEPSEEK,
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user",   "content": prompt_utente}
                ],
                temperature=0.2   # Bassa per massima precisione tecnica
            )
            h1_tradotto = response.choices[0].message.content.strip().replace('"', '')
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Tradotto in {time.time() - row_start_time:.2f}s")
            return h1_tradotto

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Errore API: {e}. Riprovo (tentativo {attempt})...")
            if attempt > 5:
                return product_name   # Fallback: restituisce il nome originale
            time.sleep(retry_delay)
            retry_delay *= 1.5        # Attesa crescente tra i tentativi
            attempt += 1


# ------------------------------------------------------------------------------
# ELABORAZIONE FILE CSV
# ------------------------------------------------------------------------------

def elabora_h1_pandas():
    """
    Carica il CSV di input, traduce ogni nome prodotto e salva il risultato.

    Gestisce anche gli ID prodotto con formato decimale (es. "1.234")
    convertendoli nel numero intero corretto tramite logica sequenziale.

    Output: CSV con colonne → id_prod | h1_XX | idl
    """
    print(f"--- Caricamento file: {FILE_CSV_INPUT} ---")
    try:
        # dtype=str evita che pandas interpreti gli ID come numeri decimali
        df = pd.read_csv(FILE_CSV_INPUT, sep=SEPARATORE, encoding='utf-8-sig', dtype=str)
    except Exception as e:
        print(f"❌ Errore apertura file: {e}")
        return

    # Ricerca automatica delle colonne ID e nome prodotto
    col_id   = next((c for c in df.columns if "id" in c.lower()), None)
    col_name = next((c for c in df.columns if any(x in c.lower() for x in ["name", "titolo", "desc", "nome"])), None)

    if not col_id or not col_name:
        print(f"❌ Colonne non trovate. Trovate: {df.columns.tolist()}")
        return

    results        = []
    start_time     = time.time()
    last_id_processed = 0

    print(f"Inizio elaborazione di {len(df)} righe per {INFO_LINGUA['nome']}...")

    for index, row in df.iterrows():
        raw_id = str(row[col_id]).strip()

        # ------------------------------------------------------------------
        # NORMALIZZAZIONE ID
        # PrestaShop può esportare ID come "1.234" (es. 1234) o "1.5" (es. 1500)
        # Questa logica ricostruisce l'intero corretto leggendo la sequenza
        # ------------------------------------------------------------------
        if '.' in raw_id:
            parti    = raw_id.split('.')
            i_intera = int(parti[0])
            i_grande = int(parti[0] + parti[1].ljust(3, '0'))

            if last_id_processed < 999 and i_intera > last_id_processed:
                category_id = i_intera
            elif i_grande > last_id_processed:
                category_id = i_grande
            else:
                category_id = i_intera
        else:
            category_id = int(raw_id)
            if category_id < 100 and last_id_processed > 999:
                category_id = category_id * 1000

        last_id_processed = category_id
        # ------------------------------------------------------------------

        print(f"\n--- Riga {index + 1}/{len(df)} (ID: {raw_id} → {category_id}) ---")

        h1_tradotto = genera_h1_deepseek(row[col_name], INFO_LINGUA)

        results.append({
            'id_prod':                          category_id,
            f'h1_{INFO_LINGUA["codice"].lower()}': h1_tradotto,
            'idl':                              CODICE_NUMERICO_TARGET
        })

    # Salva il file di output
    df_output  = pd.DataFrame(results)
    nome_output = f"h1_mancanti_{INFO_LINGUA['codice'].lower()}.csv"
    df_output.to_csv(nome_output, index=False, sep=SEPARATORE, encoding='utf-8-sig')

    tempo_totale = (time.time() - start_time) / 60
    print(f"\n{'=' * 60}")
    print(f"✅ COMPLETATO in {tempo_totale:.1f} minuti → {nome_output}")
    print(f"{'=' * 60}")


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    elabora_h1_pandas()
