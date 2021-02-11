import io
import pandas as pd

from enum import Enum
from more_itertools import peekable
from pathlib import Path

from .transaction import Transaction, TxnType


class ReadState(Enum):
    BEGIN_ALL = 0
    BEGIN_MONTHLY_LEDGER = 1
    READ_TXN = 2
    BETWEEN_TXN = 3
    END_MONTHLY_LEDGER = 4
    BETWEEN_MONTHLY_LEDGER = 5
    END_ALL = 6


class SingleStream(io.RawIOBase):
    def readable(self):
        return True

    def __enter__(self):
        files = sorted(self.DIR.glob("*.txt"))
        self.streams_read = 0
        self.stream = None
        self.stream_iter = map(lambda f: open(f, "r"), files)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def __next__(self):
        out = self.readline()
        if not out:
            self.stream.close()
            self.stream = None
            try:
                out = self.readline()
            except StopIteration:
                self.read_state = ReadState.END_ALL
        return out

    def readline(self, size=-1):
        try:
            out = self.stream.readline()
            return out
        except AttributeError:
            if self.streams_read == 0:
                self.read_state = ReadState.BEGIN_ALL
            else:
                self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
            self.stream = next(self.stream_iter)
            self.streams_read += 1
            self.bar_counter = 0
            out = self.stream.readline()
            return out


# Idea from here https://stackoverflow.com/a/50770511
class Ledger(SingleStream):
    def __init__(self, ledger_dir):
        """
        Parameters
        ----------
        ledger_dir : str
            A directory containing monthly ledgers downloaded from COL
            Financial

        Example
        -------
        Always use this class within a context:

        .. code-block:: python

           DIR = "./ledger"
           ledger = Ledger(DIR)
           df = ledger.dataframe
        """
        self.DIR = Path(ledger_dir)
        self.dispatch = {
            ReadState.BEGIN_ALL: self.__read_begin,
            ReadState.BEGIN_MONTHLY_LEDGER: self.__read_begin_monthly_ledger,
            ReadState.READ_TXN: self.__read_txn,
            ReadState.BETWEEN_TXN: self.__read_between_txn,
            ReadState.BETWEEN_MONTHLY_LEDGER: self.__read_between_monthly_ledger,
            ReadState.END_MONTHLY_LEDGER: self.__read_end_monthly_ledger,
            ReadState.END_ALL: self.__read_end,
        }
        self.PREVIOUS_SECU = None

    @property
    def dataframe(self):
        with self:
            df = pd.DataFrame.from_records(self)
        return df

    def __next__(self):
        while True:
            line = super().__next__()
            line = self.dispatch[self.read_state](line)
            if line is not None:
                # print(f"{str(self.read_state):<30s}", end="")
                # print(f"{line[-70:-1]:>80s}")
                out = Transaction(line, previous_secu=self.PREVIOUS_SECU)
                if self.read_state == ReadState.READ_TXN and out["action"] in (
                    TxnType.BUY,
                    TxnType.SELL,
                ):
                    self.PREVIOUS_SECU = out["secu"]
                return out

    @staticmethod
    def __is_horizontal_bar(line):
        s = line.strip()
        return (len(s) > 0) & (s == len(s) * "-")

    @staticmethod
    def __is_start_of_txn_table(line):
        return "BEGINNING BALANCE" in line

    @staticmethod
    def __is_end_of_txn_table(line):
        return ("GAIN(LOSS)" in line) & ("COST" not in line)

    @staticmethod
    def __is_end_of_monthly_ledger(line):
        return "Total Account Equity" in line

    def __read_begin(self, line):
        if Ledger.__is_horizontal_bar(line):
            self.bar_counter += 1
        if Ledger.__is_start_of_txn_table(line):
            self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
            return line

    def __read_begin_monthly_ledger(self, line):
        if Ledger.__is_horizontal_bar(line):
            self.bar_counter += 1
        if self.bar_counter == 3:
            self.read_state = ReadState.READ_TXN
            return None

    def __read_txn(self, line):
        if Ledger.__is_horizontal_bar(line):
            self.read_state = ReadState.BETWEEN_TXN
            self.bar_counter_between_txn = 0
            return None
        else:
            return line

    def __read_between_txn(self, line):
        if Ledger.__is_horizontal_bar(line):
            self.bar_counter_between_txn += 1
        if self.bar_counter_between_txn == 2:
            self.read_state = ReadState.READ_TXN
        if Ledger.__is_end_of_txn_table(line):
            self.read_state = ReadState.END_MONTHLY_LEDGER

    def __read_end_monthly_ledger(self, line):
        if Ledger.__is_end_of_monthly_ledger(line):
            self.read_state = ReadState.BETWEEN_MONTHLY_LEDGER

    def __read_between_monthly_ledger(self, line):
        if not self.stream:
            self.read_state = ReadState.END_ALL
        if self.read_state == ReadState.BEGIN_MONTHLY_LEDGER:
            return None

    def __read_end(self, line):
        if self.read_state == ReadState.END_ALL:
            raise StopIteration
