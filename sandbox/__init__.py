# Clear terminal
# https://stackoverflow.com/questions/2084508/clear-terminal-in-python#comment85748431_2084521

import sys
from more_itertools import peekable

sys.path.append("./")
import pandas as pd
import numpy as np

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


def consolidate(df):
    p = peekable(df.iterrows())
    for idx, current_record in p:
        following = [
            current_record,
        ]
        if current_record["action"] in (TxnType.BUY, TxnType.SELL):
            if current_record["ref"] is None:
                continue
            peek_idx = 0
            while True:
                try:
                    _, next_record = p[peek_idx]
                except IndexError:
                    break
                if (
                    next_record["secu"] == current_record["secu"]
                    and next_record["ref"] is None
                ):
                    following.append(next_record)
                else:
                    break
                peek_idx += 1
        if len(following) == 1:
            yield current_record
        else:
            shares = np.array([record["shares"] for record in following])
            price = np.array([record["price"] for record in following])
            args = current_record.to_dict()
            args["shares"] = np.sum(shares)
            args["price"] = np.ma.average(a=price, weights=shares)
            yield pd.Series(args)


def main():
    clear()
    df = runner()
    # cols = ["date", "action", "ref", "secu", "shares", "price", "gross_amount"]
    # cols = df.columns
    # df = df[cols].iloc[50:101]
    df = pd.DataFrame.from_records(consolidate(df))
    display(df)
    # df_iter = df[cols].iloc[50:101].iterrows()
    # p = peekable(df_iter)
    # print(p.peek())
    # looper()
    # optimize()
    # print(len(df.index))
    # buffer_fn()
    # ledger = core.SingleStream(DIR)
    # fd = open("./sandbox/LEDGER/202007.txt", "r")
