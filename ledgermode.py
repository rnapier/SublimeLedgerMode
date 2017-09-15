# import sublime
import sublime_plugin
import subprocess


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
        result = subprocess.check_output(
            ["ledger", "bal", account], universal_newlines=True)

        panel = self.view.window().create_output_panel("ledger")
        panel.set_read_only(False)
        panel.insert(edit, 0, result)
        panel.set_read_only(True)
        self.view.window().run_command(
            "show_panel", {"panel": "output.ledger"})
