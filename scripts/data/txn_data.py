#!/usr/bin/env python3
"""
TxnData class for managing collections of investment income transactions.
Handles loading from multiple QFX files and deduplication.
"""

import os
import sys
from typing import List, Dict, Optional, Set
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .qfx_data_file import QFXDataFile


class TxnData:
    """
    Transaction repository that manages collections of investment income transactions.
    
    Loads transactions from multiple QFX files and eliminates duplicates using
    content-based matching. Provides methods to extract data for specific time periods.
    """
    
    def __init__(self):
        """Initialize empty transaction repository."""
        self._transactions: List[Dict] = []
        self._source_files: Set[str] = set()
        self._duplicate_count = 0
    
    def add_qfx_file(self, qfx_file: QFXDataFile) -> int:
        """
        Add transactions from a QFX file to the repository.
        
        Args:
            qfx_file: QFXDataFile object to load transactions from
            
        Returns:
            Number of new transactions added (after deduplication)
        """
        new_transactions = qfx_file.parse_transactions()
        added_count = 0
        
        for transaction in new_transactions:
            if not self._is_duplicate(transaction):
                self._transactions.append(transaction)
                added_count += 1
            else:
                self._duplicate_count += 1
        
        self._source_files.add(qfx_file.filename)
        return added_count
    
    def load_qfx_files(self, file_paths: List[str]) -> Dict[str, int]:
        """
        Load transactions from multiple QFX files.
        
        Args:
            file_paths: List of paths to QFX files
            
        Returns:
            Dictionary mapping filenames to count of transactions added
        """
        results = {}
        
        for file_path in file_paths:
            qfx_file = QFXDataFile(file_path)
            filename = os.path.basename(file_path)
            
            try:
                added_count = self.add_qfx_file(qfx_file)
                results[filename] = added_count
                print(f"✅ Loaded {filename}: {added_count} new transactions")
            except Exception as e:
                results[filename] = 0
                print(f"❌ Failed to load {filename}: {e}")
        
        return results
    
    def _is_duplicate(self, transaction: Dict) -> bool:
        """
        Check if a transaction is a duplicate using content-based matching.
        
        Uses account + posted + amount + name + memo + type for comparison,
        ignoring fitid which can be inconsistent across downloads.
        
        Args:
            transaction: Transaction dictionary to check
            
        Returns:
            True if transaction is a duplicate, False otherwise
        """
        # Create content signature (excluding fitid and other variable fields)
        signature = (
            transaction.get('account', ''),
            transaction.get('posted', ''),
            transaction.get('amount', 0.0),
            transaction.get('name', ''),
            transaction.get('memo', ''),
            transaction.get('type', '')
        )
        
        # Check against existing transactions
        for existing_txn in self._transactions:
            existing_signature = (
                existing_txn.get('account', ''),
                existing_txn.get('posted', ''),
                existing_txn.get('amount', 0.0),
                existing_txn.get('name', ''),
                existing_txn.get('memo', ''),
                existing_txn.get('type', '')
            )
            
            if signature == existing_signature:
                return True
        
        return False
    
    def get_all_transactions(self) -> List[Dict]:
        """
        Get all transactions in the repository.
        
        Returns:
            List of all transaction dictionaries
        """
        return self._transactions.copy()
    
    def get_date_range_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get transactions within a specific date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of transactions within the date range
        """
        filtered_transactions = []
        
        for txn in self._transactions:
            posted_str = txn.get('posted', '')
            if not posted_str or posted_str == 'Unknown':
                continue
            
            try:
                # Parse the posted date (assuming ISO format from ofxtools)
                posted_date = datetime.fromisoformat(posted_str.replace('Z', '+00:00'))
                posted_date = posted_date.replace(tzinfo=None)  # Remove timezone for comparison
                
                if start_date <= posted_date <= end_date:
                    filtered_transactions.append(txn)
            except (ValueError, TypeError):
                # Skip transactions with unparseable dates
                continue
        
        return filtered_transactions
    
    def get_quarter_transactions(self, year: int, quarter: int) -> List[Dict]:
        """
        Get transactions for a specific quarter.
        
        Args:
            year: Year (e.g., 2024)
            quarter: Quarter (1-4)
            
        Returns:
            List of transactions in the specified quarter
        """
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
        
        if quarter not in quarter_starts:
            raise ValueError(f"Invalid quarter: {quarter}. Must be 1-4.")
        
        start_month, start_day = quarter_starts[quarter]
        end_month, end_day = quarter_ends[quarter]
        
        start_date = datetime(year, start_month, start_day)
        end_date = datetime(year, end_month, end_day)
        
        return self.get_date_range_transactions(start_date, end_date)
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics about the transaction repository.
        
        Returns:
            Dictionary with repository statistics
        """
        account_counts = {}
        total_amount = 0.0
        
        for txn in self._transactions:
            account = txn.get('account', 'Unknown')
            amount = txn.get('amount', 0.0)
            
            if account not in account_counts:
                account_counts[account] = {'count': 0, 'total': 0.0}
            
            account_counts[account]['count'] += 1
            account_counts[account]['total'] += amount
            total_amount += amount
        
        return {
            'total_transactions': len(self._transactions),
            'source_files': sorted(list(self._source_files)),
            'duplicates_skipped': self._duplicate_count,
            'total_amount': total_amount,
            'accounts': account_counts
        }
    
    def clear(self) -> None:
        """Clear all transactions and reset the repository."""
        self._transactions.clear()
        self._source_files.clear()
        self._duplicate_count = 0
    
    def __len__(self) -> int:
        """Return the number of transactions in the repository."""
        return len(self._transactions)
    
    def __str__(self) -> str:
        """String representation of the transaction repository."""
        return f"TxnData({len(self._transactions)} transactions from {len(self._source_files)} files)"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"TxnData(transactions={len(self._transactions)}, duplicates_skipped={self._duplicate_count})"