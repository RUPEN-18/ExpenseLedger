import sqlite3
import unittest
from ledger import initialize, add, expenses, summary, delete, amount_to_paise, month_bounds, safe_csv

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:'); initialize(self.conn)
    def tearDown(self): self.conn.close()
    def test_exact_currency(self):
        self.assertEqual(amount_to_paise('0.29'), 29)
        for bad in ('-1','0','nan','0.001'):
            with self.assertRaises(ValueError): amount_to_paise(bad)
    def test_month_and_summary(self):
        add(self.conn,'2026-11-01','Food','10.20'); add(self.conn,'2026-11-30','food','0.80'); add(self.conn,'2026-12-01','travel','5')
        self.assertEqual(summary(self.conn,'2026-11'), [('food',1100,2)])
        self.assertEqual(len(expenses(self.conn)), 3)
    def test_delete(self):
        i=add(self.conn,'2026-11-01','food','50'); self.assertTrue(delete(self.conn,i)); self.assertFalse(delete(self.conn,i))
    def test_month_boundary(self): self.assertEqual(month_bounds('2026-12'), ('2026-12-01','2027-01-01'))
    def test_csv_text(self): self.assertEqual(safe_csv('=1+1'), "'=1+1")
