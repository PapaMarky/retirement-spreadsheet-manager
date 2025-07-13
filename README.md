# Retirement Spreadsheet Manager

Automated tools for managing retirement planning using a Google Sheets spreadsheet with 
investment income, networth, and expense tracking.

## Overview

Currently adding the "Net Worth" (Assets and Libilities) to the spreadsheet is a manual task 
which I perform manually once per quarter.

This project provides Python automation tools for processing passive income data 
(primarily QFX files from Vanguard) and updating the Google Sheets retirement planning spreadsheet. 
The system automatically categorizes investment income by tax treatment and populates quarterly 
data while preserving existing formulas.

**Key Features:**
- 🔄 **Automated QFX Processing**: Parse Vanguard QFX files to extract dividend and interest income
- 📊 **Tax Categorization**: Automatically categorize income as Tax-Free, Tax-Deferred, or Taxed Now
- 📈 **Google Sheets Integration**: Update quarterly income data in retirement planning spreadsheets
- 🔍 **Dry-Run Mode**: Preview changes before making updates
- ⚡ **Dynamic Column Detection**: Automatically discover quarterly columns without hardcoding
- 🛡️ **Secure Configuration**: Keep sensitive account information in local config files

## Architecture

The project is currently transitioning from functional scripts to an object-oriented design. 
See [DESIGN.md](DESIGN.md) for the detailed architecture plan.

### Current Implementation
- **Functional Scripts**: Working tools for immediate use
- **Configuration-Based**: Sensitive data moved to local config files
- **Google Sheets API**: Automated spreadsheet updates with authentication

### Planned Architecture (Future)
- **NetworthSpreadsheet Class**: Main controller for spreadsheet management
- **BaseSheet/YearSheet Classes**: Object-oriented sheet handling
- **QuarterColumn Class**: Dynamic quarterly column management
- **Extensible Parsers**: Support for multiple financial institutions

## Quick Start

### Prerequisites

1. **Python 3.7+** with required packages:
   ```bash
   pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
   ```

2. **Google Sheets API Setup**:
   - Follow instructions in [GoogleDocs-Setup.md](GoogleDocs-Setup.md) (if committed)
   - Create service account and download credentials to `scripts/google_credentials.json`

3. **Configuration**:
   ```bash
   cd scripts/
   cp config.py.example config.py
   # Edit config.py with your spreadsheet ID and account mappings
   ```

### Basic Usage

1. **Verify QFX Files**:
   ```bash
   python3 scripts/verify_qfx_dates.py
   ```

2. **Preview Updates** (Dry Run):
   ```bash
   python3 scripts/update_spreadsheet_income.py --dry-run
   ```

3. **Update Spreadsheet**:
   ```bash
   python3 scripts/update_spreadsheet_income.py
   ```

## Project Structure

```
├── scripts/                          # Main automation scripts
│   ├── config.py.example             # Configuration template
│   ├── google_auth.py                # Google Sheets API authentication
│   ├── vanguard_income_parser.py     # QFX file parsing
│   ├── update_spreadsheet_income.py  # Main spreadsheet updater
│   ├── verify_qfx_dates.py          # Data validation
│   └── [other analysis scripts]     # Additional utilities
├── DESIGN.md                         # Architecture documentation
├── CLAUDE.md                         # Claude Code guidance
└── README.md                         # This file
```

## Key Scripts

### Core Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `update_spreadsheet_income.py` | Main spreadsheet updater | `python3 update_spreadsheet_income.py [--dry-run]` |
| `verify_qfx_dates.py` | Validate QFX file date ranges | `python3 verify_qfx_dates.py` |
| `vanguard_income_parser.py` | QFX file parsing library | Imported by other scripts |
| `google_auth.py` | Google Sheets API authentication | Imported by other scripts |

### Analysis & Debugging

| Script | Purpose |
|--------|---------|
| `spreadsheet_format_breakdown.py` | Generate detailed income breakdown reports |
| `verify_sheet_structure.py` | Validate spreadsheet structure |
| `csv_vs_qfx_comparison.py` | Compare different data format outputs |
| `debug_accounts.py` | Debug account ID mappings |

## Data Flow

1. **Manual Download**: Download QFX files from Vanguard (quarterly)
2. **File Validation**: Verify QFX files contain expected date ranges
3. **Data Parsing**: Extract income transactions and categorize by tax treatment
4. **Sheet Discovery**: Automatically find quarterly columns in spreadsheet
5. **Data Update**: Write categorized income data to appropriate cells
6. **Formula Preservation**: Maintain existing SUM formulas for totals

## Tax Treatment Categories

- **Tax-Free**: Roth IRA income and municipal bond interest
- **Tax-Deferred**: Traditional IRA and 401(k) income (taxed on withdrawal)
- **Taxed Now**: Brokerage account income (taxed in current year)

## Security & Privacy

- 🔐 **Local Configuration**: Sensitive data (spreadsheet IDs, account numbers) stored in local `config.py`
- 📁 **Git Ignored**: Configuration files and credentials excluded from version control
- 🚫 **No API Keys**: Service account authentication prevents exposure of user credentials
- 🧪 **Dry-Run Mode**: Always preview changes before applying

## Future Roadmap

See [DESIGN.md](DESIGN.md) for detailed architecture plans:

1. **Object-Oriented Redesign**: Replace functional scripts with class-based architecture
2. **Multi-Institution Support**: Extend beyond Vanguard to other financial institutions
3. **Enhanced Sheet Management**: Support for networth and expense tracking sections
4. **Improved Data Discovery**: Extract account information directly from QFX files
5. **Command Line Interface**: User-friendly CLI with proper argument parsing

## Contributing

This is a personal financial management tool, but the architecture and techniques may be useful for others building similar automation. Key areas for improvement:

- Extending QFX parsing to other financial institutions
- Adding support for different file formats (CSV, OFX, etc.)
- Improving error handling and user feedback
- Adding comprehensive test suite

## Development Notes

- **Python 3.7+** required for modern features
- **Google Sheets API v4** for spreadsheet integration
- **Configuration-driven** to support different account structures
- **Dry-run mode** essential for financial data safety

## Documentation

- [DESIGN.md](DESIGN.md) - Detailed architecture and design decisions
- [CLAUDE.md](CLAUDE.md) - Development guidance for Claude Code
- [config.py.example](scripts/config.py.example) - Configuration template

---

**Note**: This tool handles personal financial data. Always use dry-run mode first and keep your configuration files private.