# main.py
import os
import logging
from telegram import Update, ForceReply, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google_sheets_api import GoogleSheetsAPI
import asyncio # Import asyncio for async operations

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inisialisasi Google Sheets API
# Sekarang tidak lagi merujuk ke 'credentials.json' secara langsung di sini
try:
    # Parameter pertama (credentials_path) diset None, karena akan diambil dari environment variable
    sheets_api = GoogleSheetsAPI(None, 'Data Sales Check-in Bot')
except Exception as e:
    logger.error(f"Error initializing GoogleSheetsAPI: {e}")
    sheets_api = None # Set to None if initialization fails

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan sambutan saat perintah /start diberikan."""
    user = update.effective_user
    await update.message.reply_html(
        f"Halo {user.mention_html()}! Saya adalah bot Sales Check-in. "
        "Gunakan perintah berikut:\n"
        "/reg - Untuk mendaftar sebagai sales\n"
        "/checkin - Untuk memulai check-in di toko\n"
        "/checkout - Untuk menyelesaikan check-out dari toko"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Memproses pendaftaran sales baru."""
    user_id = str(update.effective_user.id)
    username = update.effective_user.username if update.effective_user.username else update.effective_user.first_name

    if sheets_api is None:
        await update.message.reply_text("Bot sedang mengalami masalah internal (integrasi Google Sheets). Mohon coba lagi nanti.")
        return

    # Cek apakah user sudah terdaftar
    users_data = await sheets_api.get_all_users()
    if any(user_id == row[0] for row in users_data if row): # Pastikan baris tidak kosong
        await update.message.reply_text("Kamu sudah terdaftar.")
        return

    # Kirim notifikasi ke admin (ganti dengan ID admin sebenarnya)
    admin_id = os.getenv("ADMIN_TELEGRAM_ID") # Ambil dari environment variable
    if admin_id:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"Pending user: {user_id} - {username}\n"
                     f"Untuk menyetujui, balas dengan: /approve {user_id} <nama_sales_alias> <cabang>"
            )
            await update.message.reply_text("Permintaan pendaftaranmu telah dikirim ke admin. Mohon tunggu persetujuan.")
        except Exception as e:
            logger.error(f"Could not send message to admin {admin_id}: {e}")
            await update.message.reply_text("Terjadi kesalahan saat mengirim permintaan ke admin. Mohon coba lagi nanti.")
    else:
        await update.message.reply_text("Admin ID belum dikonfigurasi di server. Pendaftaran tidak dapat diproses.")


