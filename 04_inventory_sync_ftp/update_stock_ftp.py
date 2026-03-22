# Questo script aggiorna automaticamente le giacenze di magazzino su PrestaShop.
# Funzionamento:
#   1. Scarica via FTP il file CSV con le giacenze aggiornate dal fornitore
#   2. Legge il CSV e per ogni prodotto/taglia cerca il codice articolo nel DB
#   3. Aggiorna la quantità disponibile su PrestaShop tramite API REST
#
# 📁 Cartella: 04_inventory_sync_ftp/
# 📦 Dipendenze: ftputil, mysql.connector, csv, os, requests
# ==============================================================================

import ftputil
import mysql.connector
import csv
import os
import requests

# ------------------------------------------------------------------------------
# CONFIGURAZIONE FTP
# ⚠️ Non condividere mai queste credenziali pubblicamente!
# ------------------------------------------------------------------------------
FTP_HOST     = "IL_TUO_HOST_FTP"       # Es. "ftp.tuofornitore.com"
FTP_USER     = "IL_TUO_UTENTE_FTP"     # Username FTP
FTP_PASSWORD = "LA_TUA_PASSWORD_FTP"   # Password FTP

# ------------------------------------------------------------------------------
# CONFIGURAZIONE PRESTASHOP API
# ⚠️ Non condividere mai queste credenziali pubblicamente!
# ------------------------------------------------------------------------------
SHOP_URL = "https://tuosito.com/api"   # URL delle API del tuo negozio
API_KEY  = "LA_TUA_API_KEY"            # API key di PrestaShop

# Nome del file CSV delle giacenze scaricato via FTP
FILE_GIACENZE = "giacenze.csv"

# Prefisso usato per costruire la referenza articolo
# Formato: <PREFISSO><codice>/<colore>/<taglia>  es. "ART001/NERO/M"
# Sostituisci con il prefisso usato nel tuo catalogo
PREFISSO_REFERENZA = "IL_TUO_PREFISSO"


# ------------------------------------------------------------------------------
# CONNESSIONE FTP E DOWNLOAD FILE GIACENZE
# ------------------------------------------------------------------------------

def connectionFtp():
    """
    Si connette al server FTP del fornitore, cerca il file delle giacenze
    (giacenze.csv) e lo scarica in locale, sovrascrivendo il precedente.
    """
    # Rimuove il file precedente prima di scaricarne uno nuovo
    if os.path.exists(FILE_GIACENZE):
        os.remove(FILE_GIACENZE)

    # Connessione al server FTP
    a_host = ftputil.FTPHost(FTP_HOST, FTP_USER, FTP_PASSWORD)

    # Scansiona tutte le directory FTP alla ricerca del file
    for (dirname, subdirs, files) in a_host.walk("/"):
        for f in files:
            if FILE_GIACENZE in f:
                a_host.download(f, f)  # Scarica il file in locale
                print(f"✅ File scaricato: {f}")
                break


# ------------------------------------------------------------------------------
# AGGIORNAMENTO QUANTITÀ SU PRESTASHOP
# ------------------------------------------------------------------------------

def insertQuantit(id_product_attribute, quant):
    """
    Aggiorna la quantità disponibile di una variante prodotto su PrestaShop.

    Passaggi:
      1. Recupera l'ID dello stock disponibile per la combinazione prodotto
      2. Invia una richiesta PUT con la nuova quantità tramite XML

    Args:
        id_product_attribute (int): ID della combinazione prodotto (es. taglia/colore)
        quant (int):                nuova quantità da impostare
    """
    # Recupera l'ID dello stock disponibile per questa combinazione
    response = requests.get(
        f'{SHOP_URL}/stock_availables',
        params={
            'display': 'id',
            'filter[id_product_attribute]': id_product_attribute
        },
        auth=(API_KEY, '')
    )

    stock_available_id = response.json()['stock_availables']['stock_available']['id']

    # Costruisce il corpo XML per aggiornare la quantità
    xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
    <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <stock_available>
            <id><![CDATA[{stock_available_id}]]></id>
            <id_product_attribute><![CDATA[{id_product_attribute}]]></id_product_attribute>
            <quantity><![CDATA[{quant}]]></quantity>
            <depends_on_stock><![CDATA[0]]></depends_on_stock>
            <out_of_stock><![CDATA[2]]></out_of_stock>  <!-- 2 = accetta ordini anche se esaurito -->
        </stock_available>
    </prestashop>
    '''

    # Invia la richiesta di aggiornamento
    response = requests.put(
        f'{SHOP_URL}/stock_availables/{stock_available_id}',
        headers={'Content-Type': 'application/xml'},
        auth=(API_KEY, ''),
        data=xml_body
    )

    if response.status_code == 200:
        print(f"✅ Quantità aggiornata per variante {id_product_attribute}: {quant} pz")
    else:
        print(f"❌ Errore aggiornamento variante {id_product_attribute}: {response.status_code}")


# ------------------------------------------------------------------------------
# LETTURA FILE CSV E AVVIO AGGIORNAMENTI
# ------------------------------------------------------------------------------

def readfile():
    """
    Legge il file CSV delle giacenze e aggiorna le quantità su PrestaShop.

    Struttura del CSV (separatore ';'):
      - Riga 0-1: intestazioni da saltare
      - Colonna 0: codice prodotto
      - Colonna 2: colore
      - Colonne 3-10: quantità per taglia (XS, S, M, L, XL, XXL, 3XL, 4XL)

    Per ogni prodotto e taglia costruisce la referenza articolo nel formato:
      <PREFISSO_REFERENZA><codice>/<colore>/<taglia>
      Es. "ART001/NERO/M"
    e cerca l'ID corrispondente nel database per aggiornare la quantità.
    """
    taglie = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL']

    with open(FILE_GIACENZE, encoding='ISO-8859-1') as stan_file:
        reader = csv.reader(stan_file, delimiter=';')
        next(reader)  # Salta la prima riga di intestazione
        next(reader)  # Salta la seconda riga di intestazione

        for row in reader:
            if not row:
                continue  # Salta le righe vuote

            colore = row[2]

            for i, taglia in enumerate(taglie):
                # Costruisce la referenza univoca nel formato <PREFISSO><codice>/<colore>/<taglia>
                ref = f"{PREFISSO_REFERENZA}{row[0]}/{colore}/{taglia}"
                quantita = row[i + 3]

                # Cerca l'ID della variante nel database tramite la referenza
                id_product_attribute = findIdref(ref)

                if not id_product_attribute:
                    continue  # Salta se la referenza non è presente nel catalogo

                # Aggiorna la quantità su PrestaShop
                insertQuantit(id_product_attribute[0][0], quantita)


# ------------------------------------------------------------------------------
# PUNTO DI AVVIO DELLO SCRIPT
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    print("🔄 Avvio download giacenze via FTP...")
    connectionFtp()
    print("🔄 Avvio aggiornamento quantità su PrestaShop...")
    readfile()
    print("✅ Aggiornamento giacenze completato.")
