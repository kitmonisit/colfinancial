from enum import Enum


class TxnType(Enum):
    BUY = 0
    SELL = 1
    OR = 2
    CDIV = 3


class Transaction(dict):
    @staticmethod
    def __clean_line(line):
        line = f"{line.decode('ascii').strip()}"[1:-2]
        return list(map(lambda s: s.strip().replace(",", ""), line.split(":")))

    @staticmethod
    def __format_dict(line_split):
        return zip(
            Transaction.KEYS,
            (
                Transaction.FORMATTERS[k](v)
                for k, v in zip(Transaction.KEYS, line_split)
            ),
        )

    @staticmethod
    def __get_action(action):
        action = action.replace("+", "")
        return getattr(TxnType, action)

    @staticmethod
    def __pass_through(s):
        try:
            return s.replace(",", "")
        except AttributeError:
            return s

    @staticmethod
    def __float_or_zero(s):
        try:
            return float(s)
        except ValueError:
            return float(0.0)

    FORMATTERS = {
        "date": __pass_through.__func__,
        "action": __get_action.__func__,
        "ref": __pass_through.__func__,
        "secu": __pass_through.__func__,
        "shares": int,
        "price": __float_or_zero.__func__,
        "gross_amount": __float_or_zero.__func__,
        "comm_vat": __float_or_zero.__func__,
        "other_fees": __float_or_zero.__func__,
        "net_amount": __float_or_zero.__func__,
        "balance": __float_or_zero.__func__,
        "cost": __float_or_zero.__func__,
        "gains": __float_or_zero.__func__,
    }
    KEYS = FORMATTERS.keys()

    def __init__(self, line):
        line_split = Transaction.__clean_line(line)
        action = {
            TxnType.BUY: self.__make_stock_action,
            TxnType.SELL: self.__make_stock_action,
            TxnType.CDIV: self.__make_div_action,
            TxnType.OR: self.__make_fund_action,
        }
        args = Transaction.__format_dict(
            action[Transaction.__get_action(line_split[1])](line_split)
        )
        super().__init__(args)
        # print(self)

    def __make_stock_action(self, line_split):
        return line_split

    def __make_div_action(self, line_split):
        line_split.pop(3)  # Pop 'CD ...'
        line_split.insert(3, None)  # secu is None
        line_split.insert(4, 0)  # shares is 0.0
        line_split.insert(5, 0.0)  # price is 0.0
        return line_split

    def __make_fund_action(self, line_split):
        line_split.pop(3)  # Pop 'Additional deposit ...'
        line_split.insert(3, None)  # secu is None
        line_split.insert(4, 0)  # shares is 0.0
        line_split.insert(5, 0.0)  # price is 0.0
        return line_split
