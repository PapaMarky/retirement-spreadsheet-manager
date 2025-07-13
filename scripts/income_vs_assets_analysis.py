#!/usr/bin/env python3
"""
Analyze Q2 2025 investment income in context of total family assets.
"""

from financial_data_access import read_financial_data
import re

def parse_dollar_amount(amount_str):
    """Parse dollar amount string to float."""
    if not amount_str or amount_str.strip() == '' or amount_str == '$0.00':
        return 0.0
    
    # Remove dollar signs, commas, and whitespace
    cleaned = re.sub(r'[$,\s]', '', str(amount_str))
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def analyze_income_vs_assets():
    """Analyze Q2 investment income in context of total family assets."""
    
    print("=" * 80)
    print("Q2 2025 INVESTMENT INCOME vs TOTAL FAMILY ASSETS")
    print("=" * 80)
    
    # Get spreadsheet data
    try:
        data = read_financial_data()
        sheet_2025 = data.get('2025', [])
        
        # Q2 investment income from our analysis
        q2_investment_income = 6111.42
        annualized_investment_income = q2_investment_income * 4
        
        print(f"\n=== INVESTMENT INCOME (Q2 2025) ===")
        print(f"Quarterly Investment Income (Vanguard): ${q2_investment_income:,.2f}")
        print(f"Annualized Investment Income Estimate: ${annualized_investment_income:,.2f}")
        
        # Parse asset values from April 1 column (Q2 start)
        print(f"\n=== FAMILY ASSETS (April 1, 2025) ===")
        
        liquid_assets = 0
        near_liquid_assets = 0
        retirement_assets = 0
        
        april_col = 3  # April 1 data is in column index 3
        
        for row in sheet_2025:
            if len(row) > april_col and len(row) > 0:
                description = row[0] if row[0] else ''
                value_str = row[april_col] if len(row) > april_col else ''
                value = parse_dollar_amount(value_str)
                
                if value > 0:
                    print(f"{description:<40} ${value:>12,.2f}")
                    
                    # Categorize assets
                    desc_lower = description.lower()
                    if any(keyword in desc_lower for keyword in ['checking', 'savings', 'japan']):
                        liquid_assets += value
                    elif any(keyword in desc_lower for keyword in ['etrade', 'vanguard', 'scholarshare', 'deere']):
                        if 'retirement' in desc_lower or 'ira' in desc_lower or '401' in desc_lower:
                            retirement_assets += value
                        else:
                            near_liquid_assets += value
        
        total_assets = liquid_assets + near_liquid_assets + retirement_assets
        
        print(f"\n=== ASSET CATEGORY TOTALS ===")
        print(f"Liquid Assets:                      ${liquid_assets:>12,.2f}")
        print(f"Near Liquid Assets:                 ${near_liquid_assets:>12,.2f}")
        print(f"Retirement Assets (visible):        ${retirement_assets:>12,.2f}")
        print(f"{'='*55}")
        print(f"Total Visible Assets:               ${total_assets:>12,.2f}")
        
        # Add known Vanguard values from account balances
        vanguard_total = 1599587.71 + 39934.82 + 718616.76 + 85606.99 + 42549.57  # From account list
        
        print(f"\n=== VANGUARD ACCOUNT TOTALS (from account list) ===")
        print(f"Mark Traditional IRA (22561601):   $  1,599,587.71")
        print(f"Mark Roth IRA (27194486):          $     39,934.82")
        print(f"Joint Brokerage (75550487):        $    718,616.76")
        print(f"Kumi Rollover IRA (73309387):      $     85,606.99")
        print(f"Kumi Roth IRA (78071718):          $     42,549.57")
        print(f"{'='*55}")
        print(f"Total Vanguard Assets:              ${vanguard_total:>12,.2f}")
        
        print(f"\n=== INVESTMENT INCOME ANALYSIS ===")
        
        # Calculate yield on Vanguard assets
        vanguard_quarterly_yield = (q2_investment_income / vanguard_total) * 100
        vanguard_annual_yield = vanguard_quarterly_yield * 4
        
        print(f"Q2 Income as % of Vanguard Assets:  {vanguard_quarterly_yield:>12.3f}%")
        print(f"Annualized Yield on Vanguard:      {vanguard_annual_yield:>12.3f}%")
        
        # Calculate income as percentage of total wealth
        estimated_total_wealth = total_assets + vanguard_total
        income_vs_total_wealth = (annualized_investment_income / estimated_total_wealth) * 100
        
        print(f"\nEstimated Total Family Wealth:      ${estimated_total_wealth:>12,.2f}")
        print(f"Annual Investment Income:           ${annualized_investment_income:>12,.2f}")
        print(f"Investment Income vs Total Wealth:  {income_vs_total_wealth:>12.3f}%")
        
        print(f"\n=== KEY INSIGHTS ===")
        print(f"• Vanguard accounts generate ~{vanguard_annual_yield:.1f}% annual yield")
        print(f"• Investment income represents ~{income_vs_total_wealth:.1f}% of total wealth")
        print(f"• Quarterly passive income: ${q2_investment_income:,.0f}")
        print(f"• Monthly passive income average: ${q2_investment_income/3:,.0f}")
        
        # Compare to typical retirement withdrawal rates
        print(f"\n=== RETIREMENT PLANNING CONTEXT ===")
        four_percent_rule = estimated_total_wealth * 0.04
        three_percent_rule = estimated_total_wealth * 0.03
        
        print(f"4% Rule Annual Withdrawal:          ${four_percent_rule:>12,.2f}")
        print(f"3% Rule Annual Withdrawal:          ${three_percent_rule:>12,.2f}")
        print(f"Current Investment Income:          ${annualized_investment_income:>12,.2f}")
        print(f"")
        print(f"Investment income covers {(annualized_investment_income/four_percent_rule)*100:.1f}% of 4% rule")
        print(f"Investment income covers {(annualized_investment_income/three_percent_rule)*100:.1f}% of 3% rule")
        
    except Exception as e:
        print(f"Error analyzing data: {e}")

if __name__ == "__main__":
    analyze_income_vs_assets()