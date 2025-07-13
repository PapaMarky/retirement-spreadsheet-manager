#!/usr/bin/env python3
"""
YearSheet class for handling annual data sheets in retirement planning spreadsheets.
Extends BaseSheet with specialized functionality for quarterly income data.
"""

import re
from typing import List, Dict, Optional
from .base_sheet import BaseSheet
from .quarter_column import QuarterColumn, IncomeData


class YearSheet(BaseSheet):
    """
    Represents an annual data sheet (e.g., "2025", "2024").
    
    Handles quarterly income data with dynamic column discovery
    and INVESTMENT INCOME section management.
    """
    
    def __init__(self, sheet_name: str, sheets_service, spreadsheet_id: str, dry_run: bool = False):
        """
        Initialize year sheet.
        
        Args:
            sheet_name: Name of the sheet tab (e.g., "2025")
            sheets_service: Google Sheets API service object
            spreadsheet_id: Google Sheets spreadsheet ID
            dry_run: If True, preview changes without applying
        """
        super().__init__(sheet_name, sheets_service, dry_run)
        self._spreadsheet_id = spreadsheet_id
        self._quarter_columns: Optional[Dict[str, QuarterColumn]] = None
        self._investment_income_row: Optional[int] = None
    
    @property
    def _get_spreadsheet_id(self) -> str:
        """Get the spreadsheet ID for this sheet."""
        return self._spreadsheet_id
    
    def validate_structure(self) -> bool:
        """
        Validate that this sheet has the expected year sheet structure.
        
        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check if we can find INVESTMENT INCOME section
            income_row = self.find_investment_income_section()
            if income_row is None:
                print(f"❌ No INVESTMENT INCOME section found in {self.sheet_name}")
                return False
            
            # Check if we can discover quarterly columns
            quarter_columns = self.discover_quarter_columns()
            if not quarter_columns:
                print(f"❌ No quarterly columns found in {self.sheet_name}")
                return False
            
            print(f"✅ {self.sheet_name} structure valid: INVESTMENT INCOME at row {income_row + 1}, {len(quarter_columns)} quarterly columns")
            return True
            
        except Exception as e:
            print(f"❌ Error validating {self.sheet_name} structure: {e}")
            return False
    
    def find_investment_income_section(self) -> Optional[int]:
        """
        Find the INVESTMENT INCOME section in this sheet.
        
        Returns:
            Row index (0-based) if found, None otherwise
        """
        if self._investment_income_row is None:
            self._investment_income_row = self.find_section_row("INVESTMENT INCOME")
        
        return self._investment_income_row
    
    def discover_quarter_columns(self) -> Dict[str, QuarterColumn]:
        """
        Discover quarterly columns by scanning header rows.
        
        Returns:
            Dictionary mapping quarter keys to QuarterColumn objects
        """
        if self._quarter_columns is not None:
            return self._quarter_columns
        
        self._quarter_columns = {}
        sheet_data = self.read_sheet_data()
        
        # Scan first few rows for quarterly patterns
        for row_idx in range(min(5, len(sheet_data))):
            row = sheet_data[row_idx]
            
            for col_idx, cell in enumerate(row):
                if cell and self._looks_like_quarter_header(str(cell)):
                    quarter_col = QuarterColumn(self.sheet_name, col_idx, str(cell))
                    
                    if quarter_col.is_valid:
                        key = quarter_col.quarter_key
                        self._quarter_columns[key] = quarter_col
                        print(f"   📅 Found {quarter_col.year} Q{quarter_col.quarter} in column {quarter_col.column_letter}")
        
        return self._quarter_columns
    
    def _looks_like_quarter_header(self, text: str) -> bool:
        """
        Check if text looks like a quarterly header.
        
        Args:
            text: Text to check
            
        Returns:
            True if text matches quarterly patterns
        """
        quarterly_patterns = [
            r'\(\d{4}\s+Q\d\)',           # "(2024 Q4)"
            r'Q\d\s+\d{4}',              # "Q1 2025"
            r'\d{4}-Q\d',                # "2025-Q1"
            r'(Jan|Apr|Jul|Oct).*\d{4}', # "Jan, Feb, Mar (2025 Q1)"
        ]
        
        for pattern in quarterly_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def get_quarter_column(self, year: int, quarter: int) -> Optional[QuarterColumn]:
        """
        Get the QuarterColumn for a specific year and quarter.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
            
        Returns:
            QuarterColumn if found, None otherwise
        """
        quarter_columns = self.discover_quarter_columns()
        quarter_key = f"{year}_Q{quarter}"
        
        return quarter_columns.get(quarter_key)
    
    def update_quarterly_income(self, year: int, quarter: int, income_data: IncomeData) -> bool:
        """
        Update income data for a specific quarter.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
            income_data: IncomeData object with values to write
            
        Returns:
            True if update successful, False otherwise
        """
        # Find the quarterly column
        quarter_col = self.get_quarter_column(year, quarter)
        if quarter_col is None:
            print(f"❌ No column found for {year} Q{quarter} in {self.sheet_name}")
            return False
        
        # Find the INVESTMENT INCOME section
        income_row = self.find_investment_income_section()
        if income_row is None:
            print(f"❌ No INVESTMENT INCOME section found in {self.sheet_name}")
            return False
        
        # Update the data
        if self.dry_run:
            print(f"  [DRY RUN] Would update {year} Q{quarter} in {self.sheet_name}:")
            print(f"    Tax-Free: {income_data.format_currency(income_data.tax_free)}")
            print(f"    Tax-Deferred: {income_data.format_currency(income_data.tax_deferred)}")
            print(f"    Taxed Now: {income_data.format_currency(income_data.taxed_now)}")
            return True
        
        return quarter_col.update_income_data(self, income_row, income_data)
    
    def get_available_quarters(self) -> List[str]:
        """
        Get list of available quarters in this sheet.
        
        Returns:
            List of quarter keys (e.g., ["2024_Q4", "2025_Q1", "2025_Q2"])
        """
        quarter_columns = self.discover_quarter_columns()
        return sorted(quarter_columns.keys())
    
    def clear_cache(self) -> None:
        """Clear all cached data to force re-discovery."""
        super().clear_cache()
        self._quarter_columns = None
        self._investment_income_row = None
    
    def __str__(self) -> str:
        """String representation of the year sheet."""
        return f"YearSheet('{self.sheet_name}')"