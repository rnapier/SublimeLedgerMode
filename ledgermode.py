import sublime
import sublime_plugin
from . import ledger
from datetime import date

today = date.today()
last_used_year = today.year
last_used_month = today.month
last_used_day = today.day


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
    return view.match_selector(0, 'text.ledger')


def previous_line(view, sr):
    """sr should be a Region covering the entire hard line"""
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


def is_entry_separating_line(view, sr):
    return ledger.is_entry_separator(view.substr(sr))


def expand_to_entry(view, tp):
    sr = view.full_line(tp)
    if is_entry_separating_line(view, sr):
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
    next_location = sr
    while True:
        next_location = next_line(view, next_location)
        if next_location is None or is_entry_separating_line(view, next_location):
            break
        else:
            last = next_location.end()

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
                self.view.replace(edit, e,
                                  ledger.format_entry(self.view.substr(e)))

        else:
            self.view.window().status_message("Not a ledger file")


class LedgerNewEntry(sublime_plugin.TextCommand):
    def run(self, edit):
        if view_is_ledger(self.view):
            s = self.view.sel()[-1]

            entry_end = expand_to_entry(self.view, s.end())

            pt = entry_end.end()

            # if at the very end of the buffer with no newline
            if pt == self.view.size() and not is_entry_separating_line(self.view, self.view.full_line(entry_end)):
                pt += self.view.insert(edit, pt, "\n")
            else:
                # Remove this blank line
                blank_line = self.view.line(pt)
                self.view.erase(edit, blank_line)
                pt = blank_line.begin()

            pt += self.view.insert(edit, pt, "\n2018/")
            self.view.insert(edit, pt, "\n")

            self.view.sel().clear()
            self.view.sel().add(sublime.Region(pt))
            self.view.show(pt)


# class LedgerAutocomplete(sublime_plugin.EventListener):
    # def on_query_completions(self, view, prefix, locations):
    #     point = locations[-1]
    #     # print(prefix)
    #     #
    #     # # scope = view.scope_name(point)
    #     #
    #     line = view.full_line(point)
    #     print("auto")
    #     if ledger.is_entry_separator(view.substr(line)):
    #         print("sep")
    #         return [("new transaction", "\n{}/".format(last_used_year))]
    #
    #     return None
