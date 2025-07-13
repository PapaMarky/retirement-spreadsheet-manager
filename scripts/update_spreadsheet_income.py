#!/usr/bin/env python3
"""
Update INVESTMENT INCOME sections in annual spreadsheet sheets with QFX data.
Handles multiple quarters and years automatically.
"""

import os
from datetime import datetime
from google_auth import get_google_services
from vanguard_income_parser import parse_qfx_income, get_cusip_symbol_mapping, get_account_mapping
from config import SPREADSHEET_ID, ACCOUNT_TAX_TREATMENT

def is_tax_exempt_fund(cusip, fund_name):
    """Determine if a fund generates tax-exempt income."""
    tax_exempt_keywords = ['MUNICIPAL', 'MUN', 'CALIFORNIA', 'TAX EXEMPT']
    return any(keyword in fund_name.upper() for keyword in tax_exempt_keywords)

def calculate_income_for_quarter(qfx_file, start_date, end_date):
    """Calculate income breakdown for a specific quarter."""
    if not os.path.exists(qfx_file):
        return None
    
    try:
        transactions = parse_qfx_income(qfx_file, start_date, end_date)
        if not transactions:
            return None
            
        cusip_mapping = get_cusip_symbol_mapping()
        
        # Initialize totals
        tax_free_total = 0
        tax_deferred_total = 0
        taxed_now_total = 0
        
        # Process each transaction
        for txn in transactions:
            account_id = txn['account_id']
            amount = float(txn['amount'])
            fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
            
            # Use config-based tax treatment
            tax_treatment = ACCOUNT_TAX_TREATMENT.get(account_id, 'Unknown')
            
            if tax_treatment == 'Tax-Free':
                tax_free_total += amount
            elif tax_treatment == 'Tax-Deferred':
                tax_deferred_total += amount
            elif tax_treatment == 'Taxed-Now':
                if is_tax_exempt_fund(txn['cusip'], fund_name):
                    tax_free_total += amount  # Municipal bonds are tax-free
                else:
                    taxed_now_total += amount  # Regular investments
            else:
                print(f"Warning: Unknown tax treatment for account {account_id}")
                taxed_now_total += amount  # Default to taxed now
        
        total_income = tax_free_total + tax_deferred_total + taxed_now_total
        
        return {
            'tax_free': tax_free_total,
            'tax_deferred': tax_deferred_total,
            'taxed_now': taxed_now_total,
            'total': total_income,
            'transaction_count': len(transactions)
        }
        
    except Exception as e:
        print(f"Error processing {qfx_file}: {e}")
        return None

def find_investment_income_section(sheet_data):
    """Find the INVESTMENT INCOME section in sheet data."""
    for i, row in enumerate(sheet_data):
        if any(cell and 'INVESTMENT INCOME' in str(cell).upper() for cell in row):
            return i
    return None

def find_quarterly_columns(sheets_service, sheet_name, target_year):
    """Find quarterly column positions by reading row 3 quarter descriptions."""
    import re
    
    try:
        # Read row 3 (contains quarter descriptions like "Oct, Nov, Dec (2024 Q4)")
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!3:3"  # Row 3 only
        ).execute()
        
        row3_data = result.get('values', [[]])[0] if result.get('values') else []
        
        quarterly_columns = {}
        
        for col_index, cell in enumerate(row3_data):
            if cell and isinstance(cell, str):
                # Look for pattern like "(2024 Q4)" or "(2025 Q1)" 
                match = re.search(r'\((\d{4})\s+Q(\d)\)', cell)
                if match:
                    year = int(match.group(1))
                    quarter = int(match.group(2))
                    quarter_key = f"Q{quarter}"
                    
                    # Include quarters for target year AND previous year's Q4
                    if year == target_year or (year == target_year - 1 and quarter == 4):
                        # For previous year Q4, use special key
                        if year == target_year - 1 and quarter == 4:
                            quarter_key = f"Q4_{year}"  # e.g., "Q4_2024"
                        
                        quarterly_columns[quarter_key] = col_index
                        print(f"   📅 Found {year} Q{quarter} in column {chr(65 + col_index)} ({col_index + 1})")
        
        if not quarterly_columns:
            print(f"   ⚠️  No quarterly columns found for {target_year} in row 3")
        
        return quarterly_columns
        
    except Exception as e:
        print(f"   ❌ Error reading quarterly columns: {e}")
        # Fallback to hardcoded positions
        return {
            'Q1': 3,  # Column D
            'Q2': 6,  # Column G  
            'Q3': 9,  # Column J
            'Q4': 0   # Column A (for previous year Q4)
        }

