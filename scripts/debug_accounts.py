#!/usr/bin/env python3
"""
Debug account associations in QFX file to verify which transactions belong to which accounts.
"""

import re
from datetime import datetime

def debug_account_transactions(qfx_file):
    """Debug which transactions are associated with which accounts."""
    
    with open(qfx_file, 'r') as f:
        content = f.read()
    
    # Find all account statement sections
    account_sections = re.findall(r'<INVSTMTRS>.*?</INVSTMTRS>', content, re.DOTALL)
    
    print(f"Found {len(account_sections)} account sections in QFX file\n")
    
    for i, section in enumerate(account_sections, 1):
        print(f"=== ACCOUNT SECTION {i} ===")
        
        # Extract account ID
        account_match = re.search(r'<ACCTID>(\d+)', section)
        account_id = account_match.group(1) if account_match else 'Unknown'
        print(f"Account ID: {account_id}")
        
        # Find Q2 2025 income transactions in this account
        income_transactions = re.findall(r'<INCOME>.*?</INCOME>', section, re.DOTALL)
        print(f"Total income transactions: {len(income_transactions)}")
        
        q2_2025_transactions = []
        for transaction in income_transactions:
            date_match = re.search(r'<DTTRADE>(\d{8})', transaction)
            cusip_match = re.search(r'<UNIQUEID>(\d+)', transaction)
            total_match = re.search(r'<TOTAL>([0-9.-]+)', transaction)
            
            if date_match:
                date_str = date_match.group(1)
                transaction_date = datetime.strptime(date_str, '%Y%m%d')
                
                # Check if in Q2 2025 (April 1 - June 30)
                if datetime(2025, 4, 1) <= transaction_date <= datetime(2025, 6, 30):
                    cusip = cusip_match.group(1) if cusip_match else 'Unknown'
                    amount = total_match.group(1) if total_match else 'Unknown'
                    q2_2025_transactions.append({
                        'date': transaction_date.strftime('%Y-%m-%d'),
                        'cusip': cusip,
                        'amount': amount
                    })
        
        print(f"Q2 2025 income transactions: {len(q2_2025_transactions)}")
        
        if q2_2025_transactions:
            print("Q2 2025 Transactions:")
            print(f"{'Date':<12} {'CUSIP':<12} {'Amount':<10}")
            print("-" * 35)
            for txn in q2_2025_transactions:
                print(f"{txn['date']:<12} {txn['cusip']:<12} ${float(txn['amount']):>8.2f}")
        
        print()

    # Also check for VCTXX specifically
    print("=== VCTXX (CUSIP 922021209) TRANSACTIONS ===")
    vctxx_pattern = r'<INCOME>.*?<UNIQUEID>922021209.*?</INCOME>'
    vctxx_transactions = re.findall(vctxx_pattern, content, re.DOTALL)
    
    print(f"Found {len(vctxx_transactions)} VCTXX transactions total")
    
    for txn in vctxx_transactions:
        date_match = re.search(r'<DTTRADE>(\d{8})', txn)
        total_match = re.search(r'<TOTAL>([0-9.-]+)', txn)
        
        if date_match:
            date_str = date_match.group(1)
            transaction_date = datetime.strptime(date_str, '%Y%m%d')
            amount = total_match.group(1) if total_match else 'Unknown'
            
            # Find which account section this transaction belongs to
            # Look for the account ID that appears before this transaction
            txn_pos = content.find(txn)
            account_before = content.rfind('<ACCTID>', 0, txn_pos)
            if account_before != -1:
                account_end = content.find('</INVACCTFROM>', account_before)
                if account_end != -1:
                    account_section = content[account_before:account_end]
                    account_match = re.search(r'<ACCTID>(\d+)', account_section)
                    if account_match:
                        account_id = account_match.group(1)
                        print(f"Date: {transaction_date.strftime('%Y-%m-%d')}, Amount: ${float(amount):>8.2f}, Account: {account_id}")

if __name__ == "__main__":
    qfx_file = "/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/Vanguard.qfx"
    debug_account_transactions(qfx_file)