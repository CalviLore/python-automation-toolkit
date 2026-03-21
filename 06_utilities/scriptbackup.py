# Questo script esegue un backup automatico delle cartelle principali
# dell'utente (Scrivania, Documenti, Download, Musica, Foto, Video)
# copiandole in una cartella di archivio con data e ora nel nome.
#
# Pensato per essere usato anche da utenti non tecnici:
#   - Mostra una barra di avanzamento durante la copia
#   - Genera un file di log leggibile in caso di errori
#   - Funziona sia lanciato come script Python che come .exe compilato
#
# Funzionamento:
#   1. Rileva automaticamente la posizione dello script (o dell'eseguibile)
#   2. Crea una cartella "I miei Backup del PC / Copia del GG-MM-AAAA_ore_HH-MM"
#   3. Conta tutti i file da copiare e mostra la barra di avanzamento
#   4. Copia ogni cartella utente mantenendo la struttura originale
#   5. In caso di errori (file aperti, permessi) li registra nel log
#
# 📦 Dipendenze: tqdm
#
# Installazione:
#     pip install tqdm
# ==============================================================================

import os
import shutil
import sys
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm


def avvia_backup_solido():
    """
    Esegue il backup completo delle cartelle utente principali.

    Struttura cartella di output:
        <posizione_script>/
        └── I miei Backup del PC/
            └── Copia del GG-MM-AAAA_ore_HH-MM/
                ├── Scrivania/
                ├── Documenti/
                ├── Download/
                ├── Musica/
                ├── Foto/
                └── Video/

    I file che non possono essere copiati (es. aperti da altri programmi)
    vengono saltati e registrati nel file 'Leggi_se_ci_sono_problemi.txt'.
    """

    # ------------------------------------------------------------------
    # STEP 1 — Rileva la posizione dello script
    # Funziona sia come script .py che come eseguibile .exe (PyInstaller)
    # ------------------------------------------------------------------
    if getattr(sys, 'frozen', False):
        percorso_disco = Path(sys.executable).parent   # Modalità .exe
    else:
        percorso_disco = Path(__file__).parent          # Modalità .py

    # ------------------------------------------------------------------
    # STEP 2 — Prepara i percorsi di output
    # ------------------------------------------------------------------
    data_ora      = datetime.now().strftime("%d-%m-%Y_ore_%H-%M")
    archivio      = percorso_disco / "I miei Backup del PC"
    cartella_oggi = archivio / f"Copia del {data_ora}"
    diario_file   = percorso_disco / "Leggi_se_ci_sono_problemi.txt"

    # ------------------------------------------------------------------
    # STEP 3 — Configura il file di log per gli errori
    # Il log viene scritto in italiano per essere leggibile da chiunque
    # ------------------------------------------------------------------
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        handlers=[logging.FileHandler(diario_file, encoding='utf-8')]
    )

    # ------------------------------------------------------------------
    # STEP 4 — Definisce le cartelle da copiare
    # Usa Path.home() per trovare automaticamente la cartella utente
    # (es. C:\Users\Mario su Windows, /home/mario su Linux/Mac)
    # ------------------------------------------------------------------
    utente    = Path.home()
    obiettivi = {
        "Scrivania": utente / "Desktop",
        "Documenti": utente / "Documents",
        "Download":  utente / "Downloads",
        "Musica":    utente / "Music",
        "Foto":      utente / "Pictures",
        "Video":     utente / "Videos"
    }

    # ------------------------------------------------------------------
    # STEP 5 — Conta i file totali per la barra di avanzamento
    # ------------------------------------------------------------------
    print("🔍 Analisi dei file in corso... Attendi.")
    tutti_i_file = []
    for nome, path in obiettivi.items():
        if path.exists():
            try:
                tutti_i_file.extend(list(path.rglob('*')))
            except Exception:
                pass

    totale = len(tutti_i_file)
    print(f"📦 Trovati {totale} elementi da salvare.\n")

    # ------------------------------------------------------------------
    # STEP 6 — Copia i file con barra di avanzamento
    # shutil.copy2 preserva anche le date di modifica originali dei file
    # ------------------------------------------------------------------
    errori_riscontrati = False

    with tqdm(total=totale, desc="Progresso", unit="file") as pbar:
        for nome_cat, sorgente in obiettivi.items():
            if not sorgente.exists():
                continue

            # Crea la sottocartella di destinazione
            cat_dest = cartella_oggi / nome_cat
            cat_dest.mkdir(parents=True, exist_ok=True)

            for elemento in sorgente.rglob('*'):
                relativo = elemento.relative_to(sorgente)
                finale   = cat_dest / relativo
                try:
                    if elemento.is_dir():
                        finale.mkdir(exist_ok=True)
                    else:
                        shutil.copy2(elemento, finale)  # Copia preservando metadata
                except Exception:
                    errori_riscontrati = True
                    logging.error(f"File saltato (probabilmente in uso): {elemento}")

                pbar.update(1)

    # ------------------------------------------------------------------
    # STEP 7 — Messaggio finale
    # ------------------------------------------------------------------
    print("\n" + "=" * 40)
    print("✅ SALVATAGGIO TERMINATO")
    if errori_riscontrati:
        print(f"⚠️  Alcuni file non sono stati copiati.")
        print(f"   Consulta '{diario_file.name}' per i dettagli.")
    else:
        print("🎉 Tutto è stato copiato correttamente!")
    print("=" * 40)

    input("\nPremi INVIO per chiudere...")


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    avvia_backup_solido()