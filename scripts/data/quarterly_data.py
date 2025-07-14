#!/usr/bin/env python3
"""
QuarterlyData class for processing investment income data for a specific quarter.
Handles tax categorization and IncomeData generation.
"""

import os
import sys
from typing import List, Dict, Optional
from decimal import Decimal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spreadsheet.quarter_column import IncomeData
from .txn_data import TxnData


class QuarterlyData:
    """
    Represents investment income data for a specific quarter.
    
    Extracts transactions from TxnData for a specific quarter and applies
    tax categorization logic to generate IncomeData objects for spreadsheet integration.
    """
    
    def __init__(self, year: int, quarter: int):
        """
        Initialize quarterly data processor.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
        """
        if quarter not in [1, 2, 3, 4]:
            raise ValueError(f"Invalid quarter: {quarter}. Must be 1-4.")
        
        self.year = year
        self.quarter = quarter
        self._transactions: Optional[List[Dict]] = None
        self._income_data: Optional[IncomeData] = None
    
    @property
    def quarter_key(self) -> str:
        """Get a unique key for this quarter."""
        return f"{self.year}_Q{self.quarter}"
    
    def extract_from_txn_data(self, txn_data: TxnData) -> List[Dict]:
        """
        Extract transactions for this quarter from TxnData.
        
        Args:
            txn_data: TxnData repository to extract from
            
        Returns:
            List of transactions for this quarter
        """
        self._transactions = txn_data.get_quarter_transactions(self.year, self.quarter)
        return self._transactions
    
    def get_transactions(self) -> List[Dict]:
        """
        Get transactions for this quarter.
        
        Returns:
            List of transactions (must call extract_from_txn_data first)
        """
        if self._transactions is None:
            raise ValueError("No transactions loaded. Call extract_from_txn_data() first.")
        return self._transactions
    
    def calculate_income_breakdown(self, account_tax_treatment: Optional[Dict[str, str]] = None) -> IncomeData:
        """
        Calculate tax-categorized income breakdown for this quarter.
        
        Args:
            account_tax_treatment: Optional mapping of account IDs to tax treatment
                                 (if not provided, will try to import from config)
        
        Returns:
            IncomeData object with tax-free, tax-deferred, and taxed-now totals
        """
        if self._income_data is not None:
            return self._income_data
        
        if self._transactions is None:
            raise ValueError("No transactions loaded. Call extract_from_txn_data() first.")
        
        # Get account tax treatment mapping
        if account_tax_treatment is None:
            account_tax_treatment = self._get_account_tax_treatment()
        
        # Initialize totals
        tax_free_total = Decimal('0.00')
        tax_deferred_total = Decimal('0.00')
        taxed_now_total = Decimal('0.00')
        
        # Get CUSIP mappings for fund names
        cusip_mappings = self._get_cusip_mappings()
        
        # Process each transaction
        for txn in self._transactions:
            account_id = txn.get('account', '')
            amount = Decimal(str(txn.get('amount', 0.0)))
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
    
    def _get_account_tax_treatment(self) -> Dict[str, str]:
        """
        Get account tax treatment mapping from config.
        
        Returns:
            Dictionary mapping account IDs to tax treatment
        """
        try:
            from config import ACCOUNT_TAX_TREATMENT
            return ACCOUNT_TAX_TREATMENT
        except ImportError:
            print("Warning: Could not import ACCOUNT_TAX_TREATMENT from config")
            return {}
    
    def _get_cusip_mappings(self) -> Dict[str, str]:
        """
        Get CUSIP to fund name mappings from config.
        
        Returns:
            Dictionary mapping CUSIP to fund names
        """
        try:
            from config import CUSIP_MAPPINGS
            return CUSIP_MAPPINGS
        except ImportError:
            print("Warning: Could not import CUSIP_MAPPINGS from config")
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
    
    def get_summary(self) -> Dict:
        """
        Get summary information about this quarter's data.
        
        Returns:
            Dictionary with quarter summary and statistics
        """
        if self._transactions is None:
            return {
                'quarter_key': self.quarter_key,
                'year': self.year,
                'quarter': self.quarter,
                'transactions_loaded': False,
                'transaction_count': 0,
                'income_calculated': False
            }
        
        summary = {
            'quarter_key': self.quarter_key,
            'year': self.year,
            'quarter': self.quarter,
            'transactions_loaded': True,
            'transaction_count': len(self._transactions),
            'income_calculated': self._income_data is not None
        }
        
        if self._income_data is not None:
            summary.update({
                'total_income': self._income_data.total,
                'tax_breakdown': self._income_data.to_dict()
            })
        
        # Account breakdown
        account_totals = {}
        for txn in self._transactions:
            account = txn.get('account', 'Unknown')
            amount = txn.get('amount', 0.0)
            
            if account not in account_totals:
                account_totals[account] = {'count': 0, 'total': 0.0}
            
            account_totals[account]['count'] += 1
            account_totals[account]['total'] += amount
        
        summary['accounts'] = account_totals
        return summary
    
    def clear_cache(self) -> None:
        """Clear cached transaction and income data."""
        self._transactions = None
        self._income_data = None
    
    def __str__(self) -> str:
        """String representation of the quarterly data."""
        status = "loaded" if self._transactions is not None else "not loaded"
        count = len(self._transactions) if self._transactions else 0
        return f"QuarterlyData({self.year} Q{self.quarter}, {count} transactions, {status})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"QuarterlyData(year={self.year}, quarter={self.quarter})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another QuarterlyData."""
        if not isinstance(other, QuarterlyData):
            return False
        return self.year == other.year and self.quarter == other.quarter
    
    def __hash__(self) -> int:
        """Make QuarterlyData hashable for use in sets and dicts."""
        return hash((self.year, self.quarter))