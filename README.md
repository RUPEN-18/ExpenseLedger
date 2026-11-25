# ExpenseLedger
A lightweight personal expense tracker built with Python and SQLite. Stores Indian rupee amounts as integer paise to avoid floating-point rounding errors. Uses parameterized SQL, date indexes and grouped queries.

## Quick start (Python 3.10+)
```sh
python ledger.py add 125.50 food --date 2026-11-25 --note "Lunch"
python ledger.py add 80 travel --date 2026-11-25
python ledger.py list --month 2026-11
python ledger.py summary --month 2026-11
python ledger.py export expenses.csv --month 2026-11
python ledger.py delete 1
python -m unittest -v
```
Use `--db alternate.db` before a subcommand to use a different database. `expenses.db` is created locally on the first command. Export refuses to overwrite an existing file. Deleting an expense is permanent; back up the database first.

## Features
- Add, list and delete expenses with notes.
- Month-filtered reports and category totals using SQL aggregation.
- CSV export with basic spreadsheet formula-injection protection.
- No third-party packages, servers or API keys.

## Limitations
Single-user local CLI, INR only; no encryption, authentication, budget forecasting or automatic bank integration. Protect the database and exports as private files.
