# 🤖 ai/ — Script di Traduzione Automatica con AI

Questa cartella contiene gli script per la traduzione automatica dei contenuti
del catalogo prodotti usando il modello **DeepSeek AI** (compatibile con le API OpenAI).

Tutti gli script sono ottimizzati per il settore **DPI (Dispositivi di Protezione
Individuale)**: mantengono le sigle di sicurezza (S1P, S3, SRC, ESD...), non
traducono i brand e usano la terminologia tecnica corretta.

---

## 📋 Flusso consigliato

Gli script vanno eseguiti in questo ordine per completare la traduzione
di un catalogo PrestaShop:
```
1. scriptTitletrad.py   →  Traduce i nomi prodotto (H1)
2. scriptmetatag.py     →  Genera Meta Title e Meta Description SEO
3. traddescbrev.py      →  Traduce le descrizioni brevi (HTML)
4. traddesclong.py      →  Traduce le descrizioni lunghe (HTML)
```

---

## 📁 Script

| Script | Input | Output | Note |
|---|---|---|---|
| `scriptTitletrad.py` | `productfixmeta.csv` | `h1_mancanti_XX.csv` | Sequenziale, log dettagliato |
| `scriptmetatag.py` | `productfixmeta.csv` | `import_format_XX_DEEPSEEK_META.csv` | Parallelo, regole SEO strict |
| `traddescbrev.py` | `proddescbrv.csv` | `import_tradotto_descbrv_XX.csv` | Parallelo, HTML→MD→HTML |
| `traddesclong.py` | `proddesclng.csv` | `import_tradotto_desclng_XX.csv` | Parallelo, backup ogni 50 |

Il suffisso `XX` nel nome del file di output corrisponde al codice lingua
(es. `_fr`, `_de`, `_es`, `_en`).

---

## ⚙️ Configurazione

In ogni script è sufficiente modificare due parametri prima di avviarlo:
```python
# Lingua di destinazione
LINGUA_TARGET = "3"   # "2"=EN  "3"=FR  "4"=DE  "5"=ES

# API key DeepSeek (https://platform.deepseek.com)
DEEPSEEK_API_KEY = "LA_TUA_API_KEY"
```

---

## 📦 Installazione dipendenze
```bash
pip install pandas openai markdown markdownify
```

---

## 🔑 API Key

Gli script usano le API di **DeepSeek** per la traduzione.
Per ottenere una API key gratuita: https://platform.deepseek.com

> ⚠️ Non committare mai la API key nel repository.
> Usa una variabile d'ambiente o un file `.env` per gestirla in produzione.

---

## 🧪 Prototipo

La cartella contiene anche `test_translation_pipeline.py`, un prototipo
che dimostra la traduzione con modelli **HuggingFace locali** (senza API esterne),
usato come base di studio prima di integrare DeepSeek.
```
docs(ai): add README explaining AI translation scripts and workflow

- Documents recommended execution order for full catalog translation
- Lists input/output files and key differences for each script
- Explains LINGUA_TARGET and API key configuration
- Adds installation instructions for required dependencies
- Notes prototype script for local HuggingFace pipeline
