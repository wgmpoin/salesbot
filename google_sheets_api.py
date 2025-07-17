import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import json

class GoogleSheetsAPI:
    def __init__(self, credentials_data):
        self.service = None
        try:
            # Pastikan credentials_data adalah dictionary
            if isinstance(credentials_data, dict):
                scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                # Menggunakan from_json_keyfile_dict karena kita sudah punya data dalam bentuk dict
                creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_data, scope)
                self.service = gspread.authorize(creds)
                logging.info("Google Sheets API initialized successfully from dictionary data.")
            else:
                logging.error(f"Error: Invalid credentials_data type for GoogleSheetsAPI. Expected dict, got {type(credentials_data)}")
                self.service = None
        except Exception as e:
            logging.error(f"Error initializing GoogleSheetsAPI: {e}")
            self.service = None

    def get_spreadsheet(self, spreadsheet_name):
        if not self.service:
            logging.error("Google Sheets API service is not initialized.")
            return None
        try:
            spreadsheet = self.service.open(spreadsheet_name)
            logging.info(f"Spreadsheet '{spreadsheet_name}' opened successfully.")
            return spreadsheet
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Spreadsheet '{spreadsheet_name}' not found.")
            return None
        except Exception as e:
            logging.error(f"Error opening spreadsheet '{spreadsheet_name}': {e}")
            return None

    # Tambahkan fungsi-fungsi lain yang kamu butuhkan untuk berinteraksi dengan Google Sheets di sini
    # Contoh:
    def get_worksheet(self, spreadsheet_name, worksheet_name):
        spreadsheet = self.get_spreadsheet(spreadsheet_name)
        if spreadsheet:
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                logging.info(f"Worksheet '{worksheet_name}' in '{spreadsheet_name}' opened successfully.")
                return worksheet
            except gspread.exceptions.WorksheetNotFound:
                logging.error(f"Worksheet '{worksheet_name}' not found in '{spreadsheet_name}'.")
                return None
            except Exception as e:
                logging.error(f"Error opening worksheet '{worksheet_name}': {e}")
                return None