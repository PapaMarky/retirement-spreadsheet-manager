#!/usr/bin/env python3
"""
Base class for all Google Sheets tab operations.
Provides common functionality for reading, writing, and pattern matching.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import re


class BaseSheet(ABC):
    """
    Abstract base class for all Google Sheets tab operations.
    
    Provides common functionality for reading/writing cell ranges,
    batch updates, dry-run mode, and text pattern matching.
    """
    
    def __init__(self, sheet_name: str, sheets_service, dry_run: bool = False):
        """
        Initialize base sheet.
        
        Args:
            sheet_name: Name of the sheet tab
            sheets_service: Google Sheets API service object
            dry_run: If True, preview changes without applying
        """
        self.sheet_name = sheet_name
        self.sheets_service = sheets_service
        self.dry_run = dry_run
        self._sheet_data: Optional[List[List[str]]] = None
        
    def read_sheet_data(self, range_spec: str = "A:Z") -> List[List[str]]:
        """
        Read data from the sheet and cache it.
        
        Args:
            range_spec: Range specification (e.g., "A:Z", "A1:C10")
            
        Returns:
            2D list of cell values
        """
        if self._sheet_data is None:
            full_range = f"{self.sheet_name}!{range_spec}"
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self._get_spreadsheet_id(),
                range=full_range
            ).execute()
            
            self._sheet_data = result.get('values', [])
        
        return self._sheet_data
    
    def find_text_pattern(self, pattern: str, start_row: int = 0) -> Optional[Tuple[int, int]]:
        """
        Find the first occurrence of a text pattern in the sheet.
        
        Args:
            pattern: Text pattern to search for (supports regex)
            start_row: Row to start searching from (0-indexed)
            
        Returns:
            (row, column) tuple if found, None otherwise
        """
        sheet_data = self.read_sheet_data()
        
        for row_idx in range(start_row, len(sheet_data)):
            row = sheet_data[row_idx]
            for col_idx, cell in enumerate(row):
                if cell and re.search(pattern, str(cell), re.IGNORECASE):
                    return (row_idx, col_idx)
        
        return None
    
    def find_section_row(self, section_name: str) -> Optional[int]:
        """
        Find the row containing a specific section header.
        
        Args:
            section_name: Name of section to find (e.g., "INVESTMENT INCOME")
            
        Returns:
            Row index (0-based) if found, None otherwise
        """
        location = self.find_text_pattern(section_name)
        return location[0] if location else None
    
    def read_cell_range(self, range_spec: str) -> List[List[str]]:
        """
        Read a specific range of cells.
        
        Args:
            range_spec: Range specification (e.g., "A1:C10")
            
        Returns:
            2D list of cell values in the range
        """
        full_range = f"{self.sheet_name}!{range_spec}"
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=self._get_spreadsheet_id(),
            range=full_range
        ).execute()
        
        return result.get('values', [])
    
    def write_cell_range(self, range_spec: str, values: List[List[Any]]) -> bool:
        """
        Write data to a specific range of cells.
        
        Args:
            range_spec: Range specification (e.g., "A1:C10")
            values: 2D list of values to write
            
        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would write to {self.sheet_name}!{range_spec}: {values}")
            return True
        
        try:
            full_range = f"{self.sheet_name}!{range_spec}"
            body = {
                'values': values
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self._get_spreadsheet_id(),
                range=full_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Invalidate cached data since we modified the sheet
            self.clear_cache()
            
            return True
            
        except Exception as e:
            print(f"Error writing to {self.sheet_name}!{range_spec}: {e}")
            return False
    
    def batch_update(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Perform multiple cell updates in a single batch operation.
        
        Args:
            updates: List of update dictionaries with 'range' and 'values' keys
            
        Returns:
            True if successful, False otherwise
        """
        if not updates:
            return True
            
        if self.dry_run:
            print(f"  [DRY RUN] Would batch update {len(updates)} ranges in {self.sheet_name}:")
            for update in updates:
                print(f"    {update['range']}: {update['values']}")
            return True
        
        try:
            # Convert to Google Sheets batch update format
            batch_updates = []
            for update in updates:
                batch_updates.append({
                    'range': f"{self.sheet_name}!{update['range']}",
                    'values': update['values']
                })
            
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': batch_updates
            }
            
            self.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=self._get_spreadsheet_id(),
                body=body
            ).execute()
            
            # Invalidate cached data since we modified the sheet
            self.clear_cache()
            
            print(f"✅ Updated {len(updates)} ranges in {self.sheet_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error batch updating {self.sheet_name}: {e}")
            return False
    
    def get_row_data(self, row_index: int) -> List[str]:
        """
        Get data from a specific row.
        
        Args:
            row_index: 0-based row index
            
        Returns:
            List of cell values in the row
        """
        sheet_data = self.read_sheet_data()
        if row_index < len(sheet_data):
            return sheet_data[row_index]
        return []
    
    def clear_cache(self) -> None:
        """Clear cached sheet data to force re-read on next access."""
        self._sheet_data = None
    
    @abstractmethod
    def _get_spreadsheet_id(self) -> str:
        """
        Get the spreadsheet ID for this sheet.
        
        Returns:
            Google Sheets spreadsheet ID
        """
        pass
    
    @abstractmethod
    def validate_structure(self) -> bool:
        """
        Validate that this sheet has the expected structure.
        
        Returns:
            True if structure is valid, False otherwise
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the sheet."""
        return f"{self.__class__.__name__}('{self.sheet_name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the sheet."""
        return f"{self.__class__.__name__}(sheet_name='{self.sheet_name}', dry_run={self.dry_run})"