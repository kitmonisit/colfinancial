import sys
sys.path.append("./")
import pandas as pd

import core
from core.transaction import Transaction, TxnType

from pyinstrument import Profiler

DIR = "./sandbox/LEDGER"

def display(df):
    with pd.option_context(
            "display.max_rows", None,
            ):
        print(df)

def runner():
    with Profiler() as p:
        ledger = core.Ledger(DIR)
        df = ledger.dataframe
    print(p.output_text(color=True))
    return df

if __name__ == "__main__":
    df = runner()
    display(df)
    # looper()
    # optimize()
    # print(len(df.index))
    # buffer_fn()
    # ledger = core.SingleStream(DIR)
    # fd = open("./sandbox/LEDGER/202007.txt", "r")

