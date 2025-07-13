#!/usr/bin/env python3
"""
Break down Q2 2025 investment income by taxable vs non-taxable status.
"""

from datetime import datetime
from vanguard_income_parser import parse_qfx_income, get_cusip_symbol_mapping, get_account_mapping

def analyze_taxable_vs_nontaxable_income():
    """Analyze investment income by tax status."""
    
    qfx_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 6, 30)
    
    print("=" * 80)
    print("Q2 2025 INVESTMENT INCOME: TAXABLE vs NON-TAXABLE BREAKDOWN")
    print("=" * 80)
    
    # Get data
    transactions = parse_qfx_income(qfx_file, start_date, end_date)
    cusip_mapping = get_cusip_symbol_mapping()
    account_mapping = get_account_mapping()
    
    # Define account tax characteristics
    account_tax_status = {
        '22561601': 'Tax-Deferred',      # Mark Traditional IRA - grows tax-deferred, taxed on withdrawal
        '27194486': 'Tax-Free',          # Mark Roth IRA - tax-free growth and withdrawal
        '75550487': 'Taxable',           # Joint Brokerage - taxable income
        '73309387': 'Tax-Deferred',      # Kumi Rollover IRA - grows tax-deferred
        '78071718': 'Tax-Free',          # Kumi Roth IRA - tax-free growth and withdrawal
    }
    
    # Define fund tax characteristics (for funds in taxable accounts)
    def is_tax_exempt_fund(cusip, fund_name):
        """Determine if a fund generates tax-exempt income."""
        # Municipal bond funds generate tax-exempt income
        tax_exempt_keywords = ['MUNICIPAL', 'MUN', 'CALIFORNIA', 'TAX EXEMPT']
        return any(keyword in fund_name.upper() for keyword in tax_exempt_keywords)
    
    # Categorize income
    taxable_income = 0           # Income taxed as ordinary income in current year
    tax_exempt_income = 0        # Municipal bond income (federally tax-exempt)
    tax_deferred_income = 0      # IRA income (taxed when withdrawn)
    tax_free_income = 0          # Roth IRA income (never taxed)
    
    detailed_breakdown = {
        'Taxable (Current Year)': [],
        'Tax-Exempt (Municipal)': [],
        'Tax-Deferred (Traditional IRA)': [],
        'Tax-Free (Roth IRA)': []
    }
    
    print("\n=== DETAILED TRANSACTION ANALYSIS ===")
    
    for txn in transactions:
        account_id = txn['account_id']
        account_name = account_mapping.get(account_id, f"Account {account_id}")
        fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
        amount = txn['amount']
        tax_status = account_tax_status.get(account_id, 'Unknown')
        
        print(f"${amount:>8.2f} | {account_name:<30} | {fund_name[:40]:<40} | {tax_status}")
        
        if tax_status == 'Taxable':
            if is_tax_exempt_fund(txn['cusip'], fund_name):
                # Municipal bonds in taxable account = tax-exempt income
                tax_exempt_income += amount
                detailed_breakdown['Tax-Exempt (Municipal)'].append({
                    'fund': fund_name, 'amount': amount, 'account': account_name
                })
            else:
                # Regular funds in taxable account = taxable income
                taxable_income += amount
                detailed_breakdown['Taxable (Current Year)'].append({
                    'fund': fund_name, 'amount': amount, 'account': account_name
                })
        elif tax_status == 'Tax-Deferred':
            # Traditional IRA = tax-deferred (taxed when withdrawn)
            tax_deferred_income += amount
            detailed_breakdown['Tax-Deferred (Traditional IRA)'].append({
                'fund': fund_name, 'amount': amount, 'account': account_name
            })
        elif tax_status == 'Tax-Free':
            # Roth IRA = tax-free
            tax_free_income += amount
            detailed_breakdown['Tax-Free (Roth IRA)'].append({
                'fund': fund_name, 'amount': amount, 'account': account_name
            })
    
    total_income = taxable_income + tax_exempt_income + tax_deferred_income + tax_free_income
    
    print(f"\n{'='*80}")
    print("INCOME SUMMARY BY TAX STATUS")
    print(f"{'='*80}")
    
    print(f"\nTaxable Income (Current Year):      ${taxable_income:>10.2f} ({taxable_income/total_income*100:>5.1f}%)")
    print(f"Tax-Exempt Income (Municipal):     ${tax_exempt_income:>10.2f} ({tax_exempt_income/total_income*100:>5.1f}%)")
    print(f"Tax-Deferred Income (Trad IRA):    ${tax_deferred_income:>10.2f} ({tax_deferred_income/total_income*100:>5.1f}%)")
    print(f"Tax-Free Income (Roth IRA):        ${tax_free_income:>10.2f} ({tax_free_income/total_income*100:>5.1f}%)")
    print(f"{'='*60}")
    print(f"Total Investment Income:            ${total_income:>10.2f}")
    
    print(f"\n=== FOR SPREADSHEET INPUT ===")
    print("July 1, 2025 Column - INVESTMENT INCOME section:")
    print()
    
    # For tax reporting purposes, common breakdown:
    current_year_taxable = taxable_income  # Taxable in current year
    non_taxable_current = tax_exempt_income  # Tax-exempt (municipal bonds)
    
    print(f"Taxable Investment Income:          ${current_year_taxable:>10.2f}")
    print(f"Non-Taxable Investment Income:      ${non_taxable_current:>10.2f}")
    print()
    print("Notes for tax planning:")
    print(f"- Tax-Deferred (Traditional IRA):  ${tax_deferred_income:>10.2f} (taxed when withdrawn)")
    print(f"- Tax-Free (Roth IRA):              ${tax_free_income:>10.2f} (never taxed)")
    
    print(f"\n=== DETAILED BREAKDOWN ===")
    
    for category, items in detailed_breakdown.items():
        if items:
            category_total = sum(item['amount'] for item in items)
            print(f"\n{category} (${category_total:.2f}):")
            for item in items:
                print(f"  ${item['amount']:>8.2f} | {item['fund'][:50]}")
    
    print(f"\n=== TAX PLANNING INSIGHTS ===")
    print(f"• Municipal bond income (${tax_exempt_income:.2f}) is federally tax-exempt")
    print(f"• Traditional IRA income (${tax_deferred_income:.2f}) grows tax-deferred")
    print(f"• Roth IRA income (${tax_free_income:.2f}) is permanently tax-free")
    print(f"• Only ${current_year_taxable:.2f} is taxable as ordinary income in 2025")
    
    # Calculate effective tax rate
    total_current_taxable = current_year_taxable
    print(f"\nCurrent year taxable income: {total_current_taxable/total_income*100:.1f}% of total investment income")
    
    return {
        'taxable_current_year': current_year_taxable,
        'non_taxable_current_year': non_taxable_current,
        'tax_deferred': tax_deferred_income,
        'tax_free': tax_free_income,
        'total': total_income
    }

if __name__ == "__main__":
    analyze_taxable_vs_nontaxable_income()