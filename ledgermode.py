import sublime
import sublime_plugin
import subprocess
import re


class LedgerException(Exception):
    pass


def ledger(args, input=None):
    extra_args = []
    if input is not None:
        extra_args.extend(["-f", "-"])

    p = subprocess.Popen(["ledger"] + extra_args + args,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         universal_newlines=True)
    stdout, stderr = p.communicate(input)

    if not p.returncode == 0:
        raise LedgerException()

    return stdout.strip()


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


class LedgerEntry(object):
    """docstring for LedgerEntry"""

    def __init__(self, text):
        super(LedgerEntry, self).__init__()
        self.text = text

    def formatted(self):
        return self.text


class LedgerBalanceCommand(sublime_plugin.TextCommand):
    def __init__(self, *args):
        super().__init__(*args)
        self.selected_index = None  # type: int
        self.accounts = None  # type: list

    def run(self, edit):
        if self.selected_index is None:
            text = self.view.substr(sublime.Region(0, self.view.size()))
            accounts_output = ledger(['accounts', '^Assets:', '^Liabilities:'],
                                     input=text)

            if len(accounts_output) == 0:
                accounts_output = ledger(['accounts'])

            self.accounts = accounts_output.split("\n")

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
        balance = ledger(['balance', account])
        set_ledger_output(edit, self.view.window(), balance)


class LedgerReformatEntry(sublime_plugin.TextCommand):
    def run(self, edit):
        if view_is_ledger(self.view):
            entries = []
            for s in self.view.sel():
                for e in all_entries_intersecting_selection(self.view, s):
                    if e not in entries:
                        entries.append(e)

            if len(entries) > 0:
                self.view.sel().clear()
                for e in entries:
                    self.view.sel().add(e)

        else:
            self.view.window().status_message("Not a ledger file")
