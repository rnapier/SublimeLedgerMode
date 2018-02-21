import unittest
import ledger

formatted_entry = '''2017/03/24 * THE URBAN CHICKEN NCRALEIGH NC
    Expenses:Pets                             $28.27
    Liabilities:Credit Cards:American Express
'''


class FormatTest(unittest.TestCase):
    def test_format_posting(self):
        posting = '    Expenses:Pets                             $28.27'
        self.assertEqual(posting, ledger.format_posting(posting))

    def test_format_entry(self):
        self.assertEqual(formatted_entry,
                         ledger.format_entry(formatted_entry))
