from google_auth import get_sheets_service
from config import SPREADSHEET_ID

def read_financial_data():
    """
    Read financial data from the Google Spreadsheet.
    
    Returns:
        dict: Financial data organized by sheet/category
    """
    service = get_sheets_service()
    
    # Get list of sheets
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    
    data = {}
    for sheet in sheets:
        sheet_name = sheet['properties']['title']
        
        # Read data from each sheet
        range_name = f"{sheet_name}!A:Z"  # Adjust range as needed
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, 
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        data[sheet_name] = values
    
    return data

def update_financial_data(sheet_name, range_name, values):
    """
    Update data in the Google Spreadsheet.
    
    Args:
        sheet_name (str): Name of the sheet to update
        range_name (str): Range to update (e.g., 'A1:C10')
        values (list): 2D list of values to write
    """
    service = get_sheets_service()
    
    full_range = f"{sheet_name}!{range_name}"
    
    body = {
        'values': values
    }
    
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=full_range,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    return result

if __name__ == "__main__":
    # Test the connection
    try:
        data = read_financial_data()
        print("Successfully connected to spreadsheet!")
        print(f"Found {len(data)} sheets:")
        for sheet_name in data.keys():
            print(f"  - {sheet_name}")
    except Exception as e:
        print(f"Error connecting to spreadsheet: {e}")