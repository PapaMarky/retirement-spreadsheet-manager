# Net Worth Spreadsheet Income Updater - Design Document

## Overview

This document describes the object-oriented redesign of the spreadsheet income updater system. The goal is to create a flexible, maintainable system that can automatically update quarterly investment income data in Google Sheets from QFX files.

## Current State

### Existing Scripts
- **Legacy Script**: `update_spreadsheet_income.py` - Functional but monolithic approach
- **Parser Module**: `vanguard_income_parser.py` - QFX file parsing logic
- **Auth Module**: `google_auth.py` - Google Sheets API authentication
- **Multiple Analysis Scripts**: Various utility scripts for data analysis

### Current Data Flow
1. QFX files downloaded manually from Vanguard (quarterly)
2. Scripts parse QFX files to extract income transactions
3. Categorize income by tax treatment (Tax-Free, Tax-Deferred, Taxed Now)
4. Update Google Sheets with quarterly values
5. Preserve existing SUM formulas for totals

## Proposed Architecture

### Core Classes

#### 1. NetworthSpreadsheet Class
**Purpose**: Main controller for the retirement/net worth Google Spreadsheet

**Responsibilities**:
- Connect to Google Sheets API using existing `google_auth.py`
- Auto-discover and classify all sheet tabs by type
- Build comprehensive map of all QuarterColumns across YearSheets
- Provide interface for bulk operations across sheets
- Handle dry-run mode globally
- Route QFX data to correct sheet/column combinations

#### 2. BaseSheet Class (Abstract Base)
**Purpose**: Common functionality for all Google Sheets tabs

**Responsibilities**:
- Hold sheet name and Google Sheets service reference
- Provide methods for reading/writing cell ranges
- Handle batch updates and dry-run mode
- Find text patterns across rows (e.g., section headers)
- Common validation and error handling
- Abstract methods for sheet-specific operations

#### 3. YearSheet Class (extends BaseSheet)
**Purpose**: Represents annual data sheets (e.g., "2025", "2024")

**Responsibilities**:
- Scan rows to find INVESTMENT INCOME section location (not hardcoded)
- Parse header rows to discover quarterly columns dynamically
- Create QuarterColumn objects for discovered quarters
- Update income data while preserving SUM formulas
- Validate year sheet structure

#### 4. Future Sheet Classes (extends BaseSheet)
- **GraphSheet**: Handle chart/visualization sheets
- **OverviewSheet**: Summary/dashboard sheets  
- **ReferenceSheet**: Read-only reference sheets (Notes, Account Notes)

#### 5. QuarterColumn Class
**Purpose**: Represents a quarterly column that can accept income data

**Responsibilities**:
- Parse quarter description from header rows (e.g., "Oct, Nov, Dec (2024 Q4)")
- Extract year and quarter information via regex  
- Store parent sheet reference and column index
- Provide methods to write income data to correct cells
- Handle formatting and validation

#### 6. QFXDataFile Class
**Purpose**: Represents and parses a single QFX file

**Responsibilities**:
- Parse filename to extract year/quarter (YYYY-QQ.qfx format)
- Use existing `vanguard_income_parser.py` for transaction extraction
- Calculate 3-category breakdown (Tax-Free, Tax-Deferred, Taxed Now)
- Handle date range filtering automatically
- Support future expansion to other institution formats

#### 7. IncomeData Class
**Purpose**: Value object for quarterly income breakdown

**Responsibilities**:
- Store tax_free, tax_deferred, taxed_now amounts
- Provide formatting methods for spreadsheet display
- Calculate totals and percentages for reporting
- Handle currency formatting and validation

## Key Design Principles

### Flexible Column Detection
- **No Hardcoded Assumptions**: Scan all rows to find quarter patterns, not just row 3
- **Regex Pattern Matching**: Use patterns like `"Jan, Feb, Mar (2025 Q1)"` or `"Oct, Nov, Dec (2024 Q4)"`
- **Adaptive Layout**: Handle variations in formatting between sheets
- **Remember Discovery**: Cache which row contains headers for each sheet

### Universal Quarter Mapping
- **Global Quarter Map**: Build map of `{(year, quarter): QuarterColumn}`
- **No Special Cases**: All quarters treated equally - no special Q4 logic
- **Natural Routing**: Automatic routing based on year/quarter matching
- **Cross-Sheet Support**: Quarters can appear in any sheet (e.g., 2024 Q4 in 2025 sheet)