def update_investment_income_values(sheet_name, year, quarter_data_map):
    """Update INVESTMENT INCOME section for a specific year sheet."""
    
    try:
        docs_service, sheets_service, drive_service = get_google_services()
        
        # Read current sheet data
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        
        sheet_data = result.get('values', [])
        
        # Find INVESTMENT INCOME section
        income_row = find_investment_income_section(sheet_data)
        if income_row is None:
            print(f"❌ Could not find INVESTMENT INCOME section in {sheet_name}")
            return False
        
        print(f"✅ Found INVESTMENT INCOME section in {sheet_name} at row {income_row + 1}")
        
        # Read row 3 to find quarterly column mappings dynamically
        print(f"🔍 Detecting quarterly columns for {year} in {sheet_name}...")
        quarterly_columns = find_quarterly_columns(sheets_service, sheet_name, year)
        
        # Prepare updates
        updates = []
        
        for quarter, col_index in quarterly_columns.items():
            if quarter in quarter_data_map and quarter_data_map[quarter]:
                data = quarter_data_map[quarter]
                
                # Calculate the rows for each category (based on 2025 sheet structure)
                tax_free_row = income_row + 1      # Row 64: "Tax-Free" 
                tax_deferred_row = income_row + 2  # Row 65: "Tax-Deferred"
                taxed_now_row = income_row + 3     # Row 66: "Taxed Now"
                total_row = income_row + 5         # Row 68: "TOTAL INCOME"
                
                # Create update requests (skip TOTAL INCOME - let SUM formula handle it)
                updates.extend([
                    {
                        'range': f"{sheet_name}!{chr(65 + col_index)}{tax_free_row + 1}",
                        'values': [[f"${data['tax_free']:.2f}"]]
                    },
                    {
                        'range': f"{sheet_name}!{chr(65 + col_index)}{tax_deferred_row + 1}",
                        'values': [[f"${data['tax_deferred']:.2f}"]]
                    },
                    {
                        'range': f"{sheet_name}!{chr(65 + col_index)}{taxed_now_row + 1}",
                        'values': [[f"${data['taxed_now']:.2f}"]]
                    }
                    # Note: Skipping TOTAL INCOME row - let spreadsheet SUM formula calculate it
                ])
        
        # Execute batch update
        if updates:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }
            
            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()
            
            print(f"✅ Updated {len(updates)} cells in {sheet_name}")
            return True
        else:
            print(f"⚠️  No data to update in {sheet_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {sheet_name}: {e}")
        return False

