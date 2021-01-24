import io
from collections import deque
from enum import Enum
from pathlib import Path


class ReadState(Enum):
    BEGIN_MONTHLY_LEDGER = 0
    READ_TXN = 1
    BETWEEN_TXN = 2
    END_MONTHLY_LEDGER = 3
    DONE_MONTHLY_LEDGER = 4


# Idea from here https://stackoverflow.com/a/50770511
class Ledger(io.RawIOBase):
    def __init__(self, ledger_dir):
        """
        Parameters
        ----------
        ledger_dir : str
            A directory containing monthly ledgers downloaded from COL
            Financial
        """
        self.DIR = Path(ledger_dir)

    def __enter__(self):
        self.leftover = b""
        files = sorted(self.DIR.glob("*.txt"))
        self.fds = list(map(lambda f: open(f, "r"), files))
        self.stream_iter = iter(self.fds)
        try:
            self.bar_counter = 0
            self.stream = next(self.stream_iter)
            self.FIRST_STREAM = True
        except StopIteration:
            self.stream = None
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        deque(map(lambda f: f.close(), self.fds))
        super().close()

    def readable(self):
        return True

    def __read_next_chunk(self, max_length):
        if self.leftover:
            return self.leftover
        elif self.stream is not None:
            return self.stream.read(max_length)
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
                self.FIRST_STREAM = False
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
        return b"BEGINNING_BALANCE" in line

    @staticmethod
    def __is_end_of_txn_table(line):
        return (b"GAIN(LOSS)" in line) & (b"COST" not in line)

    @staticmethod
    def __is_end_of_monthly_ledger(line):
        return b"Total Account Equity" in line

    def __read_begin_monthly_ledger(self):
        if self.read_state == ReadState.BEGIN_MONTHLY_LEDGER:
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    self.bar_counter += 1
                if self.FIRST_STREAM & Ledger.__is_start_of_txn_table(line):
                    # TODO Emit beginning balance data
                    pass
                if self.bar_counter == 3:
                    self.read_state = ReadState.READ_TXN
                    break
            if self.read_state == ReadState.BEGIN_MONTHLY_LEDGER:
                raise StopIteration

    def __read_txn(self):
        if self.read_state == ReadState.READ_TXN:
            for line in self:
                if Ledger.__is_horizontal_bar(line):
                    self.read_state = ReadState.BETWEEN_TXN
                    break
                else:
                    # TODO Read transaction line atom and emit data
                    s = f"{line.decode('ascii').strip()}"[1:-2]
                    yield s

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
                    self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
                    break

    def reader(self):
        self.read_state = ReadState.BEGIN_MONTHLY_LEDGER
        while True:
            try:
                self.__read_begin_monthly_ledger()
                for s in self.__read_txn():
                    yield s
                self.__read_between_txn()
                self.__read_end_monthly_ledger()
            except StopIteration:
                break
