#!/usr/bin/env python3
"""
NetworthSpreadsheet class for managing the retirement planning Google Spreadsheet.
Main controller that discovers and coordinates YearSheet objects.
"""

import re
from typing import List, Dict, Optional, Set
from .year_sheet import YearSheet
from .quarter_column import QuarterColumn, IncomeData


class NetworthSpreadsheet:
    """
    Main controller for the retirement/net worth Google Spreadsheet.
    
    Discovers sheet tabs, creates YearSheet objects, and provides
    a unified interface for updating quarterly income data.
    """
    
    def __init__(self, spreadsheet_id: str, sheets_service, dry_run: bool = False):
        """
        Initialize networth spreadsheet controller.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheets_service: Google Sheets API service object
            dry_run: If True, preview changes without applying
        """
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service = sheets_service
        self.dry_run = dry_run
        self._sheets_discovered = False
        self._year_sheets: Optional[Dict[str, YearSheet]] = None
        self._quarter_map: Optional[Dict[str, QuarterColumn]] = None
    
    def discover_sheets(self) -> None:
        """
        Discover and classify all sheet tabs, creating appropriate sheet objects.
        
        Currently discovers YearSheet objects. Future plans:
        - GraphSheet: Handle chart/visualization sheets
        - OverviewSheet: Summary/dashboard sheets  
        - ReferenceSheet: Read-only reference sheets (Notes, Account Notes)
        
        Use get_year_sheets(), get_graph_sheets(), etc. to access discovered sheets.
        """
        if self._sheets_discovered:
            return
        
        self._sheets_discovered = True
        self._year_sheets = {}
        
        # Get all sheet metadata
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        
        sheets = spreadsheet.get('sheets', [])
        print(f"📋 Discovered {len(sheets)} sheet tabs in spreadsheet")
        
        for sheet in sheets:
            sheet_name = sheet['properties']['title']
            
            if self._is_year_sheet(sheet_name):
                year_sheet = YearSheet(sheet_name, self.sheets_service, self.spreadsheet_id, self.dry_run)
                
                # Validate the sheet structure
                if year_sheet.validate_structure():
                    self._year_sheets[sheet_name] = year_sheet
                    print(f"  ✅ Added YearSheet: {sheet_name}")
                else:
                    print(f"  ❌ Skipped invalid year sheet: {sheet_name}")
            else:
                print(f"  ℹ️  Skipped non-year sheet: {sheet_name}")
        
        print(f"📊 Created {len(self._year_sheets)} YearSheet objects")
    
    def _is_year_sheet(self, sheet_name: str) -> bool:
        """
        Determine if a sheet name represents a year sheet.
        
        Args:
            sheet_name: Name of the sheet tab
            
        Returns:
            True if this looks like a year sheet (e.g., "2025", "2024")
        """
        # Pattern: 4-digit year, possibly with spaces
        return bool(re.match(r'^\s*20\d{2}\s*$', sheet_name))
    
    def get_year_sheets(self) -> Dict[str, YearSheet]:
        """
        Get all discovered YearSheet objects.
        
        Returns:
            Dictionary mapping sheet names to YearSheet objects
        """
        self.discover_sheets()
        return self._year_sheets or {}
    
    def build_quarter_map(self) -> Dict[str, QuarterColumn]:
        """
        Build map of all quarterly columns across year sheets.
        
        Returns:
            Dictionary mapping quarter keys to QuarterColumn objects
        """
        if self._quarter_map is not None:
            return self._quarter_map
        
        self._quarter_map = {}
        year_sheets = self.get_year_sheets()
        
        print("🗺️  Building quarter map...")
        
        for sheet_name, year_sheet in year_sheets.items():
            quarter_columns = year_sheet.discover_quarter_columns()
            
            for quarter_key, quarter_col in quarter_columns.items():
                if quarter_key in self._quarter_map:
                    existing = self._quarter_map[quarter_key]
                    print(f"  ⚠️  Duplicate quarter {quarter_key}: {existing} vs {quarter_col}")
                else:
                    self._quarter_map[quarter_key] = quarter_col
        
        print(f"📅 Quarter map contains {len(self._quarter_map)} quarterly columns")
        return self._quarter_map
    
    def get_year_sheet(self, year: int) -> Optional[YearSheet]:
        """
        Get the YearSheet for a specific year.
        
        Args:
            year: Year to find (e.g., 2024, 2025)
            
        Returns:
            YearSheet if found, None otherwise
        """
        year_sheets = self.get_year_sheets()
        
        # Try exact match first
        year_str = str(year)
        if year_str in year_sheets:
            return year_sheets[year_str]
        
        # Try with whitespace variations
        for sheet_name, year_sheet in year_sheets.items():
            if sheet_name.strip() == year_str:
                return year_sheet
        
        return None
    
    def get_quarter_column(self, year: int, quarter: int) -> Optional[QuarterColumn]:
        """
        Get the QuarterColumn for a specific year and quarter.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
            
        Returns:
            QuarterColumn if found, None otherwise
        """
        quarter_map = self.build_quarter_map()
        quarter_key = f"{year}_Q{quarter}"
        
        return quarter_map.get(quarter_key)
    
    def update_quarterly_income(self, year: int, quarter: int, income_data: IncomeData) -> bool:
        """
        Update income data for a specific quarter across all relevant sheets.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
            income_data: IncomeData object with values to write
            
        Returns:
            True if update successful, False otherwise
        """
        print(f"💰 Updating income for {year} Q{quarter}")
        
        # Find the quarter column
        quarter_col = self.get_quarter_column(year, quarter)
        if quarter_col is None:
            print(f"❌ No column found for {year} Q{quarter}")
            return False
        
        # Find the corresponding year sheet
        year_sheet = self.get_year_sheet(year)
        if year_sheet is None:
            print(f"❌ No year sheet found for {year}")
            return False
        
        # Perform the update
        return year_sheet.update_quarterly_income(year, quarter, income_data)
    
    def get_available_quarters(self) -> List[str]:
        """
        Get list of all available quarters across all year sheets.
        
        Returns:
            Sorted list of quarter keys (e.g., ["2024_Q4", "2025_Q1", "2025_Q2"])
        """
        quarter_map = self.build_quarter_map()
        return sorted(quarter_map.keys())
    
    def get_years_with_data(self) -> Set[int]:
        """
        Get set of years that have data sheets available.
        
        Returns:
            Set of years with YearSheet objects
        """
        year_sheets = self.get_year_sheets()
        years = set()
        
        for sheet_name in year_sheets.keys():
            # Extract year from sheet name
            match = re.match(r'^\s*(20\d{2})\s*$', sheet_name)
            if match:
                years.add(int(match.group(1)))
        
        return years
    
    def validate_all_sheets(self) -> bool:
        """
        Validate structure of all discovered sheets.
        
        Currently validates YearSheet objects. Future plans:
        - GraphSheet: Validate chart/visualization sheet structure
        - OverviewSheet: Validate summary/dashboard sheet structure
        - ReferenceSheet: Validate read-only reference sheet structure
        
        Returns:
            True if all sheets are valid, False otherwise
        """
        year_sheets = self.get_year_sheets()
        
        if not year_sheets:
            print("❌ No year sheets found to validate")
            return False
        
        print(f"🔍 Validating {len(year_sheets)} year sheets...")
        
        all_valid = True
        for sheet_name, year_sheet in year_sheets.items():
            if not year_sheet.validate_structure():
                all_valid = False
        
        if all_valid:
            print("✅ All year sheets validated successfully")
        else:
            print("❌ Some year sheets failed validation")
        
        return all_valid
    
    def clear_cache(self) -> None:
        """Clear all cached data to force re-discovery."""
        # Clear caches in existing year sheets before clearing references
        if self._year_sheets:
            for year_sheet in self._year_sheets.values():
                year_sheet.clear_cache()
        
        self._sheets_discovered = False
        self._year_sheets = None
        self._quarter_map = None
    
    def __str__(self) -> str:
        """String representation of the networth spreadsheet."""
        year_count = len(self._year_sheets) if self._year_sheets else "unknown"
        return f"NetworthSpreadsheet({year_count} year sheets)"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"NetworthSpreadsheet(spreadsheet_id='{self.spreadsheet_id}', dry_run={self.dry_run})"