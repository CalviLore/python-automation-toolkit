# ------------------------------------------------------------------------------
# Prototipo che dimostra l'uso di modelli AI locali (HuggingFace Transformers)
# per tradurre e riscrivere testo in modo automatico, senza API esterne.
#
# Modelli usati:
#   - Helsinki-NLP/opus-mt-it-en  → traduzione Italiano → Inglese
#   - t5-base                     → riscrittura/parafrasi del testo tradotto
#
# 💡 Questo approccio è la base degli script di traduzione prodotti
#    (scriptTitletrad.py, traddesclong.py, traddescbrev.py)
#
# 📦 Dipendenze: transformers, torch
# ==============================================================================

from transformers import pipeline

# Inizializza il modello di traduzione Italiano → Inglese
translator = pipeline(
    "translation",
    model="Helsinki-NLP/opus-mt-it-en"
)

# Inizializza il modello di riscrittura/parafrasi (T5)
paraphraser = pipeline(
    "text2text-generation",
    model="t5-base"
)

# Testo di esempio da tradurre e riscrivere
text_to_translate = "Ciao, come stai?"

# Esegue la traduzione
translated_text = translator(text_to_translate)[0]['translation_text']
print(f"Originale:   {text_to_translate}")
print(f"Traduzione:  {translated_text}")

# Esegue la riscrittura del testo tradotto
paraphrased_text = paraphraser(
    f"paraphrase: {translated_text}",
    max_length=100
)[0]['generated_text']
print(f"Riscrittura: {paraphrased_text}")