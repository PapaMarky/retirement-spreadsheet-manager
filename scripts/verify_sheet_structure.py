#!/usr/bin/env python3
"""
Verify the structure of annual sheets before running updates.
Check INVESTMENT INCOME sections and column headers.
"""

from google_auth import get_google_services
from config import SPREADSHEET_ID

def find_investment_income_section(sheet_data):
    """Find the INVESTMENT INCOME section in sheet data."""
    for i, row in enumerate(sheet_data):
        if any(cell and 'INVESTMENT INCOME' in str(cell).upper() for cell in row):
            return i
    return None

def analyze_sheet_structure(sheet_name):
    """Analyze the structure of a specific sheet."""
    try:
        docs_service, sheets_service, drive_service = get_google_services()
        
        # Read current sheet data
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        
        sheet_data = result.get('values', [])
        
        print(f"\n{'='*60}")
        print(f"ANALYZING SHEET: {sheet_name}")
        print(f"{'='*60}")
        
        # Find INVESTMENT INCOME section
        income_row = find_investment_income_section(sheet_data)
        if income_row is None:
            print(f"❌ Could not find INVESTMENT INCOME section in {sheet_name}")
            return False
        
        print(f"✅ Found INVESTMENT INCOME section at row {income_row + 1}")
        
        # Show header row to verify quarterly columns
        print(f"\n📅 COLUMN HEADERS (Row 1):")
        if len(sheet_data) > 0:
            headers = sheet_data[0]
            for i, header in enumerate(headers[:10]):  # Show first 10 columns
                if header:
                    print(f"  Column {chr(65+i)} ({i+1}): {header}")
        
        # Show the INVESTMENT INCOME section structure
        print(f"\n📊 INVESTMENT INCOME SECTION STRUCTURE:")
        start_row = max(0, income_row - 1)
        end_row = min(len(sheet_data), income_row + 8)
        
        for j in range(start_row, end_row):
            if j < len(sheet_data):
                row_data = sheet_data[j]
                # Show first 6 columns (should cover quarterly data)
                formatted_row = []
                for k in range(6):
                    if k < len(row_data):
                        cell_str = str(row_data[k]) if row_data[k] else ''
                        formatted_row.append(f"{cell_str:<20}")
                    else:
                        formatted_row.append(" " * 20)
                
                row_indicator = "➤" if j == income_row else " "
                print(f"  {row_indicator} Row {j+1:2d}: {''.join(formatted_row)}")
        
        # Check specific expected rows
        expected_structure = {
            income_row + 1: "Tax-Free",
            income_row + 2: "Tax-Deferred", 
            income_row + 3: "Taxed Now",
            income_row + 5: "TOTAL INCOME"
        }
        
        print(f"\n🔍 VERIFYING EXPECTED STRUCTURE:")
        all_good = True
        
        for expected_row, expected_text in expected_structure.items():
            if expected_row < len(sheet_data) and len(sheet_data[expected_row]) > 0:
                actual_text = str(sheet_data[expected_row][0]) if sheet_data[expected_row][0] else ""
                if expected_text.upper() in actual_text.upper():
                    print(f"  ✅ Row {expected_row + 1}: Found '{actual_text}' (expected '{expected_text}')")
                else:
                    print(f"  ❌ Row {expected_row + 1}: Found '{actual_text}' (expected '{expected_text}')")
                    all_good = False
            else:
                print(f"  ❌ Row {expected_row + 1}: Row doesn't exist or is empty (expected '{expected_text}')")
                all_good = False
        
        # Check for quarterly columns (simplified check)
        print(f"\n📅 QUARTERLY COLUMN ANALYSIS:")
        quarterly_indicators = ['APRIL', 'JULY', 'OCTOBER', 'JANUARY', 'Q1', 'Q2', 'Q3', 'Q4']
        
        found_quarters = []
        if len(sheet_data) > 0:
            headers = sheet_data[0]
            for i, header in enumerate(headers[:10]):
                if header:
                    header_upper = str(header).upper()
                    for indicator in quarterly_indicators:
                        if indicator in header_upper:
                            found_quarters.append(f"Column {chr(65+i)} ({i+1}): {header}")
                            break
        
        if found_quarters:
            print("  ✅ Found quarterly columns:")
            for quarter in found_quarters:
                print(f"    {quarter}")
        else:
            print("  ⚠️  Could not identify quarterly columns clearly")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error analyzing {sheet_name}: {e}")
        return False

def verify_all_sheets():
    """Verify structure of all annual sheets."""
    
    print("=" * 80)
    print("VERIFYING SPREADSHEET STRUCTURE BEFORE UPDATES")
    print("=" * 80)
    
    sheets_to_check = ['2025', '2024', '2023']
    all_sheets_ok = True
    
    for sheet_name in sheets_to_check:
        sheet_ok = analyze_sheet_structure(sheet_name)
        all_sheets_ok = all_sheets_ok and sheet_ok
    
    print(f"\n{'='*80}")
    if all_sheets_ok:
        print("✅ ALL SHEETS LOOK GOOD - SAFE TO RUN UPDATE SCRIPT")
    else:
        print("❌ SOME ISSUES FOUND - REVIEW BEFORE RUNNING UPDATE SCRIPT")
    print(f"{'='*80}")
    
    return all_sheets_ok

if __name__ == "__main__":
    verify_all_sheets()