import os
import sys # Pastikan sys sudah diimpor
import logging # Pastikan logging sudah diimpor
import base64 # Tambahkan ini
import json # Pastikan json sudah diimpor
from google_sheets_api import GoogleSheetsAPI # Pastikan ini benar

# ... definisikan BOT_TOKEN, ADMIN_TELEGRAM_ID, dll. di sini ...
# Pastikan BOT_TOKEN dan ADMIN_TELEGRAM_ID juga diambil dari environment variables
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID') # Ini akan menjadi string, bukan integer
if ADMIN_TELEGRAM_ID:
    try:
        ADMIN_TELEGRAM_ID = int(ADMIN_TELEGRAM_ID)
    except ValueError:
        logging.error("ADMIN_TELEGRAM_ID in environment variable is not a valid integer.")
        ADMIN_TELEGRAM_ID = None

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Inisialisasi GoogleSheetsAPI dari environment variable
google_sheets_api = None
if os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO'):
    try:
        # Ambil nilai Base64, hapus awalan 'base64:' jika ada
        base64_string = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
        if base64_string.startswith('base64:'):
            base64_string = base64_string[7:] # Hapus "base64:"

        # Decode string Base64 dari environment variable
        decoded_credentials_json = base64.b64decode(base64_string).decode('utf-8')
        # Muat string JSON yang sudah di-decode menjadi objek Python (dictionary)
        credentials_info = json.loads(decoded_credentials_json)
        google_sheets_api = GoogleSheetsAPI(credentials_info)
        logging.info("Google Sheets credentials loaded from environment variable (decoded Base64).")
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON from GOOGLE_SERVICE_ACCOUNT_INFO: {e}")
        google_sheets_api = None
    except Exception as e:
        logging.error(f"Error decoding or loading Google Sheets credentials from environment variable: {e}")
        google_sheets_api = None
else:
    logging.error("GOOGLE_SERVICE_ACCOUNT_INFO environment variable is not set.")
    google_sheets_api = None

# Periksa apakah GoogleSheetsAPI berhasil diinisialisasi
if not google_sheets_api or not google_sheets_api.service:
    logging.error("Google Sheets API not initialized. Exiting.")
    sys.exit(1)

# ... sisa kode botmu (bot = Bot(token=BOT_TOKEN), updater, dispatcher, handler, dll.)
# Pastikan bagian bot Telegram juga ada di sini

# Contoh penggunaan GoogleSheetsAPI (pastikan ini ada jika botmu menggunakannya)
# Misalnya, di fungsi start:
# def start(update: Update, context: CallbackContext) -> None:
#     try:
#         worksheet = google_sheets_api.get_worksheet("Nama_Spreadsheet_mu", "Nama_Worksheet_mu")
#         if worksheet:
#             # Lakukan sesuatu dengan worksheet
#             update.message.reply_text("Halo! Bot Salesbot sudah aktif dan terhubung ke Google Sheets.")
#         else:
#             update.message.reply_text("Halo! Bot Salesbot aktif, tapi gagal terhubung ke Google Sheets. Mohon cek log.")
#     except Exception as e:
#         logging.error(f"Error in start command: {e}")
#         update.message.reply_text("Terjadi kesalahan saat memulai bot. Mohon coba lagi nanti.")

# ... bagian akhir main.py (updater.start_polling(), dll.)
logging.info("Bot started. Press Ctrl-C to stop.")
updater.start_polling()
updater.idle()