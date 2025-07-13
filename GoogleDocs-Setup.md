# Google Docs Setup Instructions

This document provides instructions for setting up Google Docs/Sheets API access to allow automated reading and writing of financial tracking data. 

## Phase 1: Google Cloud Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "Financial-Asset-Tracking"
3. Note the project ID for reference

### 2. Enable Required APIs

Navigate to APIs & Services → Library and enable:

- **Google Docs API** - For document creation/editing
- **Google Drive API** - For document creation and management
- **Google Sheets API** - For spreadsheet access

1. Go to IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Name: "financial-tracking-service"
4. Description: "Service account for automated financial data access"
5. Click "Create and Continue"
6. Skip role assignment (optional step)
7. Click "Done"

### 4. Generate Credentials

1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Download the file
6. Rename to `google_credentials.json`
7. Save in your project directory
8. **Important**: Add `google_credentials.json` to `.gitignore`

## Phase 2: Python Setup

### 1. Install Dependencies

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### 2. Create Authentication Module

Create `google_auth.py`:

```python
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
```

## Phase 3: Spreadsheet Access Setup

### 1. Share Your Spreadsheet

1. Open your spreadsheet
2. Click "Share" button
3. Add the service account email (found in the downloaded JSON credentials file)
4. Give it "Editor" permissions
5. Click "Send"

### 2. Extract Spreadsheet ID

From your spreadsheet URL:
```
https://docs.google.com/spreadsheets/d/<SPREADSHEET-ID>/edit...
```

## Phase 4: Implementation

### 1. Create Data Access Script

Create `financial_data_access.py`:

```python
from google_auth import get_sheets_service

SPREADSHEET_ID = 'your_spreadsheet_id_here'

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
```

## Security Considerations

### Important Security Notes

1. **Keep Credentials Private**
   - Never commit `google_credentials.json` to version control
   - Add to `.gitignore` immediately
   - Store securely and backup safely

2. **Service Account Security**
   - The service account approach allows automated access without manual authentication
   - Only share spreadsheets with the service account that need access
   - Regularly review and rotate credentials if needed

3. **Environment Variables** (Optional Enhancement)
   - Consider storing sensitive configuration in environment variables
   - Use tools like `python-dotenv` for local development

### Create .gitignore

Create or update `.gitignore`:

```
# Google API Credentials
google_credentials.json
*.json

# Environment files
.env
.env.local

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
```

## Testing the Setup

1. Run the test script:
   ```bash
   python financial_data_access.py
   ```

2. You should see output confirming connection to your spreadsheet and listing available sheets

## Next Steps

Once this setup is complete, you can:

1. Create scripts to automatically read financial data from your spreadsheet
2. Generate reports or documents based on the data
3. Update the spreadsheet programmatically with new financial information
4. Integrate with Claude Code tools for automated financial analysis

## Troubleshooting

- **Authentication Error**: Verify the service account has been shared with your spreadsheet
- **Permission Error**: Ensure the service account has Editor permissions
- **Import Error**: Verify all required packages are installed
- **File Not Found**: Ensure `google_credentials.json` is in the correct directory