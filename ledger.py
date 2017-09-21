import subprocess
import re


class LedgerException(Exception):
    pass


def run(args, input=None):
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


def accounts(text=None):
    accounts_output = run(['accounts', '^Assets:', '^Liabilities:'],
                          input=text)

    if not accounts_output:
        accounts_output = run(['accounts'])

    return accounts_output.splitlines()


def balance(account):
    return run(['balance', account])


posting_re = r'\s+'  # Starts with whitespace
comment_re = r'^(.*?)(;.*)?$'
amount_re = r'^(.*?)(?: {2,}(.*))?$'
commodity_re = r'^(.*?)( .*)?$'
entry_separator_re = r'^\s*$'

account_column = 4
amount_column = 52


def is_entry_separator(line):
    return re.match(entry_separator_re, line) is not None


def is_posting(line):
    return re.match(posting_re, line)


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
        if is_posting(line):
            formatted.append(format_posting(line))
        else:
            formatted.append(line)
    return "\n".join(formatted) + "\n"
