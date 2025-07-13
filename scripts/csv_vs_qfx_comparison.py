#!/usr/bin/env python3
"""
Compare QFX vs CSV analysis for Vanguard investment income reporting.
Analyze both file formats for Q2 2025 data and compare results.
"""

import re
import csv
from datetime import datetime
from decimal import Decimal
from vanguard_income_parser import parse_qfx_income, get_cusip_symbol_mapping, get_account_mapping

def analyze_csv_structure(csv_file):
    """
    Analyze the structure and content of the CSV file.
    """
    print("=== CSV FILE ANALYSIS ===")
    
    try:
        with open(csv_file, 'r') as f:
            # Read first few lines to understand structure
            sample_lines = []
            for i, line in enumerate(f):
                sample_lines.append(line.strip())
                if i >= 10:  # Read first 11 lines
                    break
        
        print("First 11 lines of CSV:")
        for i, line in enumerate(sample_lines):
            print(f"Line {i+1}: {line}")
        
        # Try to parse as CSV
        print("\n--- CSV Parsing Attempt ---")
        with open(csv_file, 'r') as f:
            # Try different approaches to parse the CSV
            content = f.read()
            
            # Check if it contains transaction data
            if 'Trade Date' in content and 'Settlement Date' in content:
                print("✓ Appears to contain transaction data")
                return analyze_csv_transactions(csv_file)
            elif 'Account Number' in content and 'Investment Name' in content:
                print("✓ Appears to contain holdings data")
                return analyze_csv_holdings(csv_file)
            else:
                print("? Unknown CSV format")
                return None
                
    except Exception as e:
        print(f"Error analyzing CSV: {e}")
        return None

def analyze_csv_transactions(csv_file):
    """
    Analyze CSV file that contains transaction data.
    """
    print("\n=== CSV TRANSACTION ANALYSIS ===")
    
    try:
        transactions = []
        income_transactions = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"CSV Headers: {headers}")
            
            for row in reader:
                transactions.append(row)
                
                # Look for income-related transactions
                transaction_type = row.get('Transaction Type', '').upper()
                description = row.get('Description', '').upper()
                
                if any(keyword in transaction_type or keyword in description 
                       for keyword in ['DIVIDEND', 'INTEREST', 'INCOME', 'REINVESTMENT']):
                    income_transactions.append(row)
        
        print(f"Total transactions: {len(transactions)}")
        print(f"Income transactions: {len(income_transactions)}")
        
        if income_transactions:
            print("\nSample income transactions:")
            for i, txn in enumerate(income_transactions[:5]):
                print(f"  {i+1}: {txn}")
        
        return {
            'format': 'transactions',
            'total_count': len(transactions),
            'income_count': len(income_transactions),
            'headers': headers,
            'sample_income': income_transactions[:5]
        }
        
    except Exception as e:
        print(f"Error analyzing CSV transactions: {e}")
        return None

def analyze_csv_holdings(csv_file):
    """
    Analyze CSV file that contains holdings/positions data.
    """
    print("\n=== CSV HOLDINGS ANALYSIS ===")
    
    try:
        holdings = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"CSV Headers: {headers}")
            
            for row in reader:
                # Skip empty rows
                if any(row.values()):
                    holdings.append(row)
        
        print(f"Total holdings: {len(holdings)}")
        
        if holdings:
            print("\nSample holdings:")
            for i, holding in enumerate(holdings[:5]):
                print(f"  {i+1}: {holding}")
        
        return {
            'format': 'holdings',
            'total_count': len(holdings),
            'headers': headers,
            'sample_holdings': holdings[:5]
        }
        
    except Exception as e:
        print(f"Error analyzing CSV holdings: {e}")
        return None