async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menyetujui pendaftaran user oleh admin/owner."""
    user_id = str(update.effective_user.id)

    if sheets_api is None:
        await update.message.reply_text("Bot sedang mengalami masalah internal (integrasi Google Sheets). Mohon coba lagi nanti.")
        return

    # Cek role user
    user_role = await sheets_api.get_user_role(user_id)
    if user_role not in ['owner', 'admin']:
        await update.message.reply_text("Maaf, kamu tidak memiliki izin untuk menggunakan perintah ini.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Format salah. Gunakan: /approve <id_telegram> <nama_sales_alias> <cabang>")
        return

    target_user_id = args[0]
    alias = args[1]
    cabang = args[2]

    try:
        await sheets_api.add_user(target_user_id, alias, cabang, 'user')
        await update.message.reply_text(f"User **{alias}** (ID: `{target_user_id}`) berhasil disetujui dan ditambahkan.", parse_mode='Markdown')
        # Beri tahu user yang disetujui
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Selamat! Akunmu telah disetujui oleh admin. Kamu sekarang bisa menggunakan bot ini."
            )
        except Exception as e:
            logger.warning(f"Could not notify approved user {target_user_id}: {e}")
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        await update.message.reply_text(f"Terjadi kesalahan saat menyetujui user: {e}")

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Memulai proses check-in."""
    user_id = str(update.effective_user.id)

    if sheets_api is None:
        await update.message.reply_text("Bot sedang mengalami masalah internal (integrasi Google Sheets). Mohon coba lagi nanti.")
        return

    user_data = await sheets_api.get_user_by_id(user_id)
    if not user_data:
        await update.message.reply_text("Kamu belum terdaftar. Silakan gunakan perintah /reg untuk mendaftar.")
        return

    # Cek apakah user sudah check-in tapi belum check-out
    open_checkin = await sheets_api.get_open_checkin(user_id)
    if open_checkin:
        await update.message.reply_text("Kamu sudah melakukan check-in dan belum check-out. Silakan gunakan /checkout terlebih dahulu.")
        return

    # Simpan state untuk check-in
    context.user_data['state'] = 'awaiting_store_info'
    await update.message.reply_text(
        "Oke, silakan ketik **nama toko & daerah** (contoh: *Toko Abadi, Kandangan*). "
        "Setelah itu, klik tombol **'Share Location'** di bawah untuk membagikan lokasimu."
    )

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Memulai proses check-out."""
    user_id = str(update.effective_user.id)

    if sheets_api is None:
        await update.message.reply_text("Bot sedang mengalami masalah internal (integrasi Google Sheets). Mohon coba lagi nanti.")
        return

    user_data = await sheets_api.get_user_by_id(user_id)
    if not user_data:
        await update.message.reply_text("Kamu belum terdaftar. Silakan gunakan perintah /reg untuk mendaftar.")
        return

    open_checkin = await sheets_api.get_open_checkin(user_id)
    if not open_checkin:
        await update.message.reply_text("Kamu belum melakukan check-in. Silakan gunakan /checkin terlebih dahulu.")
        return

    # Simpan state untuk check-out
    context.user_data['state'] = 'awaiting_checkout_info'
    await update.message.reply_text(
        "Oke, silakan isi formulir check-out dengan format:\n"
        "**Bertemu**: <bertemu dengan siapa>\n"
        "**Order**: <jumlah order atau '-'>\n"
        "**Tagihan**: <jumlah tagihan atau '-'>\n"
        "**Kendala**: <kendala yang dihadapi atau '-'>\n\n"
        "*Contoh:*\n"
        "Bertemu: Pak Budi\n"
        "Order: 150000\n"
        "Tagihan: 100000\n"
        "Kendala: Tidak ada"
    )

# --- Message Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani pesan teks dan lokasi."""
    user_id = str(update.effective_user.id)
    current_state = context.user_data.get('state')

    if sheets_api is None:
        await update.message.reply_text("Bot sedang mengalami masalah internal (integrasi Google Sheets). Mohon coba lagi nanti.")
        return

    if current_state == 'awaiting_store_info':
        if update.message.text:
            context.user_data['store_info'] = update.message.text
            # Minta lokasi setelah info toko
            keyboard = [[KeyboardButton("Share Location", request_location=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                "Sekarang, silakan klik tombol **'Share Location'** di bawah untuk membagikan lokasimu.",
                reply_markup=reply_markup
            )
        elif update.message.location:
            store_info = context.user_data.get('store_info')
            if not store_info:
                # Ini bisa terjadi jika user langsung share lokasi tanpa info toko
                await update.message.reply_text("Mohon berikan nama toko & daerah terlebih dahulu sebelum membagikan lokasi. Silakan ulangi /checkin.")
                del context.user_data['state']
                if 'store_info' in context.user_data: del context.user_data['store_info']
                return

            nama_toko, daerah = store_info.split(',', 1) if ',' in store_info else (store_info.strip(), '')
            nama_toko = nama_toko.strip()
            daerah = daerah.strip()

            latitude = update.message.location.latitude
            longitude = update.message.location.longitude
            # Link Google Maps yang benar
            Maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            timestamp_checkin = update.message.date.strftime("%Y-%m-%d %H:%M:%S")

            user_data = await sheets_api.get_user_by_id(user_id)
            if not user_data:
                await update.message.reply_text("Terjadi kesalahan: data user tidak ditemukan. Silakan coba /reg lagi.")
                del context.user_data['state']
                if 'store_info' in context.user_data: del context.user_data['store_info']
                return

            # Pastikan user_data memiliki cukup elemen
            sales_alias = user_data[1] if len(user_data) > 1 else 'N/A'
            cabang = user_data[2] if len(user_data) > 2 else 'N/A'

            try:
                await sheets_api.add_checkin_data(
                    user_id, sales_alias, cabang, nama_toko, daerah, Maps_link, timestamp_checkin
                )
                await update.message.reply_text("✅ Check-in berhasil dicatat!")
            except Exception as e:
                logger.error(f"Error adding check-in data: {e}")
                await update.message.reply_text(f"❌ Terjadi kesalahan saat mencatat check-in: {e}")

            # Reset state
            del context.user_data['state']
            if 'store_info' in context.user_data:
                del context.user_data['store_info']

        else:
            await update.message.reply_text("Mohon berikan **nama toko & daerah** atau **bagikan lokasi**.")

    elif current_state == 'awaiting_checkout_info':
        if update.message.text:
            try:
                lines = update.message.text.split('\n')
                checkout_data = {}
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        checkout_data[key.strip().lower()] = value.strip()

                bertemu = checkout_data.get('bertemu', '-')
                order = checkout_data.get('order', '-')
                tagihan = checkout_data.get('tagihan', '-')
                kendala = checkout_data.get('kendala', '-')
                timestamp_checkout = update.message.date.strftime("%Y-%m-%d %H:%M:%S")

                await sheets_api.update_checkout_data(
                    user_id, timestamp_checkout, order, tagihan, kendala
                )
                await update.message.reply_text("✅ Check-out berhasil dicatat!")
            except Exception as e:
                logger.error(f"Error processing checkout data: {e}")
                await update.message.reply_text(f"❌ Terjadi kesalahan atau format check-out salah: {e}\n"
                                                 "Pastikan formatnya:\n"
                                                 "**Bertemu**: <siapa>\n"
                                                 "**Order**: <jumlah>\n"
                                                 "**Tagihan**: <jumlah>\n"
                                                 "**Kendala**: <deskripsi>")
            finally:
                # Reset state
                del context.user_data['state']
        else:
            await update.message.reply_text("Mohon isi formulir check-out dengan lengkap.")
    else:
        # Default response if no specific state
        await update.message.reply_text("Saya tidak mengerti perintahmu. Gunakan /start untuk melihat opsi.")


# --- Main Function ---

def main() -> None:
    """Menjalankan bot."""
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        raise ValueError("TELEGRAM_BOT_TOKEN is required.")

    application = Application.builder().token(telegram_token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reg", register))
    application.add_handler(CommandHandler("approve", approve_user))
    application.add_handler(CommandHandler("checkin", checkin))
    application.add_handler(CommandHandler("checkout", checkout))

    # Message handler (untuk teks dan lokasi)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.LOCATION, handle_message))


    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started. Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Ensure sheets_api is initialized before running main
    if sheets_api:
        main()
    else:
        logger.error("Google Sheets API not initialized. Exiting.")