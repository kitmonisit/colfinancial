# Clear terminal
# https://stackoverflow.com/questions/2084508/clear-terminal-in-python#comment85748431_2084521

import sys

sys.path.append("./")
import pandas as pd

import core
from core.transaction import Transaction, TxnType

from pyinstrument import Profiler

DIR = "./sandbox/LEDGER"

def clear():
    print(chr(27) + "c" + chr(27) + "[3J" + chr(27) + "[H" + chr(27) + "[2J", end="")


def display(df):
    with pd.option_context(
        "display.max_rows",
        None,
    ):
        print(df)


def runner():
    with Profiler() as p:
        ledger = core.Ledger(DIR)
        df = ledger.dataframe
    # print(p.output_text(color=True))
    return df


def main():
    clear()
    df = runner()
    cols = ["date", "secu", "shares", "price", "gross_amount"]
    cols = df.columns
    display(df[cols])
    # looper()
    # optimize()
    # print(len(df.index))
    # buffer_fn()
    # ledger = core.SingleStream(DIR)
    # fd = open("./sandbox/LEDGER/202007.txt", "r")
