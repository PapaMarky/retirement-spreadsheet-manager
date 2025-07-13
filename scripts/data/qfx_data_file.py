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

# Configure logging to suppress ofxtools noise
logging.getLogger('ofxtools.Parser').setLevel(logging.WARNING)
logging.getLogger('ofxtools.Types').setLevel(logging.WARNING)


class QFXDataFile:
    """
    Parses a single QFX file and extracts all investment income transactions.
    
    This is a pure file parser that loads the entire QFX file and returns
    all investment income transactions found in the file. It does not make
    assumptions about quarterly data or date ranges - it simply extracts
    all income transactions from the file.
    
    Use with TxnData for deduplication and QuarterlyData for quarterly filtering.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize QFX data file parser.
        
        Args:
            file_path: Path to the QFX file
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self._transactions: Optional[List[Dict]] = None
    
    
    def parse_transactions(self) -> List[Dict]:
        """
        Parse QFX file and extract all investment income transactions.
        
        Returns:
            List of all income transactions found in the file
        """
        if self._transactions is not None:
            return self._transactions
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"QFX file not found: {self.file_path}")
        
        # Parse QFX file using ofxtools
        self._transactions = self._parse_qfx_file()
        
        return self._transactions
    
    def _parse_qfx_file(self) -> List[Dict]:
        """
        Parse QFX file using ofxtools and extract all investment income transactions.
        
        Returns:
            List of all income transactions in the file
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
                    
                    transaction = {
                        'account': account_id,  # Changed to 'account' to match budgy convention
                        'posted': str(txn_date) if txn_date else 'Unknown',  # Changed to 'posted' for budgy compatibility
                        'fitid': income_txn.invtran.fitid if hasattr(income_txn.invtran, 'fitid') else 'Unknown',
                        'memo': income_txn.invtran.memo if hasattr(income_txn.invtran, 'memo') else '',
                        'amount': float(income_txn.total) if hasattr(income_txn, 'total') else 0.0,
                        'name': income_txn.invtran.memo if hasattr(income_txn.invtran, 'memo') else '',  # Added 'name' field for budgy
                        'type': income_txn.incometype if hasattr(income_txn, 'incometype') else 'INCOME',  # Added 'type' field
                        'cusip': income_txn.secid.uniqueid if hasattr(income_txn, 'secid') and hasattr(income_txn.secid, 'uniqueid') else 'Unknown',
                        'source_file': self.filename  # Track source file
                    }
                    transactions.append(transaction)
        
        # Sort by account and date
        return sorted(transactions, key=lambda x: (x['account'], x['posted']))
    
    def clear_cache(self) -> None:
        """Clear cached transaction data."""
        self._transactions = None
    
    def __str__(self) -> str:
        """String representation of the QFX data file."""
        return f"QFXDataFile({self.filename})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"QFXDataFile(file_path='{self.file_path}')"