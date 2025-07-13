#!/usr/bin/env python3
"""
QFXDataFile class for parsing QFX files and extracting investment income data.
Bridges QFX files to the spreadsheet infrastructure.
"""

import re
import os
import sys
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict
from decimal import Decimal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofxtools.Parser import OFXTree
import logging

from spreadsheet.quarter_column import IncomeData

# Configure logging to suppress ofxtools noise
logging.getLogger('ofxtools.Parser').setLevel(logging.WARNING)
logging.getLogger('ofxtools.Types').setLevel(logging.WARNING)


class QFXDataFile:
    """
    Represents and parses a single QFX file for investment income data.
    
    Handles filename parsing, date range calculation, transaction extraction,
    and tax category breakdown using existing vanguard_income_parser logic.
    """
    
    def __init__(self, file_path: str, account_tax_treatment: Optional[Dict[str, str]] = None):
        """
        Initialize QFX data file.
        
        Args:
            file_path: Path to the QFX file
            account_tax_treatment: Optional mapping of account IDs to tax treatment
                                 (if not provided, will try to import from config)
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self._account_tax_treatment = account_tax_treatment
        self._year: Optional[int] = None
        self._quarter: Optional[int] = None
        self._transactions: Optional[List[Dict]] = None
        self._income_data: Optional[IncomeData] = None
        
        self._parse_filename()
    
    def _parse_filename(self) -> None:
        """
        Parse filename to extract year and quarter information.
        
        Supports formats like:
        - "2025-Q2.qfx" 
        - "2024-Q4.qfx"
        - "Q1-2025.qfx"
        """
        # Pattern 1: "2025-Q2.qfx" or "2024-Q4.qfx"
        match = re.search(r'(\d{4})-Q(\d)', self.filename)
        if match:
            self._year = int(match.group(1))
            self._quarter = int(match.group(2))
            return
        
        # Pattern 2: "Q2-2025.qfx" or "Q1-2024.qfx"
        match = re.search(r'Q(\d)-(\d{4})', self.filename)
        if match:
            self._quarter = int(match.group(1))
            self._year = int(match.group(2))
            return
        
        # Pattern 3: Just year "2025.qfx" - assume Q1
        match = re.search(r'(\d{4})\.qfx', self.filename)
        if match:
            self._year = int(match.group(1))
            self._quarter = 1  # Default to Q1 if no quarter specified
            return
    
    @property
    def year(self) -> Optional[int]:
        """Get the year extracted from filename."""
        return self._year
    
    @property
    def quarter(self) -> Optional[int]:
        """Get the quarter extracted from filename."""
        return self._quarter
    
    @property
    def is_valid(self) -> bool:
        """Check if the filename was successfully parsed."""
        return self._year is not None and self._quarter is not None
    
    @property
    def quarter_key(self) -> str:
        """Get a unique key for this quarter."""
        if not self.is_valid:
            return f"INVALID_FILE_{self.filename}"
        return f"{self._year}_Q{self._quarter}"
    
    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Calculate the date range for this quarter.
        
        Returns:
            Tuple of (start_date, end_date) for the quarter
            
        Raises:
            ValueError: If year/quarter are not valid
        """
        if not self.is_valid:
            raise ValueError(f"Cannot calculate date range for invalid file: {self.filename}")
        
        # Calculate quarter date ranges
        quarter_starts = {
            1: (1, 1),    # Q1: Jan 1 - Mar 31
            2: (4, 1),    # Q2: Apr 1 - Jun 30
            3: (7, 1),    # Q3: Jul 1 - Sep 30
            4: (10, 1)    # Q4: Oct 1 - Dec 31
        }
        
        quarter_ends = {
            1: (3, 31),   # Q1: Jan 1 - Mar 31
            2: (6, 30),   # Q2: Apr 1 - Jun 30
            3: (9, 30),   # Q3: Jul 1 - Sep 30
            4: (12, 31)   # Q4: Oct 1 - Dec 31
        }
        
        start_month, start_day = quarter_starts[self._quarter]
        end_month, end_day = quarter_ends[self._quarter]
        
        start_date = datetime(self._year, start_month, start_day)
        end_date = datetime(self._year, end_month, end_day)
        
        return start_date, end_date
    
    def parse_transactions(self) -> List[Dict]:
        """
        Parse QFX file and extract income transactions for this quarter.
        
        Returns:
            List of income transactions within the quarter date range
        """
        if self._transactions is not None:
            return self._transactions
        
        if not self.is_valid:
            raise ValueError(f"Cannot parse invalid QFX file: {self.filename}")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"QFX file not found: {self.file_path}")
        
        # Get date range for this quarter
        start_date, end_date = self.get_date_range()
        
        # Parse QFX file using ofxtools
        self._transactions = self._parse_qfx_file(start_date, end_date)
        
        return self._transactions
    
    def _parse_qfx_file(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Parse QFX file using ofxtools and extract investment income transactions.
        
        Args:
            start_date: Start date for filtering transactions
            end_date: End date for filtering transactions
            
        Returns:
            List of income transactions within date range
        """
        try:
            parser = OFXTree()
            parser.parse(self.file_path)
            ofx = parser.convert()
        except Exception as e:
            raise ValueError(f"Failed to parse QFX file {self.file_path}: {e}")
        
        transactions = []
        
        # Process investment statements in the QFX file
        for statement in ofx.statements:
            # Skip non-investment statements
            if not hasattr(statement, 'invtranlist'):
                continue
                
            # Extract account ID from investment account
            account_id = statement.invacctfrom.acctid if hasattr(statement, 'invacctfrom') else 'Unknown'
            
            # Process investment transactions
            for inv_txn in statement.invtranlist:
                # Look for income transactions (INCOME type)
                if hasattr(inv_txn, 'income') and inv_txn.income:
                    income_txn = inv_txn.income
                    
                    # Extract transaction details
                    txn_date = income_txn.invtran.dttrade if hasattr(income_txn.invtran, 'dttrade') else None
                    
                    if txn_date and start_date <= txn_date <= end_date:
                        transaction = {
                            'account_id': account_id,
                            'date': txn_date,
                            'fitid': income_txn.invtran.fitid if hasattr(income_txn.invtran, 'fitid') else 'Unknown',
                            'memo': income_txn.invtran.memo if hasattr(income_txn.invtran, 'memo') else 'Unknown',
                            'amount': float(income_txn.total) if hasattr(income_txn, 'total') else 0.0,
                            'cusip': income_txn.secid.uniqueid if hasattr(income_txn, 'secid') and hasattr(income_txn.secid, 'uniqueid') else 'Unknown',
                            'income_type': income_txn.incometype if hasattr(income_txn, 'incometype') else 'Unknown'
                        }
                        transactions.append(transaction)
        
        # Sort by account and date
        return sorted(transactions, key=lambda x: (x['account_id'], x['date']))
    
    def _get_account_tax_treatment(self) -> Dict[str, str]:
        """
        Get account tax treatment mapping.
        
        Returns:
            Dictionary mapping account IDs to tax treatment
        """
        if self._account_tax_treatment is not None:
            return self._account_tax_treatment
        
        # Try to import from config
        try:
            from config import ACCOUNT_TAX_TREATMENT
            return ACCOUNT_TAX_TREATMENT
        except ImportError:
            print("Warning: Could not import ACCOUNT_TAX_TREATMENT from config")
            return {}
    
    def _is_tax_exempt_fund(self, cusip: str, fund_name: str) -> bool:
        """
        Determine if a fund generates tax-exempt income.
        
        Args:
            cusip: Fund CUSIP identifier
            fund_name: Fund name/description
            
        Returns:
            True if fund generates tax-exempt income
        """
        if not fund_name:
            return False
        
        tax_exempt_keywords = ['MUNICIPAL', 'MUN', 'CALIFORNIA', 'TAX EXEMPT']
        return any(keyword in fund_name.upper() for keyword in tax_exempt_keywords)
    
    def calculate_income_breakdown(self) -> IncomeData:
        """
        Calculate tax-categorized income breakdown for this quarter.
        
        Returns:
            IncomeData object with tax-free, tax-deferred, and taxed-now totals
        """
        if self._income_data is not None:
            return self._income_data
        
        transactions = self.parse_transactions()
        account_tax_treatment = self._get_account_tax_treatment()
        
        # Initialize totals
        tax_free_total = Decimal('0.00')
        tax_deferred_total = Decimal('0.00')
        taxed_now_total = Decimal('0.00')
        
        # Get CUSIP mappings for fund names
        try:
            from config import CUSIP_MAPPINGS
            cusip_mappings = CUSIP_MAPPINGS
        except ImportError:
            print("Warning: Could not import CUSIP_MAPPINGS from config")
            cusip_mappings = {}
        
        # Process each transaction
        for txn in transactions:
            account_id = txn['account_id']
            amount = txn['amount']
            cusip = txn.get('cusip', 'Unknown')
            
            # Get fund name for tax-exempt checking
            fund_name = cusip_mappings.get(cusip, f"Unknown Fund ({cusip})")
            
            # Determine tax treatment based on account
            tax_treatment = account_tax_treatment.get(account_id, 'Unknown')
            
            if tax_treatment == 'Tax-Free':
                tax_free_total += amount
            elif tax_treatment == 'Tax-Deferred':
                tax_deferred_total += amount
            elif tax_treatment == 'Taxed-Now':
                # Check if this is a tax-exempt fund (municipal bonds)
                if self._is_tax_exempt_fund(cusip, fund_name):
                    tax_free_total += amount  # Municipal bonds are tax-free
                else:
                    taxed_now_total += amount  # Regular investments
            else:
                print(f"Warning: Unknown tax treatment for account {account_id}, defaulting to Taxed-Now")
                taxed_now_total += amount  # Default to taxed now
        
        # Create IncomeData object
        self._income_data = IncomeData(
            tax_free=float(tax_free_total),
            tax_deferred=float(tax_deferred_total),
            taxed_now=float(taxed_now_total)
        )
        
        return self._income_data
    
    def get_transaction_summary(self) -> Dict:
        """
        Get summary information about the transactions in this file.
        
        Returns:
            Dictionary with transaction counts and totals
        """
        transactions = self.parse_transactions()
        income_data = self.calculate_income_breakdown()
        
        account_totals = {}
        for txn in transactions:
            account_id = txn['account_id']
            amount = txn['amount']
            
            if account_id not in account_totals:
                account_totals[account_id] = {
                    'count': 0,
                    'total': Decimal('0.00')
                }
            
            account_totals[account_id]['count'] += 1
            account_totals[account_id]['total'] += amount
        
        return {
            'file_path': self.file_path,
            'year': self.year,
            'quarter': self.quarter,
            'quarter_key': self.quarter_key,
            'transaction_count': len(transactions),
            'total_income': income_data.total,
            'tax_breakdown': income_data.to_dict(),
            'account_totals': {k: {'count': v['count'], 'total': float(v['total'])} 
                             for k, v in account_totals.items()}
        }
    
    def clear_cache(self) -> None:
        """Clear cached transaction and income data."""
        self._transactions = None
        self._income_data = None
    
    def __str__(self) -> str:
        """String representation of the QFX data file."""
        if self.is_valid:
            return f"QFXDataFile({self.year} Q{self.quarter} -> {self.filename})"
        else:
            return f"QFXDataFile(INVALID -> {self.filename})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"QFXDataFile(file_path='{self.file_path}', "
                f"year={self.year}, quarter={self.quarter})")
    
    def __eq__(self, other) -> bool:
        """Check equality with another QFXDataFile."""
        if not isinstance(other, QFXDataFile):
            return False
        return (self.year == other.year and 
                self.quarter == other.quarter and
                self.file_path == other.file_path)
    
    def __hash__(self) -> int:
        """Make QFXDataFile hashable for use in sets and dicts."""
        return hash((self.year, self.quarter, self.file_path))