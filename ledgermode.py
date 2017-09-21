import sublime
import sublime_plugin
import re
from . import ledger


def set_ledger_output(edit, window, text):
    panel = window.create_output_panel('ledger')
    panel.set_read_only(False)
    region = sublime.Region(0, panel.size())
    panel.erase(edit, region)
    panel.insert(edit, 0, text)
    panel.set_read_only(True)
    panel.show(0)
    window.run_command("show_panel", {"panel": "output.ledger"})


def view_is_ledger(view):
    return view.match_selector(0, 'source.ledger')


def previous_line(view, sr):
    """sr should be a Regiion covering the entire hard line"""
    if sr.begin() == 0:
        return None
    else:
        return view.full_line(sr.begin() - 1)


def next_line(view, sr):
    """sr should be a Region covering the entire hard line, including
    the newline"""
    if sr.end() == view.size():
        return None
    else:
        return view.full_line(sr.end())


separating_line_pattern = re.compile("^[\\t ]*\\n?$")


def is_entry_separating_line(view, sr):
    return separating_line_pattern.match(view.substr(sr)) is not None


def expand_to_entry(view, tp):
    sr = view.full_line(tp)
    if is_entry_separating_line(view, tp):
        return sublime.Region(tp, tp)

    first = sr.begin()
    prev = sr
    while True:
        prev = previous_line(view, prev)
        if prev is None or is_entry_separating_line(view, prev):
            break
        else:
            first = prev.begin()

    last = sr.end()
    next = sr
    while True:
        next = next_line(view, next)
        if next is None or is_entry_separating_line(view, next):
            break
        else:
            last = next.end()

    return sublime.Region(first, last)


def all_entries_intersecting_selection(view, sr):
    entries = []

    entry = expand_to_entry(view, sr.begin())
    if not entry.empty():
        entries.append(entry)

    while True:
        line = next_line(view, entry)
        if line is None or line.begin() >= sr.end():
            break

        if not is_entry_separating_line(view, line):
            entry = expand_to_entry(view, line.begin())
            entries.append(entry)
        else:
            entry = line

    return entries


posting_re = r'\s+'  # Starts with whitespace
comment_re = r'^(.*?)(;.*)?$'
amount_re = r'^(.*?)(?: {2,}(.*))?$'
commodity_re = r'^(.*?)( .*)?$'

account_column = 4
amount_column = 52


def format_posting(text):
    # remove extra leading and trailing spaces
    text = text.strip()

    # Remove any trailing comment (in case it has double spaces).
    # Also removes extra spaces.
    (non_comment, comment) = re.match(comment_re, text).groups('')

    (account, amount) = re.match(amount_re, non_comment).groups('')

    (amount_value, commodity) = re.match(commodity_re, amount).groups('')

    leading_space = " " * account_column

    if not amount:
        amount_space = ""
    else:
        amount_space = " " * \
            max(amount_column - len(amount_value) -
                len(account) - len(leading_space), 2)

    return leading_space + account + amount_space + amount + comment


def format_entry(text):
    formatted = []
    for line in text.splitlines():
        if re.match(posting_re, line):
            formatted.append(format_posting(line))
        else:
            formatted.append(line)
    return "\n".join(formatted) + "\n"


class LedgerBalanceCommand(sublime_plugin.TextCommand):
    def __init__(self, *args):
        super().__init__(*args)
        self.selected_index = None  # type: int
        self.accounts = None  # type: list

    def run(self, edit):
        if self.selected_index is None:
            text = self.view.substr(sublime.Region(0, self.view.size()))
            self.accounts = ledger.accounts(text=text)
            self.view.window().show_quick_panel(self.accounts,
                                                self.input_account)
        else:
            if self.selected_index >= 0:
                account = self.accounts[self.selected_index]
                self.show_balance(edit, account)

            self.selected_index = None
            self.accounts = None

    def input_account(self, index):
        self.selected_index = index
        self.view.run_command('ledger_balance')

    def show_balance(self, edit, account):
        balance = ledger.balance(account)
        set_ledger_output(edit, self.view.window(), balance)


class LedgerReformatEntry(sublime_plugin.TextCommand):
    def run(self, edit):
        if view_is_ledger(self.view):
            entries = []
            for s in self.view.sel():
                for e in all_entries_intersecting_selection(self.view, s):
                    if e not in entries:
                        entries.append(e)

            for e in reversed(entries):
                self.view.replace(edit, e, format_entry(self.view.substr(e)))

        else:
            self.view.window().status_message("Not a ledger file")
