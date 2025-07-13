from google_auth import get_sheets_service

SPREADSHEET_ID = '1c93Nr0XyeAzT0tAVlkna78gp8mM_8NWiTgmxlQJ9Wko'

def test_basic_access():
    """Test basic spreadsheet access with minimal API calls."""
    try:
        service = get_sheets_service()
        print("✓ Google Sheets service created successfully")
        
        # Try to get basic spreadsheet info
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        print("✓ Spreadsheet accessed successfully")
        print(f"Title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        
        # List sheets
        sheets = spreadsheet.get('sheets', [])
        print(f"✓ Found {len(sheets)} sheets:")
        for sheet in sheets:
            sheet_name = sheet['properties']['title']
            print(f"  - {sheet_name}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_basic_access()