# google_sheets_api.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsAPI:
    def __init__(self, credentials_path, spreadsheet_name):
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, self.scope)
        self.client = gspread.authorize(self.creds)
        self.spreadsheet = self.client.open(spreadsheet_name)
        self.sales_data_sheet = self.spreadsheet.worksheet("Sales_Data")
        self.users_sheet = self.spreadsheet.worksheet("users")
        logger.info(f"Successfully connected to Google Sheet: {spreadsheet_name}")

    async def add_user(self, user_id, alias, cabang, role):
        """Menambahkan user baru ke sheet 'users'."""
        try:
            self.users_sheet.append_row([user_id, alias, cabang, role])
            logger.info(f"User {alias} (ID: {user_id}) added to 'users' sheet.")
        except Exception as e:
            logger.error(f"Error adding user to 'users' sheet: {e}")
            raise

    async def get_all_users(self):
        """Mengambil semua data user dari sheet 'users'."""
        try:
            return self.users_sheet.get_all_values()
        except Exception as e:
            logger.error(f"Error getting all users from 'users' sheet: {e}")
            return []

    async def get_user_by_id(self, user_id):
        """Mencari user berdasarkan ID di sheet 'users'."""
        try:
            users_data = self.users_sheet.get_all_values()
            for row in users_data:
                if row and row[0] == user_id:
                    return row
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    async def get_user_role(self, user_id):
        """Mendapatkan role user berdasarkan ID."""
        user_data = await self.get_user_by_id(user_id)
        if user_data and len(user_data) > 3:
            return user_data[3] # Kolom 'role'
        return None

    async def add_checkin_data(self, user_id, sales_alias, cabang, nama_toko, daerah, google_maps_link, timestamp_checkin):
        """Menambahkan data check-in ke sheet 'Sales_Data'."""
        try:
            row = [user_id, sales_alias, cabang, nama_toko, daerah, google_maps_link, timestamp_checkin, '', '', '', '']
            self.sales_data_sheet.append_row(row)
            logger.info(f"Check-in data added for user {user_id}.")
        except Exception as e:
            logger.error(f"Error adding check-in data: {e}")
            raise

    async def get_open_checkin(self, user_id):
        """Mencari check-in yang belum di-checkout."""
        try:
            data = self.sales_data_sheet.get_all_values()
            # Mencari dari bawah ke atas untuk check-in terbaru
            for i in range(len(data) - 1, 0, -1): # Lewati header (row 0)
                row = data[i]
                if len(row) > 0 and row[0] == user_id: # Kolom ID
                    if len(row) < 8 or not row[7]: # Kolom Timestamp checkout (index 7) kosong
                        return i + 1 # Mengembalikan nomor baris (1-indexed)
            return None
        except Exception as e:
            logger.error(f"Error getting open check-in for user {user_id}: {e}")
            return None

    async def update_checkout_data(self, user_id, timestamp_checkout, order, tagihan, kendala):
        """Memperbarui data check-out di sheet 'Sales_Data'."""
        row_index = await self.get_open_checkin(user_id)
        if not row_index:
            raise ValueError("Tidak ada check-in yang terbuka untuk user ini.")

        try:
            # Update kolom CHECKOUT (index 7), ORDER (index 8), TAGIHAN (index 9), KENDALA (index 10)
            self.sales_data_sheet.update_cell(row_index, 8, timestamp_checkout) # Kolom CHECKOUT (index 7, tapi gspread 1-indexed)
            self.sales_data_sheet.update_cell(row_index, 9, order) # Kolom ORDER (index 8)
            self.sales_data_sheet.update_cell(row_index, 10, tagihan) # Kolom TAGIHAN (index 9)
            self.sales_data_sheet.update_cell(row_index, 11, kendala) # Kolom KENDALA (index 10)
            logger.info(f"Check-out data updated for user {user_id} at row {row_index}.")
        except Exception as e:
            logger.error(f"Error updating check-out data for user {user_id} at row {row_index}: {e}")
            raise