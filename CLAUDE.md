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

## Important Notes

- This is personal financial data - handle with appropriate confidentiality
- No automation is in place by design (security preference)
- Data collection frequency is quarterly
- No software build, test, or deployment processes exist