#!/usr/bin/env python3

import os, sys
from pathlib import Path
import datetime
import argparse

from utils.settings import *

# ========== Print to stderr ===========
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser(description="Diet manipulation and monitoring")
parser.add_argument('--output-file',
                    default = "stdout",
                    metavar = "fl",
                    type    = str,
                    help    = "file to which recipes and buy list must be outputted",
                    dest    = "out_file")
parser.add_argument('--working-dir',
                    default = "recipes",
                    metavar = "DIR",
                    type    = str,
                    help    = "directory with recipes",
                    dest    = "working_dir")

args = parser.parse_args()

if __name__ == "__main__":
    print("hello")