def compare_qfx_vs_csv_analysis():
    """
    Run comprehensive comparison between QFX and CSV analysis approaches.
    """
    qfx_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    csv_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.csv"
    
    print("=" * 80)
    print("COMPREHENSIVE QFX vs CSV COMPARISON")
    print("=" * 80)
    
    # 1. Analyze CSV structure
    csv_analysis = analyze_csv_structure(csv_file)
    
    print("\n" + "=" * 80)
    
    # 2. Analyze QFX structure for Q2 data
    print("=== QFX FILE ANALYSIS ===")
    
    try:
        start_date = datetime(2025, 4, 1)
        end_date = datetime(2025, 6, 30)
        
        qfx_transactions = parse_qfx_income(qfx_file, start_date, end_date)
        print(f"QFX Income transactions found: {len(qfx_transactions)}")
        
        if qfx_transactions:
            print("\nQFX Income transactions summary:")
            total_qfx_income = sum(txn['amount'] for txn in qfx_transactions)
            print(f"Total income: ${total_qfx_income:.2f}")
            
            accounts = set(txn['account_id'] for txn in qfx_transactions)
            print(f"Accounts involved: {len(accounts)}")
            
            funds = set(txn['cusip'] for txn in qfx_transactions)
            print(f"Unique funds: {len(funds)}")
        
        qfx_analysis = {
            'format': 'qfx_income',
            'income_count': len(qfx_transactions),
            'total_income': total_qfx_income if qfx_transactions else 0,
            'accounts': len(accounts) if qfx_transactions else 0,
            'funds': len(funds) if qfx_transactions else 0
        }
        
    except Exception as e:
        print(f"Error analyzing QFX: {e}")
        qfx_analysis = None
    
    print("\n" + "=" * 80)
    
    # 3. Comparison Summary
    print("=== COMPARISON SUMMARY ===")
    
    print("\n1. DATA AVAILABILITY:")
    if csv_analysis:
        print(f"   CSV: {csv_analysis['format']} format with {csv_analysis['total_count']} records")
        if csv_analysis['format'] == 'transactions':
            print(f"        {csv_analysis['income_count']} income transactions")
    else:
        print("   CSV: Analysis failed")
    
    if qfx_analysis:
        print(f"   QFX: {qfx_analysis['income_count']} income transactions")
        print(f"        ${qfx_analysis['total_income']:.2f} total income")
        print(f"        {qfx_analysis['accounts']} accounts, {qfx_analysis['funds']} funds")
    else:
        print("   QFX: Analysis failed")
    
    print("\n2. EASE OF ANALYSIS:")
    print("   CSV Pros:")
    print("   - Human readable")
    print("   - Easy to import into spreadsheets")
    print("   - Simple structure")
    print("   - Standard format")
    
    print("\n   CSV Cons:")
    print("   - May not contain income/dividend details")
    print("   - Limited transaction history")
    print("   - Requires manual calculation of income")
    
    print("\n   QFX Pros:")
    print("   - Contains detailed transaction data")
    print("   - Includes specific income transactions")
    print("   - Account-level detail")
    print("   - Standardized financial format")
    
    print("\n   QFX Cons:")
    print("   - Complex XML-like format")
    print("   - Requires specialized parsing")
    print("   - Less human readable")
    print("   - May have data accuracy issues")
    
    print("\n3. ACCURACY COMPARISON:")
    if csv_analysis and qfx_analysis:
        if csv_analysis['format'] == 'transactions' and csv_analysis['income_count'] > 0:
            print("   Both formats contain transactional data for comparison")
        elif csv_analysis['format'] == 'holdings':
            print("   CSV contains holdings, QFX contains transactions - different data types")
            print("   Cannot directly compare income calculations")
        else:
            print("   Insufficient data for direct comparison")
    
    print("\n4. RECOMMENDATION:")
    if qfx_analysis and qfx_analysis['income_count'] > 0:
        print("   FOR INCOME ANALYSIS: QFX is superior")
        print("   - Contains actual dividend/income transactions")
        print("   - Provides exact amounts and dates")
        print("   - Account-level breakdown available")
    
    if csv_analysis and csv_analysis['format'] == 'holdings':
        print("   FOR PORTFOLIO ANALYSIS: CSV is simpler")
        print("   - Easy to see current positions")
        print("   - Simple to calculate total values")
        print("   - Good for position size analysis")
    
    print(f"\n{'='*80}")
    
    return qfx_analysis, csv_analysis

if __name__ == "__main__":
    compare_qfx_vs_csv_analysis()