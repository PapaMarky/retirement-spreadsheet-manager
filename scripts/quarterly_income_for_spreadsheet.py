#!/usr/bin/env python3
"""
Calculate quarterly investment income values for the Family Assets spreadsheet.
Extract income data from QFX and format for quarterly reporting.
"""

from datetime import datetime
from vanguard_income_parser import parse_qfx_income, get_cusip_symbol_mapping, get_account_mapping

def calculate_quarterly_income_for_spreadsheet():
    """Calculate investment income by quarter for spreadsheet input."""
    
    qfx_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    
    print("=" * 80)
    print("QUARTERLY INVESTMENT INCOME FOR FAMILY ASSETS SPREADSHEET")
    print("=" * 80)
    
    # Define quarterly periods (matching your spreadsheet structure)
    quarters = {
        'Q1 2025': (datetime(2025, 1, 1), datetime(2025, 3, 31)),
        'Q2 2025': (datetime(2025, 4, 1), datetime(2025, 6, 30)),
        'Q3 2025': (datetime(2025, 7, 1), datetime(2025, 9, 30)),
        'Q4 2025': (datetime(2025, 10, 1), datetime(2025, 12, 31))
    }
    
    # Get mappings
    cusip_mapping = get_cusip_symbol_mapping()
    account_mapping = get_account_mapping()
    
    print("\n=== QUARTERLY INVESTMENT INCOME BREAKDOWN ===")
    
    total_annual_income = 0
    quarterly_totals = {}
    
    for quarter_name, (start_date, end_date) in quarters.items():
        try:
            transactions = parse_qfx_income(qfx_file, start_date, end_date)
            
            if transactions:
                quarter_total = sum(txn['amount'] for txn in transactions)
                quarterly_totals[quarter_name] = quarter_total
                total_annual_income += quarter_total
                
                print(f"\n{quarter_name} ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}):")
                print(f"  Total Income: ${quarter_total:,.2f}")
                print(f"  Transactions: {len(transactions)}")
                
                # Break down by account
                account_totals = {}
                for txn in transactions:
                    account_name = account_mapping.get(txn['account_id'], f"Account {txn['account_id']}")
                    if account_name not in account_totals:
                        account_totals[account_name] = 0
                    account_totals[account_name] += txn['amount']
                
                for account, amount in sorted(account_totals.items(), key=lambda x: x[1], reverse=True):
                    print(f"    {account}: ${amount:,.2f}")
                    
            else:
                quarterly_totals[quarter_name] = 0
                print(f"\n{quarter_name}: No investment income data available")
                
        except Exception as e:
            quarterly_totals[quarter_name] = 0
            print(f"\n{quarter_name}: Error reading data - {e}")
    
    print(f"\n{'='*80}")
    print("SUMMARY FOR SPREADSHEET INPUT")
    print(f"{'='*80}")
    
    print("\nQuarterly Investment Income Values:")
    print("(These are the values to enter in your INVESTMENT INCOME section)")
    print()
    
    # Format for spreadsheet input
    spreadsheet_columns = [
        ("January 1 (Q4 2024 income)", "Data not available in Q2 file"),
        ("April 1 (Q1 2025 income)", quarterly_totals.get('Q1 2025', 0)),
        ("July 1 (Q2 2025 income)", quarterly_totals.get('Q2 2025', 0)),
        ("October 1 (Q3 2025 income)", quarterly_totals.get('Q3 2025', 0))
    ]
    
    for column_label, value in spreadsheet_columns:
        if isinstance(value, (int, float)):
            print(f"{column_label:<30} ${value:>10,.2f}")
        else:
            print(f"{column_label:<30} {value}")
    
    # Calculate what we can project
    if quarterly_totals.get('Q2 2025', 0) > 0:
        q2_income = quarterly_totals['Q2 2025']
        print(f"\n=== PROJECTIONS BASED ON Q2 DATA ===")
        print(f"Q2 2025 Actual Income:              ${q2_income:,.2f}")
        print(f"Projected Annual Income (Q2 x 4):   ${q2_income * 4:,.2f}")
        print(f"Monthly Average:                    ${q2_income / 3:,.2f}")
    
    print(f"\n=== RECOMMENDED SPREADSHEET ENTRIES ===")
    print("Based on available data, update your INVESTMENT INCOME section:")
    print()
    print("July 1 column (Q2 2025 income):")
    print(f"  Vanguard Investment Income: ${quarterly_totals.get('Q2 2025', 0):,.2f}")
    print()
    print("Notes:")
    print("- Q2 file only contains Q2 2025 data")
    print("- For complete year, you'd need Q1, Q3, Q4 QFX files")
    print("- Or download full-year QFX file for all quarters")
    
    # Detailed breakdown for the quarter we have data for
    if quarterly_totals.get('Q2 2025', 0) > 0:
        print(f"\n=== DETAILED Q2 2025 BREAKDOWN ===")
        transactions = parse_qfx_income(qfx_file, datetime(2025, 4, 1), datetime(2025, 6, 30))
        
        # Group by fund type for better understanding
        fund_categories = {
            'Bond Funds': [],
            'Stock Funds': [],
            'Municipal Bonds': [],
            'Money Market': [],
            'Other': []
        }
        
        for txn in transactions:
            fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
            
            if any(keyword in fund_name.upper() for keyword in ['BOND', 'TREASURY']):
                fund_categories['Bond Funds'].append(txn)
            elif any(keyword in fund_name.upper() for keyword in ['STOCK', 'EQUITY', 'GROWTH', 'VALUE']):
                fund_categories['Stock Funds'].append(txn)
            elif any(keyword in fund_name.upper() for keyword in ['MUNICIPAL', 'CALIFORNIA', 'MUN']):
                fund_categories['Municipal Bonds'].append(txn)
            elif 'MONEY MARKET' in fund_name.upper():
                fund_categories['Money Market'].append(txn)
            else:
                fund_categories['Other'].append(txn)
        
        for category, txns in fund_categories.items():
            if txns:
                category_total = sum(txn['amount'] for txn in txns)
                print(f"\n{category}: ${category_total:,.2f}")
                for txn in txns:
                    fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
                    account_name = account_mapping.get(txn['account_id'], f"Account {txn['account_id']}")
                    print(f"  {fund_name[:50]}: ${txn['amount']:>8.2f} ({account_name})")

if __name__ == "__main__":
    calculate_quarterly_income_for_spreadsheet()