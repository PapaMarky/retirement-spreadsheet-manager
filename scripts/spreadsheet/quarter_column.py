#!/usr/bin/env python3
"""
QuarterColumn class for representing quarterly data columns in spreadsheets.
Handles parsing of quarter descriptions and updating income data.
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class IncomeData:
    """Data class for quarterly income breakdown."""
    tax_free: float
    tax_deferred: float
    taxed_now: float
    
    @property
    def total(self) -> float:
        """Calculate total income across all categories."""
        return self.tax_free + self.tax_deferred + self.taxed_now
    
    def format_currency(self, amount: float) -> str:
        """Format amount as currency string."""
        return f"${amount:.2f}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'tax_free': self.tax_free,
            'tax_deferred': self.tax_deferred,
            'taxed_now': self.taxed_now,
            'total': self.total
        }


class QuarterColumn:
    """
    Represents a quarterly column that can accept income data.
    
    Parses quarter descriptions from header rows and provides methods
    to write income data to the correct cells.
    """
    
    def __init__(self, sheet_name: str, column_index: int, header_text: str):
        """
        Initialize quarter column.
        
        Args:
            sheet_name: Name of the parent sheet
            column_index: 0-based column index
            header_text: Header text to parse for quarter information
        """
        self.sheet_name = sheet_name
        self.column_index = column_index
        self.header_text = header_text
        self.year: Optional[int] = None
        self.quarter: Optional[int] = None
        
        self._parse_header()
    
    def _parse_header(self) -> None:
        """
        Parse the header text to extract year and quarter information.
        
        Supports patterns like:
        - "Oct, Nov, Dec (2024 Q4)"
        - "Jan, Feb, Mar (2025 Q1)"
        - "Q1 2025"
        - "2025-Q1"
        """
        if not self.header_text:
            return
        
        # Pattern 1: "Oct, Nov, Dec (2024 Q4)" or "Jan, Feb, Mar (2025 Q1)"
        match = re.search(r'\((\d{4})\s+Q(\d)\)', self.header_text)
        if match:
            self.year = int(match.group(1))
            self.quarter = int(match.group(2))
            return
        
        # Pattern 2: "Q1 2025" or "Q2 2024"
        match = re.search(r'Q(\d)\s+(\d{4})', self.header_text)
        if match:
            self.quarter = int(match.group(1))
            self.year = int(match.group(2))
            return
        
        # Pattern 3: "2025-Q1" or "2024-Q2"
        match = re.search(r'(\d{4})-Q(\d)', self.header_text)
        if match:
            self.year = int(match.group(1))
            self.quarter = int(match.group(2))
            return
        
        # If no pattern matches, leave year and quarter as None
    
    @property
    def is_valid(self) -> bool:
        """Check if this column has valid quarter information."""
        return self.year is not None and self.quarter is not None
    
    @property
    def quarter_key(self) -> str:
        """
        Get a unique key for this quarter.
        
        Returns:
            String key like "Q1" or "Q4_2024" for previous year Q4
        """
        if not self.is_valid:
            return f"INVALID_COL_{self.column_index}"
        
        # For previous year Q4 in current year sheet, use special key
        if hasattr(self, '_is_previous_year_q4') and self._is_previous_year_q4:
            return f"Q4_{self.year}"
        
        return f"Q{self.quarter}"
    
    @property
    def column_letter(self) -> str:
        """Get the Excel-style column letter (A, B, C, etc.)."""
        return chr(65 + self.column_index)
    
    def matches_quarter(self, year: int, quarter: int) -> bool:
        """
        Check if this column matches the specified year and quarter.
        
        Args:
            year: Year to match
            quarter: Quarter to match (1-4)
            
        Returns:
            True if this column matches the specified quarter
        """
        return self.year == year and self.quarter == quarter
    
    def update_income_data(self, base_sheet, income_section_row: int, income_data: IncomeData) -> bool:
        """
        Update the income data in this column.
        
        Args:
            base_sheet: BaseSheet instance for performing updates
            income_section_row: Row index where INVESTMENT INCOME section starts
            income_data: IncomeData object with values to write
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Calculate row offsets based on standard structure
            tax_free_row = income_section_row + 1      # "Tax-Free" row
            tax_deferred_row = income_section_row + 2  # "Tax-Deferred" row
            taxed_now_row = income_section_row + 3     # "Taxed Now" row
            # Note: Skip TOTAL INCOME row to preserve SUM formula
            
            # Prepare batch update
            updates = [
                {
                    'range': f"{self.column_letter}{tax_free_row + 1}",  # +1 for 1-based indexing
                    'values': [[income_data.format_currency(income_data.tax_free)]]
                },
                {
                    'range': f"{self.column_letter}{tax_deferred_row + 1}",
                    'values': [[income_data.format_currency(income_data.tax_deferred)]]
                },
                {
                    'range': f"{self.column_letter}{taxed_now_row + 1}",
                    'values': [[income_data.format_currency(income_data.taxed_now)]]
                }
            ]
            
            return base_sheet.batch_update(updates)
            
        except Exception as e:
            print(f"❌ Error updating income data in {self}: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation of the quarter column."""
        if self.is_valid:
            return f"QuarterColumn({self.year} Q{self.quarter} -> {self.sheet_name}:{self.column_letter})"
        else:
            return f"QuarterColumn(INVALID -> {self.sheet_name}:{self.column_letter})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"QuarterColumn(sheet='{self.sheet_name}', column={self.column_index}, "
                f"year={self.year}, quarter={self.quarter}, header='{self.header_text}')")
    
    def __eq__(self, other) -> bool:
        """Check equality with another QuarterColumn."""
        if not isinstance(other, QuarterColumn):
            return False
        return (self.year == other.year and 
                self.quarter == other.quarter and
                self.sheet_name == other.sheet_name)
    
    def __hash__(self) -> int:
        """Make QuarterColumn hashable for use in sets and dicts."""
        return hash((self.year, self.quarter, self.sheet_name))