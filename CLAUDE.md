# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a personal financial asset tracking repository for retirement planning, not a software development codebase. It contains:

- Financial statements and documents (PDFs)
- Downloaded account data (CSV, TXT files) 
- Historical financial data organized by institution

## Directory Structure

- `2025-07/` - Current month's downloaded statements and data
- `Historical-Data/` - Organized by financial institution (Vanguard, eTrade, Chase, etc.)
- `logs/` - Empty directory for potential logging

## Data Sources

The repository tracks assets from multiple financial institutions:
- **Broadridge** - John Deere stock holdings
- **Chase** - Banking accounts  
- **eTrade** - F5 RSUs, ISOs, and cash holdings
- **Guideline** - Mimic 401(k)
- **Provident Credit Union** - Savings, checking, credit cards
- **ScholarShare 529** - Education savings accounts
- **Vanguard** - Joint accounts and IRAs

## File Formats

- **PDF** - Account statements (primary format for most institutions)
- **CSV** - Investment holdings data (Vanguard, eTrade portfolio downloads)
- **TXT** - Copy-pasted account summaries from web interfaces
- **QFX** - Quicken export format from some institutions
- **XLSX** - Excel exports from some platforms

## Data Collection Process

Data is manually downloaded every 3-4 months following specific procedures documented in README.md for each financial institution. The process involves logging into each account and downloading statements or exporting account data.

## External Tools

Financial data is maintained in a Google Spreadsheet for trend analysis and graphing. The repository serves as the raw data storage location.

## Git and Version Control Guidelines

**CRITICAL**: This repository contains sensitive financial data and configuration files.

### Git Add Rules
- **NEVER use `git add .` or `git add --all`** - Always specify individual files
- **Always specify exact file paths** when staging files for commit
- **Review staged files** with `git status` before committing
- **Check for sensitive data** before adding any new files

### Files to NEVER Commit
- `scripts/config.py` - Contains personal spreadsheet IDs and account numbers
- `scripts/google_credentials.json` - Contains Google API credentials
- `ASSETS.md` - Contains personal account information and procedures
- `Claude-GoogleDocs-Setup.md` - Contains personal spreadsheet URLs
- Any files in `Historical-Data/` - Contains actual financial statements
- Any `.json` files that might contain credentials

### Safe Git Workflow
1. Use specific file paths: `git add scripts/new_feature.py`
2. Review staged files: `git status`
3. Verify no sensitive data: `git diff --cached`
4. Then commit with descriptive message

## Important Notes

- This is personal financial data - handle with appropriate confidentiality
- No automation is in place by design (security preference)
- Data collection frequency is quarterly
- No software build, test, or deployment processes exist