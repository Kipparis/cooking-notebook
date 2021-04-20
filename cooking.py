#!python3
# -*- coding: utf-8 -*-

import os, sys
import datetime
import argparse

import pandas as pd
from peewee import *
from utils.models import *

from utils import recipe

# ========== Print to stderr ===========
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# TODO:
# определять офсет для которого состоявляется ценовая цена и возможность
# кастомизировать вывод
# если что-то было не найдено, выводить в стандартный вывод ошибок
#
# задаешь аргументы, он создает файл на эту неделю с датами и суммарным
# списком покупак, для вывода в файл использовать формат

parser = argparse.ArgumentParser(description="Diet manipulation and monitoring")
# через сколько дней считать план
parser.add_argument('--offset',
        default = 0,
        type    = int,
        help    = "number of days past current to calculate diet",
        metavar = "offset",
        dest    = "offset")
parser.add_argument('--cost',
        action = "store_true",
        help   = "whether program will calculate cost for next day",
        dest   = "do_calculate_cost")
parser.add_argument('--concat-recipe',
        action = "store_true",
        help   = "whether program will all recipes in one list",
        dest   = "do_concat_recipe")
parser.add_argument('--output-file',
                    default = "stdout",
                    metavar = "fl",
                    type    = str,
                    help    = "file to which recipes and buy list must be outputted",
                    dest    = "out_file")
parser.add_argument('--create-user',
                    action = "store_true",
                    help = "initiate user information to calculate nutrients",
                    dest = "create_user")
parser.add_argument('--working-dir',
        default = "generated",
        metavar = "DIR",
        type    = str,
        help    = "file to which recipes and buy list must be outputted",
        dest    = "working_dir")
parser.add_argument('-l', '--list',
                    action  = "store_true",
                    help    = "list all recipes",
                    dest    = "list")
parser.add_argument('-a', '--add',
                    action = "store_true",
                    help    = "add new recipe to db",
                    dest    = "add")
parser.add_argument('-d', '--database',
                    default = "recipe.db",
                    type    = str,
                    help    = "database for recipe storage",
                    metavar = "DB_FN",
                    dest    = "db_fn")
parser.add_argument('-e', '--export',
                    nargs='*',
                    help = "export database into several csv files (exported and imported files must have same versions)",
                    dest = "export_tables")
parser.add_argument('-i', '--import',
                    nargs='*',
                    help = "import database from serveral csv files (exported and imported files must have same versions)",
                    dest = "import_tables")

args = parser.parse_args()

if __name__ == "__main__":
    ret_d, tables = create_database(args.db_fn)
    # create database if it not exists
    # also it returns database instance and models
    globals().update(ret_d)

    if args.do_concat_recipe:
        concat_recipe()

    if args.export_tables is not None:
        if len(args.export_tables) == 0:
            print("exporting database contents")
            export_database(tables)
        else:
            print("exporting specific tables is not implemented yet")

    # if flag is presented
    if args.import_tables is not None:
        if len(args.import_tables) == 0:
            print("importing all tables is not implemented yet")
        else:
            for table in args.import_tables:
                # find table by name
                for key, val in ret_d.items():
                    if key.lower() == table.lower():
                        # import values
                        val.import_table()

    if args.find_nutrients:
        print("finding nutrients")

    if args.add:    # add recipe(s)
        MealType.output_choices()
        meal = input("select meal type or enter new: ")
        #
        # select\create meal type
        #
        if meal.isdigit(): # user input is number
            meal = MealType.get(MealType.id == int(meal)).name
        #
        # create recipe
        #
        recipe = str(input("enter recipe name: "))
        #
        # insert cooking algorithm
        #
        print("enter algorithm line by line (empty line considered as empty)")
        algo = []
        while True:
            line = input()
            if line in "":
                break
            algo.append(line)
        #
        # enter ingredients
        #
        ingredients = {}
        while True:
            # read ingredient name
            ingredient = input("select ingredient or type new: ")
            # user want to exit
            if ingredient in "exit":
                break
            quantity = float(input("enter quantity: "))
            MeasureUnit.output_choices()
            measure_unit = input("enter measure units (int or str): ")
            if measure_unit.isdigit():
                measure_unit = MeasureUnit.get(MeasureUnit.id == int(measure_unit)).name
            ingredients[ingredient] = [quantity, measure_unit]
        Recipe.create_new(recipe, meal, algo, ingredients)

    if args.list:
        # build query joining all recipes
        query = (Recipe
                 .select(Recipe, MealType, RecipeIngredient, Ingredient, MeasureUnit)
                 .join(MealType)
                 .switch(Recipe)
                 .join(RecipeIngredient,
                       on=(RecipeIngredient.recipe == Recipe.id),
                       attr='ri')
                 .join(Ingredient,
                       on=(RecipeIngredient.ingredient == Ingredient.id),
                       attr='ingr')
                 .switch(RecipeIngredient)
                 .join(MeasureUnit))
        if len(query) != 0:
            # output contents of query
            df = pd.DataFrame([{"name": entry.name,
                                "meal type": entry.meal_type.name,
                                "ingr name": entry.ri.ingr.name,
                                "ingr qty": entry.ri.quantity,
                                "measure unit": entry.ri.measure_unit.name}
                            for entry in query])
            print(df.to_string(index=False))
        else:
            print("no recipes in the book")
    if args.create_user:
        print("creating user profile")
