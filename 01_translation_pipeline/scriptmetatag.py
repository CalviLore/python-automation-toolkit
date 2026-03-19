# ------------------------------------------------------------------------------
# Questo script genera automaticamente Meta Title e Meta Description SEO
# per i prodotti del catalogo, traducendoli dall'italiano verso una lingua
# target usando l'AI DeepSeek.
#
# I meta tag vengono ottimizzati rispettando i limiti SEO standard:
#   - Meta Title:       massimo 60 caratteri
#   - Meta Description: massimo 155 caratteri con Call To Action (CTA)
#
# Funzionamento:
#   1. Legge meta title e meta description in italiano dal CSV di input
#   2. Elabora più prodotti contemporaneamente (parallelizzazione)
#   3. Salva i risultati in un CSV pronto per l'importazione su PrestaShop
#
# File di input  → productfixmeta.csv
# File di output → import_format_XX_DEEPSEEK_META.csv (es. _es.csv)
#
# 📦 Dipendenze: pandas, openai
# ==============================================================================

import pandas as pd
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

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
FILE_CSV_INPUT = "productfixmeta.csv"   # CSV con meta title e description in italiano
SEPARATORE     = ";"
MAX_WORKERS    = 10                     # Numero di chiamate API simultanee
                                        # Aumentare con cautela per evitare rate limit

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
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, http_client=None)


# ------------------------------------------------------------------------------
# PULIZIA ID PRODOTTO
# ------------------------------------------------------------------------------

def sanifica_id(valore):
    """
    Pulisce l'ID prodotto rimuovendo punti, punto e virgola e spazi.
    Mantiene solo i caratteri numerici.

    Esempio: "1.234;" → "1234"

    Args:
        valore: valore grezzo dell'ID dal CSV

    Returns:
        str: ID numerico pulito, oppure "0" se il valore è vuoto/nullo
    """
    if pd.isna(valore):
        return "0"
    pulito = str(valore).replace('.', '').replace(';', '').strip()
    return "".join(re.findall(r'\d+', pulito))


# ------------------------------------------------------------------------------
# GENERAZIONE META TAG SEO
# ------------------------------------------------------------------------------

def ottimizza_meta(title, desc):
    """
    Invia title e description all'AI DeepSeek e restituisce i meta tag
    tradotti e ottimizzati per il SEO nella lingua target.

    Regole applicate dal modello:
      - Meta Title:       max 60 caratteri
      - Meta Description: max 155 caratteri con CTA finale
      - Output:           formato fisso "Titolo ||| Descrizione"

    In caso di errore API riprova fino a 5 volte con attesa crescente.

    Args:
        title (str): meta title originale in italiano
        desc (str):  meta description originale in italiano

    Returns:
        tuple: (meta_title_tradotto, meta_description_tradotta)
               In caso di fallimento totale restituisce i valori originali.
    """
    if not title and not desc:
        return "", ""

    prompt_sistema = (
        f"Sei un esperto SEO madrelingua {INFO_LINGUA['nome']}. "
        f"Localizza i contenuti per Google {INFO_LINGUA['nome']}."
    )
    prompt_utente = (
        f"Traduci e ottimizza SEO dall'ITALIANO al {INFO_LINGUA['nome'].upper()}:\n"
        f"Titolo Originale: {title}\n"
        f"Descrizione Originale: {desc}\n\n"
        "REGOLE TASSATIVE:\n"
        "1. Title: Max 60 caratteri.\n"
        "2. Description: Max 155 caratteri con CTA.\n"
        "3. OUTPUT: Restituisci SOLO 'Titolo ||| Descrizione'."
    )

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=MODELLO_DEEPSEEK,
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user",   "content": prompt_utente}
                ],
                temperature=0.7,
                timeout=25
            )
            content = response.choices[0].message.content.strip()

            # Il modello risponde nel formato: "Titolo ||| Descrizione"
            if "|||" in content:
                parti = content.split("|||")
                return parti[0].strip(), (parti[1].strip() if len(parti) > 1 else "")

        except Exception:
            time.sleep(2 * (attempt + 1))   # Attesa crescente tra i tentativi

    return title, desc   # Fallback: restituisce i valori originali


# ------------------------------------------------------------------------------
# ELABORAZIONE FILE CSV CON PARALLELIZZAZIONE
# ------------------------------------------------------------------------------

def elabora_meta_ottimizzato():
    """
    Carica il CSV di input, elabora tutti i prodotti in parallelo
    (MAX_WORKERS chiamate API simultanee) e salva il risultato.

    La parallelizzazione riduce drasticamente il tempo di elaborazione
    su cataloghi con centinaia o migliaia di prodotti.

    Output CSV → colonne: id_prod | meta_title_XX | meta_description_XX | idl
    """
    start_time = time.time()
    print(f"--- Caricamento file Meta: {FILE_CSV_INPUT} ---")

    try:
        df = pd.read_csv(FILE_CSV_INPUT, sep=SEPARATORE, encoding='utf-8-sig', dtype=str)
    except Exception as e:
        print(f"❌ Errore apertura file: {e}")
        return

    # Ricerca automatica delle colonne nel CSV
    col_id    = next((c for c in df.columns if "id_prod" in c.lower()), None)
    col_title = next((c for c in df.columns
                      if "meta_title" in c.lower()
                      and not c.lower().endswith(INFO_LINGUA['codice'].lower())), None)
    col_desc  = next((c for c in df.columns
                      if "meta_desc" in c.lower()
                      and not c.lower().endswith(INFO_LINGUA['codice'].lower())), None)

    if not col_id or not col_title:
        print("❌ Errore: colonne necessarie non trovate nel CSV!")
        return

    # Pulizia ID prodotto
    df['id_pulito'] = df[col_id].apply(sanifica_id)

    results = [None] * len(df)
    print(f"🚀 Avvio elaborazione parallela su {len(df)} prodotti ({MAX_WORKERS} thread)...")

    # Elaborazione parallela: MAX_WORKERS prodotti tradotti contemporaneamente
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(ottimizza_meta, row[col_title], row.get(col_desc, "")): i
            for i, row in df.iterrows()
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()
            if (idx + 1) % 10 == 0:
                print(f"📈 Progresso: {idx + 1}/{len(df)}")

    # Costruzione e salvataggio del file di output
    col_code    = INFO_LINGUA["codice"].lower()
    df_final    = pd.DataFrame({
        'id_prod':                       df['id_pulito'],
        f'meta_title_{col_code}':        [r[0] for r in results],
        f'meta_description_{col_code}':  [r[1] for r in results],
        'idl':                           LINGUA_TARGET
    })

    nome_output = f"import_format_{col_code}_DEEPSEEK_META.csv"
    df_final.to_csv(nome_output, index=False, sep=SEPARATORE, encoding='utf-8-sig')

    print(f"\n✅ Completato in {((time.time() - start_time) / 60):.2f} minuti")
    print(f"📁 Salvato come: {nome_output}")


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    elabora_meta_ottimizzato()
