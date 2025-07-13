#!/usr/bin/env python3
"""
Create investment income breakdown matching the exact spreadsheet format.
"""

from datetime import datetime
from vanguard_income_parser import parse_qfx_income, get_cusip_symbol_mapping, get_account_mapping

def create_spreadsheet_format_breakdown():
    """Create breakdown for retirement planning with tax optimization insights."""
    
    qfx_file = "/Users/mark/Documents/Retirement/Assets/2025-07/Vanguard_2025Q2.qfx"
    start_date = datetime(2025, 4, 1)
    end_date = datetime(2025, 6, 30)
    
    print("=" * 80)
    print("RETIREMENT PASSIVE INCOME ANALYSIS")
    print("Q2 2025 - Focus on Tax Optimization Opportunities")
    print("=" * 80)
    
    # Get data
    transactions = parse_qfx_income(qfx_file, start_date, end_date)
    cusip_mapping = get_cusip_symbol_mapping()
    account_mapping = get_account_mapping()
    
    # Track income by tax treatment for retirement planning
    income_categories = {
        'tax_free_forever': {
            'accounts': {
                'Vanguard Mark Roth IRA': 0.00,      # Roth IRA - tax-free forever
                'Vanguard Kumi Roth IRA': 0.00,      # Roth IRA - tax-free forever
                'Vanguard Joint (Municipal)': 0.00,   # Municipal bonds - federally tax-free
            },
            'funds': []
        },
        'tax_deferred': {
            'accounts': {
                'Vanguard Mark IRA': 0.00,           # Traditional IRA - taxed when withdrawn
                'Vanguard Kumi Rollover IRA': 0.00,  # Rollover IRA - taxed when withdrawn
            },
            'funds': []
        },
        'taxed_now': {
            'accounts': {
                'Vanguard Joint (Taxable)': 0.00,    # Regular investments - already taxed
            },
            'funds': []
        }
    }
    
    # Account ID to spreadsheet name mapping
    account_id_to_spreadsheet = {
        '22561601': 'Vanguard Mark IRA',           # Mark Traditional IRA
        '27194486': 'Vanguard Mark Roth IRA',      # Mark Roth IRA  
        '75550487': 'Vanguard Joint',              # Joint Brokerage
        '73309387': 'Vanguard Kumi Rollover IRA',  # Kumi Rollover IRA
        '78071718': 'Vanguard Kumi Roth IRA',      # Kumi Roth IRA
    }
    
    def is_tax_exempt_fund(cusip, fund_name):
        """Determine if a fund generates tax-exempt income."""
        tax_exempt_keywords = ['MUNICIPAL', 'MUN', 'CALIFORNIA', 'TAX EXEMPT']
        return any(keyword in fund_name.upper() for keyword in tax_exempt_keywords)
    
    print("\n=== PROCESSING TRANSACTIONS BY TAX TREATMENT ===")
    
    total_income = 0
    
    # Process each transaction
    for txn in transactions:
        account_id = txn['account_id']
        amount = float(txn['amount'])
        fund_name = cusip_mapping.get(txn['cusip'], f"CUSIP {txn['cusip']}")
        spreadsheet_account = account_id_to_spreadsheet.get(account_id, 'Unknown')
        total_income += amount
        
        fund_detail = {'name': fund_name, 'amount': amount, 'account': spreadsheet_account}
        
        if account_id in ['27194486', '78071718']:  # Roth IRAs
            # Roth IRA income = tax-free forever
            account_key = 'Vanguard Mark Roth IRA' if account_id == '27194486' else 'Vanguard Kumi Roth IRA'
            income_categories['tax_free_forever']['accounts'][account_key] += amount
            income_categories['tax_free_forever']['funds'].append(fund_detail)
            
        elif account_id in ['22561601', '73309387']:  # Traditional IRAs
            # Traditional IRA income = tax-deferred until withdrawal
            account_key = 'Vanguard Mark IRA' if account_id == '22561601' else 'Vanguard Kumi Rollover IRA'
            income_categories['tax_deferred']['accounts'][account_key] += amount
            income_categories['tax_deferred']['funds'].append(fund_detail)
            
        elif account_id == '75550487':  # Joint Brokerage
            if is_tax_exempt_fund(txn['cusip'], fund_name):
                # Municipal bonds = tax-free forever
                income_categories['tax_free_forever']['accounts']['Vanguard Joint (Municipal)'] += amount
                income_categories['tax_free_forever']['funds'].append(fund_detail)
            else:
                # Regular funds in taxable account = taxed now
                income_categories['taxed_now']['accounts']['Vanguard Joint (Taxable)'] += amount
                income_categories['taxed_now']['funds'].append(fund_detail)
        
        print(f"${amount:>8.2f} | {spreadsheet_account:<25} | {fund_name[:40]}")
    
    # Calculate totals by category
    tax_free_total = sum(income_categories['tax_free_forever']['accounts'].values())
    tax_deferred_total = sum(income_categories['tax_deferred']['accounts'].values())
    taxed_now_total = sum(income_categories['taxed_now']['accounts'].values())
    
    print(f"\n{'='*80}")
    print("RETIREMENT INCOME PLANNING SUMMARY")
    print(f"{'='*80}")
    
    print(f"\nTOTAL QUARTERLY PASSIVE INCOME: ${total_income:>10.2f}")
    print(f"Annualized Estimate:             ${total_income * 4:>10.2f}")
    
    print(f"\n{'='*80}")
    print("BREAKDOWN BY TAX TREATMENT IN RETIREMENT")
    print(f"{'='*80}")
    
    print(f"\nTAX-FREE FOREVER: ${tax_free_total:>10.2f} ({tax_free_total/total_income*100:5.1f}%)")
    for account, amount in income_categories['tax_free_forever']['accounts'].items():
        if amount > 0:
            print(f"  {account:<30} ${amount:>10.2f}")
    
    print(f"\nTAX-DEFERRED: ${tax_deferred_total:>10.2f} ({tax_deferred_total/total_income*100:5.1f}%)")
    for account, amount in income_categories['tax_deferred']['accounts'].items():
        if amount > 0:
            print(f"  {account:<30} ${amount:>10.2f}")
    
    print(f"\nTAXED NOW: ${taxed_now_total:>10.2f} ({taxed_now_total/total_income*100:5.1f}%)")
    for account, amount in income_categories['taxed_now']['accounts'].items():
        if amount > 0:
            print(f"  {account:<30} ${amount:>10.2f}")
    
    print(f"\n{'='*80}")
    print("TAX OPTIMIZATION OPPORTUNITIES")
    print(f"{'='*80}")
    
    print(f"\n🎯 ROTH IRA OPPORTUNITY:")
    roth_income = income_categories['tax_free_forever']['accounts']['Vanguard Mark Roth IRA'] + \
                  income_categories['tax_free_forever']['accounts']['Vanguard Kumi Roth IRA']
    if roth_income == 0:
        print("  ⚠️  NO INCOME from Roth IRAs! Consider moving to income-producing investments")
        print("     Current Roth IRA holdings are likely growth-focused")
        print("     Opportunity: Move dividend/bond funds INTO Roth IRAs for tax-free income")
    else:
        print(f"  ✅ Generating ${roth_income:.2f} tax-free income from Roth IRAs")
    
    print(f"\n💡 FUND ALLOCATION INSIGHTS:")
    print("  Income-producing funds that SHOULD be in Roth IRAs:")
    for fund in income_categories['tax_deferred']['funds']:
        if any(keyword in fund['name'].upper() for keyword in ['BOND', 'DIVIDEND', 'YIELD']):
            print(f"    • {fund['name'][:50]} (${fund['amount']:.2f})")
    
    print(f"\n📊 CURRENT EFFICIENCY:")
    efficiency = (tax_free_total / total_income) * 100
    print(f"  Tax-Free Income: {efficiency:.1f}% of total")
    print(f"  Goal: Maximize tax-free portion by moving income funds to Roth IRAs")
    
    print(f"\n{'='*80}")
    print("SPREADSHEET VALUES - JULY 1, 2025 COLUMN")
    print(f"{'='*80}")
    
    print("\nINVESTMENT INCOME")
    print(f"Tax-Free:                           ${tax_free_total:>10.2f}")
    print(f"Tax-Deferred:                       ${tax_deferred_total:>10.2f}")
    print(f"Taxed Now:                          ${taxed_now_total:>10.2f}")
    print(f"{'='*50}")
    print(f"TOTAL INCOME:                       ${total_income:>10.2f}")
    
    print(f"\n{'='*80}")
    print("DETAILED FUND BREAKDOWN")
    print(f"{'='*80}")
    
    for category, data in income_categories.items():
        if data['funds']:
            category_name = category.replace('_', ' ').title()
            category_total = sum(f['amount'] for f in data['funds'])
            print(f"\n{category_name} (${category_total:.2f}):")
            for fund in data['funds']:
                print(f"  ${fund['amount']:>8.2f} | {fund['name'][:50]}")
    
    return {
        'total_income': total_income,
        'tax_free_forever': tax_free_total,
        'tax_deferred': tax_deferred_total,
        'taxed_now': taxed_now_total,
        'categories': income_categories
    }

if __name__ == "__main__":
    create_spreadsheet_format_breakdown()