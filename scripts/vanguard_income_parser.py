#!/usr/bin/env python3
"""
Vanguard Investment Income Parser
Extracts dividend and interest income from Vanguard QFX files for Q2 2025.
"""

import re
from datetime import datetime
from decimal import Decimal
from config import CUSIP_MAPPINGS, ACCOUNT_MAPPINGS

def parse_qfx_income(file_path, start_date, end_date):
    """
    Parse QFX file and extract income transactions within date range.
    
    Args:
        file_path (str): Path to QFX file
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
    
    Returns:
        list: List of income transactions with account information
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract account sections
    account_sections = re.findall(r'<INVSTMTRS>.*?</INVSTMTRS>', content, re.DOTALL)
    
    parsed_transactions = []
    
    for account_section in account_sections:
        # Extract account ID
        account_match = re.search(r'<ACCTID>(\d+)', account_section)
        account_id = account_match.group(1) if account_match else 'Unknown'
        
        # Find all INCOME transactions in this account
        income_pattern = r'<INCOME>.*?</INCOME>'
        income_transactions = re.findall(income_pattern, account_section, re.DOTALL)
        
        for transaction in income_transactions:
            # Extract transaction details
            fitid_match = re.search(r'<FITID>(\d+)', transaction)
            date_match = re.search(r'<DTTRADE>(\d{8})', transaction)
            memo_match = re.search(r'<MEMO>([^<]+)', transaction)
            total_match = re.search(r'<TOTAL>([0-9.-]+)', transaction)
            cusip_match = re.search(r'<UNIQUEID>(\d+)', transaction)
            income_type_match = re.search(r'<INCOMETYPE>([^<]+)', transaction)
            
            if date_match and total_match:
                # Parse date (format: YYYYMMDD)
                date_str = date_match.group(1)
                transaction_date = datetime.strptime(date_str, '%Y%m%d')
                
                # Check if transaction is within our date range
                if start_date <= transaction_date <= end_date:
                    parsed_transactions.append({
                        'account_id': account_id,
                        'date': transaction_date,
                        'fitid': fitid_match.group(1) if fitid_match else 'Unknown',
                        'memo': memo_match.group(1) if memo_match else 'Unknown',
                        'amount': Decimal(total_match.group(1)),
                        'cusip': cusip_match.group(1) if cusip_match else 'Unknown',
                        'income_type': income_type_match.group(1) if income_type_match else 'Unknown'
                    })
    
    return sorted(parsed_transactions, key=lambda x: (x['account_id'], x['date']))

def get_cusip_symbol_mapping():
    """
    Return mapping of CUSIP numbers to fund symbols/names.
    Now loaded from config.py instead of hardcoded.
    """
    return CUSIP_MAPPINGS

def get_account_mapping():
    """
    Return mapping of account IDs to account descriptions.
    Now loaded from config.py instead of hardcoded.
    """
    return ACCOUNT_MAPPINGS

def generate_income_report(file_path, quarter_year="Q2 2025"):
    """
    Generate a comprehensive income report for the specified quarter.
    """
    # Define Q2 2025 date range (April 1 - June 30, 2025)
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 6, 30)
    
    print(f"\n=== VANGUARD INVESTMENT INCOME REPORT ===")
    print(f"Period: {quarter_year} (April 1 - June 30, 2025)")
    print(f"Source: {file_path}")
    print("=" * 70)
    
    # Parse transactions
    transactions = parse_qfx_income(file_path, start_date, end_date)
    
    if not transactions:
        print("No income transactions found for the specified period.")
        return
    
    # Get mappings
    cusip_mapping = get_cusip_symbol_mapping()
    account_mapping = get_account_mapping()
    
    # Summary by account and fund
    account_totals = {}
    fund_totals = {}
    account_fund_totals = {}
    total_income = Decimal('0')
    
    # Detailed transaction listing
    print(f"\n=== DETAILED TRANSACTIONS ===")
    print(f"{'Date':<12} {'Account':<25} {'Fund':<35} {'Amount':<10}")
    print("-" * 85)
    
    current_account = None
    for txn in transactions:
        account_name = account_mapping.get(txn['account_id'], f"Account {txn['account_id']}")
        fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
        amount = txn['amount']
        total_income += amount
        
        # Track totals by account
        if account_name not in account_totals:
            account_totals[account_name] = Decimal('0')
        account_totals[account_name] += amount
        
        # Track totals by fund
        if fund_name not in fund_totals:
            fund_totals[fund_name] = Decimal('0')
        fund_totals[fund_name] += amount
        
        # Track totals by account-fund combination
        if account_name not in account_fund_totals:
            account_fund_totals[account_name] = {}
        if fund_name not in account_fund_totals[account_name]:
            account_fund_totals[account_name][fund_name] = Decimal('0')
        account_fund_totals[account_name][fund_name] += amount
        
        # Show account separator
        if current_account != account_name:
            if current_account is not None:
                print("-" * 85)
            current_account = account_name
        
        # Truncate fund name for display if needed
        display_fund = fund_name[:35] if len(fund_name) > 35 else fund_name
        
        print(f"{txn['date'].strftime('%Y-%m-%d'):<12} {account_name:<25} {display_fund:<35} ${amount:>8.2f}")
    
    print("-" * 85)
    print(f"{'TOTAL INCOME':<72} ${total_income:>8.2f}")
    
    # Summary by account
    print(f"\n=== INCOME BY ACCOUNT ===")
    print(f"{'Account':<35} {'Total':<12} {'%':<6}")
    print("-" * 55)
    
    for account, amount in sorted(account_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_income * 100) if total_income > 0 else 0
        print(f"{account:<35} ${amount:>10.2f} {percentage:>5.1f}%")
    
    # Detailed breakdown by account
    print(f"\n=== BREAKDOWN BY ACCOUNT & FUND ===")
    for account in sorted(account_totals.keys()):
        account_total = account_totals[account]
        print(f"\n{account} (${account_total:.2f}):")
        print(f"{'  Fund':<43} {'Amount':<10} {'%':<6}")
        print("-" * 60)
        
        for fund, amount in sorted(account_fund_totals[account].items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / account_total * 100) if account_total > 0 else 0
            display_fund = fund[:40] if len(fund) > 40 else fund
            print(f"  {display_fund:<41} ${amount:>8.2f} {percentage:>5.1f}%")
    
    # Summary by fund (overall)
    print(f"\n=== INCOME BY FUND (OVERALL) ===")
    print(f"{'Fund':<45} {'Total':<10} {'%':<6}")
    print("-" * 62)
    
    for fund, amount in sorted(fund_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_income * 100) if total_income > 0 else 0
        display_fund = fund[:44] if len(fund) > 44 else fund
        print(f"{display_fund:<45} ${amount:>8.2f} {percentage:>5.1f}%")
    
    print(f"\n=== SUMMARY ===")
    print(f"Quarter: {quarter_year}")
    print(f"Total Investment Income: ${total_income:.2f}")
    print(f"Number of Accounts: {len(account_totals)}")
    print(f"Number of Dividend Payments: {len(transactions)}")
    print(f"Average Monthly Income: ${total_income / 3:.2f}")
    print(f"Annualized Income Estimate: ${total_income * 4:.2f}")

if __name__ == "__main__":
    # Path to Vanguard QFX file
    qfx_file_path = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    
    try:
        generate_income_report(qfx_file_path)
    except FileNotFoundError:
        print(f"Error: Could not find QFX file at {qfx_file_path}")
    except Exception as e:
        print(f"Error processing file: {e}")