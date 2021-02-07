import sys
sys.path.append("./")
import pandas as pd

import colfinancial as cf
from colfinancial.transaction import Transaction, TxnType

from pyinstrument import Profiler

DIR = "./sandbox/LEDGER"


def runner():
    with cf.Ledger(DIR) as ledger:
        with Profiler() as p:
            rows = list(ledger.reader())
    print(p.output_text(color=True))
    df = pd.DataFrame.from_records(rows)
    return df

def display(df):
    with pd.option_context(
            "display.max_rows", None,
            ):
        print(df)

def buffer_fn():
    with cf.Ledger(DIR) as ledger:
        with Profiler() as p:
            print(ledger.read(1024))
    print(p.output_text(color=True))
    # df = pd.DataFrame.from_records(rows)
    # return df

if __name__ == "__main__":
    df = runner()
    # display(df)
    # buffer_fn()

