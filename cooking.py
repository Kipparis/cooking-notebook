#!/usr/bin/env python3

import os, sys
from pathlib import Path
import datetime
import argparse

from pprint import PrettyPrinter
pp = PrettyPrinter(indent=4)

from utils.settings import *

import yaml

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
parser.add_argument('--list', '-l',
                    action  = "store_true",
                    help    = "only list recipe names",
                    dest    = "do_list_recipes")

args = parser.parse_args()

if __name__ == "__main__":
    print("hello")
    print(f"DEBUG: recipe dir: {args.working_dir}")
    def get_recipes():
        recipe_names = set()
        for fs_item in Path(args.working_dir).glob('*.y*ml'):
            if not fs_item.is_file(): continue
            with open(fs_item) as fl:
                recipe_data = yaml.safe_load(fl)
            if "name" not in recipe_data:
                print(f"WARN: recipe does not contain name: {fs_item!s}")
                continue
            if recipe_data["name"] in recipe_names:
                print(f"WARN: duplicate recipe_names: {recipe_data['name']}")
                continue
            print(f"DEBUG: adding {recipe_data['name']} into resulting list of recipe names")
            recipe_names.add(recipe_data["name"])
            yield recipe_data

    if args.do_list_recipes:
        print(f"DEBUG: listing only recipe names")
        recipe_names = [recipe['name'] for recipe in get_recipes()]
        pp.pprint(recipe_names)


