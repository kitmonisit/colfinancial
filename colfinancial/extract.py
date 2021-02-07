import io
from collections import deque
from enum import Enum
from pathlib import Path

from .transaction import Transaction


class ReadState(Enum):
    BEGIN_ALL = 0
    BEGIN_MONTHLY_LEDGER = 1
    READ_TXN = 2
    BETWEEN_TXN = 3
    END_MONTHLY_LEDGER = 4
    BETWEEN_MONTHLY_LEDGER = 5
    END_ALL = 6


# Idea from here https://stackoverflow.com/a/50770511
class Ledger(io.RawIOBase):
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

           import pandas as pd

           DIR = "./ledger"
           with Ledger(DIR) as ledger:
               rows = list(ledger.reader())
               df = pd.DataFrame(data=rows)

        """
        self.DIR = Path(ledger_dir)

    def reader(self):
        self.read_state = ReadState.BEGIN_ALL
        while True:
            try:
                for line in self.__read_beginning():
                    yield Transaction(line)
                self.__read_begin_monthly_ledger()
                for line in self.__read_txn():
                    yield Transaction(line)
                self.__read_between_txn()
                self.__read_end_monthly_ledger()
                self.__read_between_monthly_ledger()
                self.__read_end()
            except StopIteration:
                break

    def __enter__(self):
        self.leftover = b""
        files = sorted(self.DIR.glob("*.txt"))[:-1]
        self.stream_iter = map(lambda f: open(f, "r"), files)
        try:
            self.bar_counter = 0
            self.stream = next(self.stream_iter)
        except StopIteration:
            self.stream = None
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def readable(self):
        return True

    def __read_next_chunk(self, max_length):
        if self.leftover:
            return self.leftover
        elif self.stream is not None:
            return self.stream.read(0x10)
        else:
            return b""

    def readinto(self, b):
        buffer_length = len(b)
        chunk = self.__read_next_chunk(buffer_length)
        while len(chunk) == 0:
            # Move to next stream
            if self.stream is not None:
                self.stream.close()
            try:
                self.stream = next(self.stream_iter)
                self.bar_counter = 0
                self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
                chunk = self.__read_next_chunk(buffer_length)
            except StopIteration:
                # No more streams to chain together
                self.stream = None
                return 0  # Indicate EOF
        output, self.leftover = chunk[:buffer_length], chunk[buffer_length:]
        b[: len(output)] = bytes(output, encoding="ascii")
        return len(output)

    @staticmethod
    def __is_horizontal_bar(line):
        s = line.strip()
        return (len(s) > 0) & (s == len(s) * b"-")

    @staticmethod
    def __is_start_of_txn_table(line):
        return b"BEGINNING BALANCE" in line

    @staticmethod
    def __is_end_of_txn_table(line):
        return (b"GAIN(LOSS)" in line) & (b"COST" not in line)

    @staticmethod
    def __is_end_of_monthly_ledger(line):
        return b"Total Account Equity" in line

    def __read_beginning(self):
        if (self.read_state == ReadState.BEGIN_ALL):
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    self.bar_counter += 1
                if Ledger.__is_start_of_txn_table(line):
                    self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
                    yield line
                    break

    def __read_begin_monthly_ledger(self):
        if self.read_state == ReadState.BEGIN_MONTHLY_LEDGER:
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    self.bar_counter += 1
                if self.bar_counter == 3:
                    self.read_state = ReadState.READ_TXN
                    break

    def __read_txn(self):
        if self.read_state == ReadState.READ_TXN:
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    self.read_state = ReadState.BETWEEN_TXN
                    break
                else:
                    yield line

    def __read_between_txn(self):
        if self.read_state == ReadState.BETWEEN_TXN:
            bar_counter = 0
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    bar_counter += 1
                if bar_counter == 2:
                    self.read_state = ReadState.READ_TXN
                    break
                if Ledger.__is_end_of_txn_table(line):
                    self.read_state = ReadState.END_MONTHLY_LEDGER
                    break

    def __read_end_monthly_ledger(self):
        if self.read_state == ReadState.END_MONTHLY_LEDGER:
            for line in self:
                if Ledger.__is_end_of_monthly_ledger(line):
                    self.read_state = ReadState.BETWEEN_MONTHLY_LEDGER
                    break

    def __read_between_monthly_ledger(self):
        if self.read_state == ReadState.BETWEEN_MONTHLY_LEDGER:
            for line in self:
                if not self.stream:
                    self.read_state = ReadState.END_ALL
                if self.read_state == ReadState.BEGIN_MONTHLY_LEDGER:
                    break

    def __read_end(self):
        if self.read_state == ReadState.END_ALL:
            raise StopIteration
