from google_auth import get_google_services

DOCUMENT_ID = '1mviES5zD84bW7FXDNJ03Hf6umj6ZteCY'

def check_document_type():
    """Check what type of Google document this ID refers to."""
    docs_service, sheets_service, drive_service = get_google_services()
    
    try:
        # Try Drive API to get document metadata
        file_metadata = drive_service.files().get(fileId=DOCUMENT_ID).execute()
        print(f"Document found via Drive API:")
        print(f"  Name: {file_metadata.get('name', 'Unknown')}")
        print(f"  MIME Type: {file_metadata.get('mimeType', 'Unknown')}")
        print(f"  Created: {file_metadata.get('createdTime', 'Unknown')}")
        
        mime_type = file_metadata.get('mimeType', '')
        if 'spreadsheet' in mime_type:
            print("✓ This is a Google Sheets document")
        elif 'document' in mime_type:
            print("✗ This is a Google Docs document (not Sheets)")
        else:
            print(f"? Unknown document type: {mime_type}")
            
    except Exception as e:
        print(f"Error accessing document: {e}")

if __name__ == "__main__":
    check_document_type()