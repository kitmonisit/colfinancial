import sys
sys.path.append("../")
import pandas as pd

import colfinancial as cf
from colfinancial.transaction import Transaction, TxnType


DIR = "../notebooks/LEDGER"


def runner():
    with cf.Ledger(DIR) as ledger:
        rows = list(ledger.reader())
        df = pd.DataFrame.from_records(rows)
    return df

df = runner()

with pd.option_context(
        "display.max_rows", None,
        ):
    print(df)


