#!/usr/bin/env python3
"""
Verify QFX files contain transactions for the expected quarters only.
Run before updating spreadsheet to ensure data integrity.
"""

import os
import sys
from datetime import datetime
from vanguard_income_parser import parse_qfx_income

def check_qfx_date_range(qfx_file, expected_quarter, expected_year):
    """Check if QFX file contains transactions only for the expected quarter."""
    
    if not os.path.exists(qfx_file):
        return {
            'status': 'missing',
            'message': f"File not found: {qfx_file}",
            'transactions': 0
        }
    
    try:
        # Parse all transactions without date filtering
        transactions = parse_qfx_income(qfx_file, datetime(2000, 1, 1), datetime(2030, 12, 31))
        
        if not transactions:
            return {
                'status': 'empty',
                'message': "No transactions found in file",
                'transactions': 0
            }
        
        # Extract dates and convert to datetime objects
        dates = []
        for txn in transactions:
            if isinstance(txn['date'], str):
                dates.append(datetime.strptime(txn['date'], '%Y%m%d'))
            else:
                dates.append(txn['date'])
        
        earliest = min(dates)
        latest = max(dates)
        
        # Define expected date ranges for each quarter
        quarter_ranges = {
            'Q1': (datetime(expected_year, 1, 1), datetime(expected_year, 3, 31)),
            'Q2': (datetime(expected_year, 4, 1), datetime(expected_year, 6, 30)),
            'Q3': (datetime(expected_year, 7, 1), datetime(expected_year, 9, 30)),
            'Q4': (datetime(expected_year, 10, 1), datetime(expected_year, 12, 31))
        }
        
        expected_start, expected_end = quarter_ranges[expected_quarter]
        
        # Check if all transactions fall within expected range
        transactions_in_range = 0
        transactions_outside_range = 0
        outside_range_dates = []
        
        for date in dates:
            if expected_start <= date <= expected_end:
                transactions_in_range += 1
            else:
                transactions_outside_range += 1
                outside_range_dates.append(date)
        
        # Determine status
        if transactions_outside_range == 0:
            status = 'perfect'
            message = f"✅ All {len(transactions)} transactions within {expected_quarter} {expected_year}"
        else:
            status = 'mixed'
            outside_dates_str = ", ".join([d.strftime('%b %d, %Y') for d in outside_range_dates[:5]])
            if len(outside_range_dates) > 5:
                outside_dates_str += f" (and {len(outside_range_dates) - 5} more)"
            message = f"⚠️  {transactions_outside_range} transactions outside {expected_quarter} {expected_year}: {outside_dates_str}"
        
        return {
            'status': status,
            'message': message,
            'transactions': len(transactions),
            'earliest': earliest,
            'latest': latest,
            'expected_start': expected_start,
            'expected_end': expected_end,
            'in_range': transactions_in_range,
            'outside_range': transactions_outside_range
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Error reading file: {e}",
            'transactions': 0
        }

def verify_all_qfx_files():
    """Verify all QFX files in the Historical-Data/Vanguard directory."""
    
    print("=" * 80)
    print("VERIFYING QFX FILE DATE RANGES")
    print("=" * 80)
    
    base_path = "/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard"
    
    # Define expected files and their quarters
    expected_files = [
        ('2025_Q1.qfx', 'Q1', 2025),
        ('2025-Q2.qfx', 'Q2', 2025),  # Note: Your file has a dash instead of underscore
        ('2024_Q1.qfx', 'Q1', 2024),
        ('2024_Q2.qfx', 'Q2', 2024),
        ('2024_Q3.qfx', 'Q3', 2024),
        ('2024_Q4.qfx', 'Q4', 2024)
    ]
    
    # Also check the existing Q2 2025 file
    existing_q2_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    
    all_good = True
    
    print(f"\n📁 Checking files in: {base_path}")
    print(f"📁 Plus existing file: {existing_q2_file}")
    print()
    
    # Check historical files
    for filename, quarter, year in expected_files:
        file_path = os.path.join(base_path, filename)
        print(f"🔍 {filename} (Expected: {quarter} {year})")
        
        result = check_qfx_date_range(file_path, quarter, year)
        
        if result['status'] == 'perfect':
            print(f"   {result['message']}")
            print(f"   📅 Date range: {result['earliest'].strftime('%b %d, %Y')} → {result['latest'].strftime('%b %d, %Y')}")
        elif result['status'] == 'mixed':
            print(f"   {result['message']}")
            print(f"   📅 Actual range: {result['earliest'].strftime('%b %d, %Y')} → {result['latest'].strftime('%b %d, %Y')}")
            print(f"   📅 Expected range: {result['expected_start'].strftime('%b %d, %Y')} → {result['expected_end'].strftime('%b %d, %Y')}")
            all_good = False
        else:
            print(f"   ❌ {result['message']}")
            if result['status'] != 'missing':
                all_good = False
        
        print()
    
    # Check existing Q2 2025 file
    print(f"🔍 Vanguard_2025Q2.qfx (Expected: Q2 2025)")
    result = check_qfx_date_range(existing_q2_file, 'Q2', 2025)
    
    if result['status'] == 'perfect':
        print(f"   {result['message']}")
        print(f"   📅 Date range: {result['earliest'].strftime('%b %d, %Y')} → {result['latest'].strftime('%b %d, %Y')}")
    elif result['status'] == 'mixed':
        print(f"   {result['message']}")
        print(f"   📅 Actual range: {result['earliest'].strftime('%b %d, %Y')} → {result['latest'].strftime('%b %d, %Y')}")
        print(f"   📅 Expected range: {result['expected_start'].strftime('%b %d, %Y')} → {result['expected_end'].strftime('%b %d, %Y')}")
        all_good = False
    else:
        print(f"   ❌ {result['message']}")
        all_good = False
    
    print()
    print("=" * 80)
    if all_good:
        print("✅ ALL FILES CONTAIN EXPECTED QUARTERLY DATA - SAFE TO PROCEED")
    else:
        print("⚠️  SOME FILES CONTAIN DATA OUTSIDE EXPECTED QUARTERS - REVIEW BEFORE PROCEEDING")
    print("=" * 80)
    
    return all_good

if __name__ == "__main__":
    verify_all_qfx_files()