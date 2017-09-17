import sublime
import sublime_plugin
import subprocess


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
