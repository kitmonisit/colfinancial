# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.9.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# + language="html"
# <style>
# div.output_area pre {
#     white-space: pre;
# }
# </style>
# -

# %load_ext autoreload
# %autoreload 2

import sys
sys.path.append("..")

# +
from colfinancial.extract import Ledger

def func():
    with Ledger("LEDGER") as l:
        for line in l.reader():
            yield line


# +
def process(line):
    try:
        net = float(line.split(':')[-1].strip().replace(",", ""))
        return net
    except ValueError:
        return 0

import numpy as np
arr = np.array(list(map(process, func())))
arr.sum()
