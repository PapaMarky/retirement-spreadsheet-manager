#!/usr/bin/env python3
"""
Quick performance test for TxnData deduplication.
Tests how the current O(n²) approach performs with different transaction counts.
"""

import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.txn_data import TxnData


def create_mock_transactions(count: int) -> List[Dict]:
    """Create mock transactions for testing performance."""
    transactions = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(count):
        # Create some variation to avoid all being duplicates
        account_num = f"account_{i % 10}"  # 10 different accounts
        amount = round(100.0 + (i % 50), 2)  # Varying amounts
        date = base_date + timedelta(days=i % 365)  # Spread across year
        
        transaction = {
            'account': account_num,
            'posted': date.isoformat(),
            'amount': amount,
            'name': f'Transaction {i}',
            'memo': f'Memo for transaction {i}',
            'type': 'INCOME',
            'fitid': f'fit_{i}',  # This should be ignored for deduplication
            'source_file': 'test.qfx'
        }
        transactions.append(transaction)
    
    return transactions


def create_mock_qfx_file(transactions: List[Dict]):
    """Create a mock QFXDataFile that returns the given transactions."""
    class MockQFXFile:
        def __init__(self, transactions: List[Dict]):
            self._transactions = transactions
            self.filename = "mock.qfx"
        
        def parse_transactions(self) -> List[Dict]:
            return self._transactions
    
    return MockQFXFile(transactions)


def test_performance(transaction_counts: List[int]):
    """Test TxnData performance with different transaction counts."""
    print("TxnData Performance Test")
    print("=" * 50)
    print(f"{'Count':<8} {'Time (s)':<10} {'Duplicates':<12} {'Transactions/sec':<15}")
    print("-" * 50)
    
    for count in transaction_counts:
        # Create test data
        transactions = create_mock_transactions(count)
        mock_qfx = create_mock_qfx_file(transactions)
        
        # Time the operation
        txn_data = TxnData()
        start_time = time.time()
        added_count = txn_data.add_qfx_file(mock_qfx)
        end_time = time.time()
        
        elapsed = end_time - start_time
        duplicates = count - added_count
        txn_per_sec = count / elapsed if elapsed > 0 else float('inf')
        
        print(f"{count:<8} {elapsed:<10.3f} {duplicates:<12} {txn_per_sec:<15.1f}")
        
        # Test adding the same file again to measure duplicate detection performance
        start_time = time.time()
        added_count_2 = txn_data.add_qfx_file(mock_qfx)
        end_time = time.time()
        
        elapsed_2 = end_time - start_time
        txn_per_sec_2 = count / elapsed_2 if elapsed_2 > 0 else float('inf')
        
        print(f"  (dup) {elapsed_2:<10.3f} {count:<12} {txn_per_sec_2:<15.1f}")
        print()


def test_with_real_duplicates():
    """Test performance when adding files with actual duplicates."""
    print("\nDuplicate Detection Test")
    print("=" * 30)
    
    # Create transactions with some real duplicates
    base_transactions = create_mock_transactions(100)
    
    # Create a second set that has 50% duplicates
    duplicate_transactions = base_transactions[:50] + create_mock_transactions(50)
    
    txn_data = TxnData()
    
    # Add first file
    mock_qfx_1 = create_mock_qfx_file(base_transactions)
    start_time = time.time()
    added_1 = txn_data.add_qfx_file(mock_qfx_1)
    time_1 = time.time() - start_time
    
    print(f"First file:  {added_1} added in {time_1:.3f}s")
    
    # Add second file with duplicates
    mock_qfx_2 = create_mock_qfx_file(duplicate_transactions)
    start_time = time.time()
    added_2 = txn_data.add_qfx_file(mock_qfx_2)
    time_2 = time.time() - start_time
    
    print(f"Second file: {added_2} added in {time_2:.3f}s")
    
    summary = txn_data.get_summary()
    print(f"Total transactions: {summary['total_transactions']}")
    print(f"Duplicates skipped: {summary['duplicates_skipped']}")


if __name__ == "__main__":
    # Test with increasing transaction counts
    test_counts = [100, 500, 1000, 2000, 5000]
    test_performance(test_counts)
    
    # Test duplicate detection specifically
    test_with_real_duplicates()
    
    print("\nNOTE: Performance degrades quadratically (O(n²))")
    print("Consider using a hash-based approach for better performance.")