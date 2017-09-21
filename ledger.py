import subprocess


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
