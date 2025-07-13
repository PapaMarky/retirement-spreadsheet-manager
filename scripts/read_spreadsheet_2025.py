#!/usr/bin/env python3
"""
Read the 2025 sheet from your Family Assets Google Spreadsheet.
"""

from financial_data_access import read_financial_data

def read_2025_sheet():
    """Read specifically the 2025 sheet from the spreadsheet."""
    try:
        print("Reading Family Assets spreadsheet...")
        data = read_financial_data()
        
        if '2025' in data:
            print(f"\n=== 2025 SHEET CONTENTS ===")
            sheet_data = data['2025']
            
            if sheet_data:
                print(f"Rows found: {len(sheet_data)}")
                print("\nFirst 20 rows:")
                for i, row in enumerate(sheet_data[:20]):
                    print(f"Row {i+1}: {row}")
                
                if len(sheet_data) > 20:
                    print(f"\n... and {len(sheet_data) - 20} more rows")
            else:
                print("2025 sheet appears to be empty")
        else:
            print("2025 sheet not found. Available sheets:")
            for sheet_name in data.keys():
                print(f"  - {sheet_name}")
    
    except Exception as e:
        print(f"Error reading spreadsheet: {e}")
        print("Make sure the Google Sheets API credentials are set up correctly")

if __name__ == "__main__":
    read_2025_sheet()