### Extensible Data Sources
- **Plugin Architecture**: Support for different institutions
- **Common Interface**: IncomeData works regardless of source
- **Filename Patterns**: Auto-detection from YYYY-QQ.qfx format
- **Future Expansion**: Support for multiple file formats with institution prefixes

## Command Line Interface

```bash
# Single file (auto-detects year/quarter from filename)
python3 update_income.py --data 2025-Q2.qfx

# Multiple files  
python3 update_income.py --data 2024-Q1.qfx,2024-Q2.qfx,2024-Q3.qfx

# Directory of files (scans for YYYY-QQ.qfx pattern)
python3 update_income.py --data /path/to/qfx/files/

# Dry run mode
python3 update_income.py --data /path/to/files/ --dry-run

# Verbose output showing column detection
python3 update_income.py --data /path/to/files/ --verbose

# Future: Multiple institutions with different patterns
python3 update_income.py --data vanguard:/path/to/vanguard/ --data chase:/path/to/chase/
```

## File Structure

```
scripts/
├── update_income.py              # Main CLI entry point
├── spreadsheet/
│   ├── __init__.py
│   ├── networth_spreadsheet.py   # NetworthSpreadsheet class
│   ├── base_sheet.py             # BaseSheet abstract class
│   ├── year_sheet.py             # YearSheet class
│   ├── graph_sheet.py            # GraphSheet class (future)
│   ├── overview_sheet.py         # OverviewSheet class (future)
│   ├── reference_sheet.py        # ReferenceSheet class (future)
│   └── quarter_column.py         # QuarterColumn class
├── data/
│   ├── __init__.py
│   ├── qfx_file.py               # QFXDataFile class
│   ├── income_data.py            # IncomeData class
│   └── parsers/
│       ├── __init__.py
│       ├── vanguard_parser.py    # Existing vanguard logic
│       └── base_parser.py        # Abstract parser interface
└── utils/
    ├── __init__.py
    ├── date_utils.py             # Date range utilities
    └── patterns.py               # Regex patterns for parsing
```

## Example Workflow

1. **NetworthSpreadsheet** opens Google Sheet and discovers all sheets
2. **Classifies sheets** by name pattern (year sheets vs. graph/overview/notes)
3. **Each YearSheet scans its rows** to find INVESTMENT INCOME section
4. **Parses header rows** to identify quarterly columns with regex
5. **Builds global QuarterColumn map** with (year, quarter) keys
6. **QFXDataFile** extracts year/quarter from filename (e.g., 2025-Q2.qfx)
7. **Looks up target QuarterColumn** from global map
8. **Creates IncomeData** from parsed transactions
9. **Writes to correct sheet/column** while preserving SUM formulas

## Sheet Classification Strategy

```python
def classify_sheet(sheet_name):
    if re.match(r'^\d{4}$', sheet_name):  # "2025", "2024", etc.
        return YearSheet
    elif sheet_name.lower() in ['graph', 'charts']:
        return GraphSheet  
    elif sheet_name.lower() in ['overview', 'summary']:
        return OverviewSheet
    else:
        return ReferenceSheet  # Default for notes, etc.
```

## Benefits

1. **Adaptive**: No hardcoded row/column assumptions
2. **Maintainable**: Clear separation of concerns with inheritance hierarchy
3. **Extensible**: Easy to add new institutions, file formats, or sheet types
4. **Flexible**: Handles spreadsheet evolution over time
5. **Robust**: Comprehensive validation and error reporting
6. **Intuitive**: Natural mapping of quarters to locations
7. **Testable**: Each class can be unit tested independently
8. **Future-Proof**: Base class design supports adding new sheet functionality

## Implementation Phases

### Phase 1: Core Income Updating (Current Scope)
- BaseSheet + YearSheet + QuarterColumn
- QFXDataFile + IncomeData
- NetworthSpreadsheet coordinator
- Command line interface with --data and --dry-run

### Phase 2: Chart Integration
- GraphSheet for automatic chart updates
- Data range expansion when new quarters added

### Phase 3: Summary Calculations  
- OverviewSheet for dashboard updates
- Cross-year calculations and trends

### Phase 4: Multi-Institution Support
- Additional parsers for other financial institutions
- Institution-specific filename patterns and data extraction

## Migration Strategy

- Keep existing scripts functional during development
- New system will coexist with legacy scripts initially
- Comprehensive testing with dry-run mode before replacing legacy system
- Gradual migration sheet by sheet to validate behavior