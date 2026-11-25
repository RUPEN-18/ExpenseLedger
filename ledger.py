"""Track personal expenses in a local SQLite database."""
import argparse
import csv
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA = '''CREATE TABLE IF NOT EXISTS expenses (
 id INTEGER PRIMARY KEY, spent_on TEXT NOT NULL, category TEXT NOT NULL,
 amount_paise INTEGER NOT NULL CHECK(amount_paise > 0), note TEXT NOT NULL DEFAULT ''
); CREATE INDEX IF NOT EXISTS expenses_date ON expenses(spent_on);'''


def amount_to_paise(value):
    try:
        amount = Decimal(value)
        if not amount.is_finite() or not Decimal('0.01') <= amount <= Decimal('1000000000'):
            raise ValueError('Amount must be between 0.01 and 1,000,000,000 INR')
        paise = amount * 100
        if paise != paise.to_integral_value():
            raise ValueError('Amount must have at most two decimal places')
        return int(paise)
    except InvalidOperation as exc:
        raise ValueError('Invalid amount') from exc


def money(paise):
    return f'{paise // 100}.{paise % 100:02d}'


def initialize(conn):
    conn.executescript(SCHEMA)


def add(conn, spent_on, category, amount, note=''):
    spent_on = date.fromisoformat(spent_on).isoformat()
    category = category.strip().lower()
    if not category or len(category) > 50:
        raise ValueError('Category must contain 1–50 characters')
    with conn:
        cur = conn.execute('INSERT INTO expenses(spent_on,category,amount_paise,note) VALUES (?,?,?,?)',
                           (spent_on, category, amount_to_paise(amount), note.strip()))
    return cur.lastrowid


def month_bounds(month):
    if month is None:
        return None
    if len(month) != 7 or month[4] != '-':
        raise ValueError('Month must use YYYY-MM')
    start = date.fromisoformat(month+'-01')
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return start.isoformat(), end.isoformat()


def filter_month(month):
    bounds = month_bounds(month)
    return (' WHERE spent_on >= ? AND spent_on < ?', bounds) if bounds else ('', ())


def expenses(conn, month=None):
    where, params = filter_month(month)
    return conn.execute('SELECT id,spent_on,category,amount_paise,note FROM expenses'+where+' ORDER BY spent_on DESC,id DESC', params).fetchall()


def summary(conn, month=None):
    where, params = filter_month(month)
    return conn.execute('SELECT category,SUM(amount_paise),COUNT(*) FROM expenses'+where+' GROUP BY category ORDER BY SUM(amount_paise) DESC,category', params).fetchall()


def delete(conn, expense_id):
    with conn:
        return conn.execute('DELETE FROM expenses WHERE id=?', (expense_id,)).rowcount == 1


def safe_csv(value):
    # Prevent common spreadsheet formula triggers in user-controlled text.
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t','\r','\n')) else value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=Path('expenses.db'))
    sub = parser.add_subparsers(dest='action', required=True)
    new = sub.add_parser('add'); new.add_argument('amount'); new.add_argument('category'); new.add_argument('--date', default=date.today().isoformat()); new.add_argument('--note', default='')
    for action in ('list', 'summary', 'export'):
        p = sub.add_parser(action); p.add_argument('--month')
        if action == 'export': p.add_argument('output', type=Path)
    remove = sub.add_parser('delete'); remove.add_argument('id', type=int)
    args = parser.parse_args()
    conn = None
    try:
        conn = sqlite3.connect(args.db); initialize(conn)
        if args.action == 'add':
            print(f'Added expense #{add(conn,args.date,args.category,args.amount,args.note)}')
        elif args.action == 'list':
            print('ID | Date | Category | INR | Note')
            for i,d,c,a,n in expenses(conn,args.month): print(f'{i} | {d} | {c} | {money(a)} | {n}')
        elif args.action == 'summary':
            rows = summary(conn,args.month)
            for category, total, count in rows: print(f'{category}: INR {money(total)} ({count} expenses)')
            print(f'Total: INR {money(sum(r[1] for r in rows))}')
        elif args.action == 'delete':
            if not delete(conn,args.id): raise ValueError('Expense ID not found')
            print(f'Deleted expense #{args.id}')
        else:
            if args.output.resolve() == args.db.resolve(): raise ValueError('Output cannot overwrite the database')
            with args.output.open('x', encoding='utf-8', newline='') as f:
                w = csv.writer(f); w.writerow(['id','date','category','amount_inr','note'])
                for i,d,c,a,n in expenses(conn,args.month): w.writerow([i,d,safe_csv(c),money(a),safe_csv(n)])
            print(f'Exported to {args.output}')
    except (sqlite3.Error, OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f'ExpenseLedger: {exc}\n')
    finally:
        if conn is not None: conn.close()


if __name__ == '__main__': main()
