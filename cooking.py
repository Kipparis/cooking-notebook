#!python3
# -*- coding: utf-8 -*-

import os, sys
import datetime
import argparse

import pandas as pd
from peewee import *
from utils.models import *
from utils.nutrients import find_nutrients

from utils import recipe

from utils.settings import *

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
parser.add_argument('--find-nutrients',
                    action = "store_true",
                    help = "go through recipes and try to find nutrient for each ingredient",
                    dest = "find_nutrients")
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
parser.add_argument('--recipes',
                    nargs='*',
                    help ='specify target recipes\' names (otherwise, when needed, you will be given interactive prompt)',
                    dest = 'recipes')
parser.add_argument('--aggregate-nutrients',
                    action = 'store_true',
                    help ='calculate summarized nutrients for passed recipes (and ingredients, for which we don\'t know nutrition)',
                    dest ='aggregate_nutrients')

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
        for ingredient in Ingredient.select():
            print(f"finding nutrients for {ingredient.name}")
            for name, quantity, measure_unit in find_nutrients(ingredient.name):
                print(f"\tget {name} {quantity} {measure_unit}")
                matching_nutrients = Nutrient.select().where(Nutrient.name ** name) # ILIKE analogue
                assert len(matching_nutrients) < 2, "ERROR: >= 2 matching nutrients by name"
                if len(matching_nutrients) == 0:
                    continue    # get nutrient we don't know about yet
                nutrient = matching_nutrients.get()
                print(f"\tfound nutrient entry in database: ({nutrient.id}, {nutrient.name}, {nutrient.fullname})")
                mu = MeasureUnit.get(MeasureUnit.name == measure_unit)
                try:
                    IngredientNutrient.create(ingredient   = ingredient,
                                              nutrient     = nutrient,
                                              quantity     = quantity,
                                              measure_unit = mu)
                except IntegrityError:
                    entry = (IngredientNutrient
                             .select(IngredientNutrient, Nutrient, Ingredient, MeasureUnit)
                             .join_from(IngredientNutrient, Ingredient)
                             .join_from(IngredientNutrient, Nutrient)
                             .join_from(IngredientNutrient, MeasureUnit)
                             .where((Nutrient.id == nutrient) & (Ingredient.id == ingredient))
                             .get())
                    print(f"IngredientNutrient already exists: ({entry.ingredient.name}, {entry.nutrient.name}, {entry.quantity}, {entry.measure_unit.name})")


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

    if args.aggregate_nutrients:
        print("aggregating nutrients")
        names = args.recipes
        if names is None or len(names) == 0:
            print("interactive prompt is not implemented yet")
        else:
            ingredientMu = MeasureUnit.alias()  # create alias so we can
            nutrientMu = MeasureUnit.alias()    # join this table twice
            query = (Recipe
                     .select(Recipe,
                             RecipeIngredient, Ingredient, ingredientMu,
                             IngredientNutrient, Nutrient, nutrientMu)
                     .join(RecipeIngredient,   attr='ri')
                     .join(Ingredient,         attr='ing')
                     .join(IngredientNutrient, attr='inu')
                     .join(Nutrient, attr='nu')
                     .join_from(RecipeIngredient, ingredientMu, attr='mu')
                     .join_from(IngredientNutrient, nutrientMu, attr='mu')
                     .where(Recipe.name.in_(names)))
            pd_dict = [{"id": entry.id,
                        "recName": entry.name,
                        "ingName": entry.ri.ing.name,
                        "ingQty": entry.ri.quantity,
                        "ingMu": entry.ri.mu.name,
                        "nuName": entry.ri.ing.inu.nu.name,
                        "nuQty": entry.ri.ing.inu.quantity,
                        "nuMu (per 100 g)": entry.ri.ing.inu.mu.name}
                       for entry in query]
            df = pd.DataFrame(pd_dict).set_index('id')
            print("\n", df, sep="")

            print()
            print("aggregated")
            query = (Recipe
                     .select(Recipe,
                             RecipeIngredient, Ingredient, ingredientMu,
                             fn.Sum(IngredientNutrient.quantity).alias('count'),
                             IngredientNutrient, Nutrient, nutrientMu)
                     .join(RecipeIngredient,   attr='ri')
                     .join(Ingredient,         attr='ing')
                     .join(IngredientNutrient, attr='inu')
                     .join(Nutrient, attr='nu')
                     .join_from(RecipeIngredient, ingredientMu, attr='mu')
                     .join_from(IngredientNutrient, nutrientMu, attr='mu')
                     .where(Recipe.name.in_(names))
                     .group_by(Recipe.name, Nutrient.name, nutrientMu.name))
            pd_dict = [{"id": entry.id,
                        "recName": entry.name,
                        "nuName": entry.ri.ing.inu.nu.name,
                        "nuQty(per 100 g)": entry.count,
                        "nuMu": entry.ri.ing.inu.mu.name}
                       for entry in query]
            pp.pprint(query[0].__dict__)
            df = pd.DataFrame(pd_dict).set_index('id')
            print("\n", df, sep="")

