from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_google_services():
    """
    Initialize and return Google API service objects for Docs, Sheets, and Drive.
    
    Returns:
        tuple: (docs_service, sheets_service, drive_service)
    """
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    credentials = service_account.Credentials.from_service_account_file(
        'google_credentials.json', scopes=SCOPES
    )
    
    docs_service = build('docs', 'v1', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    
    return docs_service, sheets_service, drive_service

def get_sheets_service():
    """
    Get just the Sheets service for spreadsheet operations.
    
    Returns:
        Resource: Google Sheets API service object
    """
    docs_service, sheets_service, drive_service = get_google_services()
    return sheets_service