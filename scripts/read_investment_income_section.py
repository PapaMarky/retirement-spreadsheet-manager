#!/usr/bin/env python3
"""
Read the INVESTMENT INCOME section from the 2025 spreadsheet to see the exact structure.
"""

from financial_data_access import read_financial_data

def read_investment_income_section():
    """Read and display the INVESTMENT INCOME section structure from the spreadsheet."""
    try:
        print("Reading spreadsheet to find INVESTMENT INCOME section structure...")
        data = read_financial_data()
        
        if '2025' in data:
            sheet_data = data['2025']
            
            print("Searching for INVESTMENT INCOME section...")
            
            investment_income_found = False
            for i, row in enumerate(sheet_data):
                # Look for rows containing "INVESTMENT INCOME"
                if any(cell and 'INVESTMENT INCOME' in str(cell).upper() for cell in row):
                    investment_income_found = True
                    print(f"\nFound INVESTMENT INCOME section starting at row {i+1}")
                    
                    # Show the structure around this section
                    start_row = max(0, i-2)  # Show 2 rows before
                    end_row = min(len(sheet_data), i+15)  # Show next 15 rows
                    
                    print("\nSpreadsheet structure around INVESTMENT INCOME:")
                    print("=" * 100)
                    
                    for j in range(start_row, end_row):
                        if j < len(sheet_data):
                            row_data = sheet_data[j]
                            # Format each row nicely
                            formatted_row = []
                            for k, cell in enumerate(row_data):
                                if k < 11:  # Show first 11 columns (quarterly structure)
                                    cell_str = str(cell) if cell else ''
                                    formatted_row.append(f"{cell_str:<20}")
                            
                            print(f"Row {j+1:2d}: {''.join(formatted_row)}")
                    
                    break
            
            if not investment_income_found:
                print("INVESTMENT INCOME section not found. Showing all rows with 'INCOME':")
                for i, row in enumerate(sheet_data):
                    if any(cell and 'INCOME' in str(cell).upper() for cell in row):
                        print(f"Row {i+1}: {row}")
    
    except Exception as e:
        print(f"Error reading spreadsheet: {e}")

if __name__ == "__main__":
    read_investment_income_section()