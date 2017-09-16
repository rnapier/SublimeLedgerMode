# import sublime
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

    return stdout


def set_ledger_output(edit, window, text):
    panel = window.create_output_panel("ledger")
    panel.set_read_only(False)
    panel.insert(edit, 0, text)
    panel.set_read_only(True)
    window.run_command("show_panel", {"panel": "output.ledger"})


class PromptBalanceCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel(
            "Account:", "", self.on_done, None, None)

    def on_done(self, text):
        try:
            if self.window.active_view():
                self.window.active_view().run_command(
                    "balance", {"account": text})
        except ValueError:
            pass


class BalanceCommand(sublime_plugin.TextCommand):
    def run(self, edit, account):
        result = ledger(["bal", account])
        set_ledger_output(edit, self.view.window(), result)