def update_all_sheets(dry_run=False):
    """Update INVESTMENT INCOME sections in all annual sheets."""
    
    mode = "DRY RUN - PREVIEW ONLY" if dry_run else "UPDATING SPREADSHEET"
    print("=" * 80)
    print(f"{mode} - INVESTMENT INCOME SECTIONS")
    print("=" * 80)
    
    if dry_run:
        print("🔍 DRY RUN MODE: No changes will be made to the spreadsheet")
        print("=" * 80)
    
    # Define sheet updates with proper quarter mapping
    # Key insight: Q4 data goes to the NEXT year's sheet (Column A)
    sheet_configs = {
        '2025': {
            'sheet_name': '2025',
            'target_year': 2025,
            'qfx_files': {
                'Q4_2024': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2024_Q4.qfx',  # 2024 Q4 → 2025 sheet Column A
                'Q1': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2025_Q1.qfx',          # 2025 Q1 → 2025 sheet Column D
                'Q2': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2025-Q2.qfx',         # 2025 Q2 → 2025 sheet Column G
                'Q3': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2025_Q3.qfx'          # 2025 Q3 → 2025 sheet Column J
            }
        },
        '2024': {
            'sheet_name': '2024',
            'target_year': 2024,
            'qfx_files': {
                'Q4_2023': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2023_Q4.qfx',  # 2023 Q4 → 2024 sheet Column A
                'Q1': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2024_Q1.qfx',          # 2024 Q1 → 2024 sheet Column D
                'Q2': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2024_Q2.qfx',          # 2024 Q2 → 2024 sheet Column G
                'Q3': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2024_Q3.qfx'           # 2024 Q3 → 2024 sheet Column J
            }
        },
        '2023': {
            'sheet_name': '2023',
            'target_year': 2023,
            'qfx_files': {
                'Q4_2022': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2022_Q4.qfx',  # 2022 Q4 → 2023 sheet Column A  
                'Q1': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2023_Q1.qfx',          # 2023 Q1 → 2023 sheet Column D
                'Q2': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2023_Q2.qfx',          # 2023 Q2 → 2023 sheet Column G
                'Q3': '/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/2023_Q3.qfx'           # 2023 Q3 → 2023 sheet Column J
            }
        }
    }
    
    # Define quarterly date ranges
    quarterly_dates = {
        'Q1': (datetime(2023, 1, 1), datetime(2023, 3, 31)),   # Will adjust year in loop
        'Q2': (datetime(2023, 4, 1), datetime(2023, 6, 30)),
        'Q3': (datetime(2023, 7, 1), datetime(2023, 9, 30)),
        'Q4': (datetime(2023, 10, 1), datetime(2023, 12, 31))
    }
    
    for sheet_key, config in sheet_configs.items():
        print(f"\n🔄 Processing {config['sheet_name']} sheet...")
        
        quarter_data_map = {}
        
        # Process each quarter/file mapping
        for quarter_key, qfx_file in config['qfx_files'].items():
            # Determine the actual quarter and year for date filtering
            if quarter_key.startswith('Q4_'):
                # This is a previous year Q4 (e.g., Q4_2024)
                quarter = 'Q4'
                data_year = int(quarter_key.split('_')[1])
            else:
                # This is a regular quarter (Q1, Q2, Q3)
                quarter = quarter_key
                data_year = config['target_year']
            
            start_date, end_date = quarterly_dates[quarter]
            # Adjust dates for the data year
            start_date = start_date.replace(year=data_year)
            end_date = end_date.replace(year=data_year)
            
            print(f"  📊 Analyzing {quarter} {data_year} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}) → {quarter_key}...")
            
            if os.path.exists(qfx_file):
                income_data = calculate_income_for_quarter(qfx_file, start_date, end_date)
                if income_data:
                    quarter_data_map[quarter_key] = income_data  # Use quarter_key (e.g., Q4_2024) for mapping
                    print(f"     ✅ Total: ${income_data['total']:.2f} ({income_data['transaction_count']} transactions)")
                else:
                    print(f"     ⚠️  No income data found")
            else:
                print(f"     ❌ File not found: {qfx_file}")
        
        # Update the spreadsheet for this sheet (or show preview if dry run)
        if quarter_data_map:
            if dry_run:
                # Show quarterly column detection in dry-run mode
                print(f"  🔍 Detecting quarterly columns for {config['target_year']} in {config['sheet_name']}...")
                try:
                    docs_service, sheets_service, drive_service = get_google_services()
                    quarterly_columns = find_quarterly_columns(sheets_service, config['sheet_name'], config['target_year'])
                    
                    print(f"  📋 WOULD UPDATE {config['sheet_name']} sheet with:")
                    for quarter_key, data in quarter_data_map.items():
                        if quarter_key in quarterly_columns:
                            col_letter = chr(65 + quarterly_columns[quarter_key])
                            print(f"     {quarter_key} → Column {col_letter}: Tax-Free=${data['tax_free']:.2f}, Tax-Deferred=${data['tax_deferred']:.2f}, Taxed Now=${data['taxed_now']:.2f}")
                        else:
                            print(f"     {quarter_key} → No matching column found: Tax-Free=${data['tax_free']:.2f}, Tax-Deferred=${data['tax_deferred']:.2f}, Taxed Now=${data['taxed_now']:.2f}")
                    print(f"              (TOTAL will be calculated by spreadsheet SUM formula)")
                except Exception as e:
                    print(f"     ❌ Error detecting columns: {e}")
                    for quarter_key, data in quarter_data_map.items():
                        print(f"     {quarter_key}: Tax-Free=${data['tax_free']:.2f}, Tax-Deferred=${data['tax_deferred']:.2f}, Taxed Now=${data['taxed_now']:.2f}")
                        print(f"              (TOTAL will be calculated by spreadsheet SUM formula)")
            else:
                success = update_investment_income_values(config['sheet_name'], config['target_year'], quarter_data_map)
                if success:
                    print(f"  ✅ Successfully updated {config['sheet_name']} sheet")
                else:
                    print(f"  ❌ Failed to update {config['sheet_name']} sheet")
        else:
            print(f"  ⚠️  No data available for {config['sheet_name']}")
    
    print(f"\n{'='*80}")
    print("UPDATE COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    import sys
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    update_all_sheets(dry_run=dry_run)