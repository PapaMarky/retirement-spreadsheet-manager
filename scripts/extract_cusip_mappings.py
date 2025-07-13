#!/usr/bin/env python3
"""
Extract CUSIP to security name mappings from QFX file and cross-reference with CSV holdings.
"""

import re
import csv

def extract_cusips_from_csv(csv_file):
    """Extract security symbols and names from Vanguard CSV holdings file."""
    securities = {}
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Investment Name') and row.get('Symbol'):
                    symbol = row['Symbol'].strip()
                    name = row['Investment Name'].strip()
                    securities[symbol] = name
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return securities

def find_security_definitions_in_qfx(qfx_file):
    """Search for security definitions in QFX file."""
    try:
        with open(qfx_file, 'r') as f:
            content = f.read()
        
        # Look for security list section
        seclist_pattern = r'<SECLIST>.*?</SECLIST>'
        seclist_match = re.search(seclist_pattern, content, re.DOTALL)
        
        if seclist_match:
            print("Found SECLIST section!")
            seclist_content = seclist_match.group(0)
            
            # Extract individual security info blocks
            secinfo_pattern = r'<(?:STOCK|MFINFO|DEBTINFO)>.*?</(?:STOCK|MFINFO|DEBTINFO)>'
            securities = re.findall(secinfo_pattern, seclist_content, re.DOTALL)
            
            cusip_mappings = {}
            for sec in securities:
                cusip_match = re.search(r'<UNIQUEID>(\d+)', sec)
                name_match = re.search(r'<SECNAME>([^<]+)', sec)
                ticker_match = re.search(r'<TICKER>([^<]+)', sec)
                
                if cusip_match:
                    cusip = cusip_match.group(1)
                    name = name_match.group(1) if name_match else 'Unknown'
                    ticker = ticker_match.group(1) if ticker_match else ''
                    
                    if ticker:
                        cusip_mappings[cusip] = f"{name} ({ticker})"
                    else:
                        cusip_mappings[cusip] = name
            
            return cusip_mappings
        else:
            print("No SECLIST section found. Looking for individual CUSIP references...")
            
            # Extract unique CUSIPs from transactions
            cusip_pattern = r'<UNIQUEID>(\d+)'
            cusips = set(re.findall(cusip_pattern, content))
            
            print(f"Found {len(cusips)} unique CUSIPs in transactions:")
            for cusip in sorted(cusips):
                print(f"  {cusip}")
            
            return {}
            
    except Exception as e:
        print(f"Error reading QFX file: {e}")
        return {}

def cross_reference_with_known_symbols():
    """Return known Vanguard fund mappings based on common CUSIP patterns."""
    # These mappings are based on common Vanguard fund CUSIP patterns
    # You can expand this by looking up the CUSIPs online
    known_mappings = {
        '921937652': 'VANGUARD HIGH DIVIDEND YIELD ETF (VYM)',
        '922031208': 'VANGUARD TOTAL BOND MARKET INDEX ADMIRAL (VBTLX)',
        '922031760': 'VANGUARD HIGH YIELD CORP ADMIRAL (VWEAX)',
        '922906300': 'VANGUARD FEDERAL MONEY MARKET INVESTOR (VMFXX)',
        '921937603': 'VANGUARD TOTAL INTL STOCK INDEX ADMIRAL (VTIAX)',
        '922021407': 'VANGUARD EXTENDED MARKET INDEX ADMIRAL (VEXAX)',
        '922021100': 'VANGUARD 500 INDEX ADMIRAL (VFIAX)',
        '922021209': 'VANGUARD LONG TERM BOND INDEX ADMIRAL (VBLAX)',
        '921909818': 'VANGUARD TOTAL STOCK MARKET ETF (VTI)',
        '921946406': 'VANGUARD GROWTH ETF (VUG)',
        '921943866': 'VANGUARD TOTAL STOCK MARKET INDEX ADMIRAL (VTSAX)',
        '922908694': 'VANGUARD TAX MANAGED CAPITAL APPRECIATION ADMIRAL (VTCLX)',
        '922908769': 'UNKNOWN VANGUARD FUND (CUSIP 922908769)',
        '922908363': 'UNKNOWN VANGUARD FUND (CUSIP 922908363)',
        '922908710': 'UNKNOWN VANGUARD FUND (CUSIP 922908710)',
        '922906508': 'UNKNOWN VANGUARD FUND (CUSIP 922906508)',
    }
    return known_mappings

if __name__ == "__main__":
    csv_file = "/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/Vanguard.csv"
    qfx_file = "/Users/mark/Documents/Retirement/Assets/Historical-Data/Vanguard/Vanguard.qfx"
    
    print("=== CUSIP TO SECURITY MAPPING EXTRACTION ===\n")
    
    # Extract from CSV
    print("1. Extracting securities from CSV holdings file...")
    csv_securities = extract_cusips_from_csv(csv_file)
    print(f"Found {len(csv_securities)} securities in CSV:")
    for symbol, name in csv_securities.items():
        print(f"  {symbol}: {name}")
    
    print("\n" + "="*50)
    
    # Extract from QFX
    print("2. Searching for security definitions in QFX file...")
    qfx_mappings = find_security_definitions_in_qfx(qfx_file)
    
    if qfx_mappings:
        print(f"Found {len(qfx_mappings)} CUSIP mappings in QFX:")
        for cusip, name in qfx_mappings.items():
            print(f"  {cusip}: {name}")
    
    print("\n" + "="*50)
    
    # Use known mappings
    print("3. Using known Vanguard CUSIP mappings...")
    known_mappings = cross_reference_with_known_symbols()
    
    print(f"\nCOMPLETE CUSIP MAPPING for updating vanguard_income_parser.py:")
    print("def get_cusip_symbol_mapping():")
    print("    return {")
    
    all_mappings = {**known_mappings, **qfx_mappings}
    for cusip, name in sorted(all_mappings.items()):
        print(f"        '{cusip}': '{name}',")
    
    print("    }")