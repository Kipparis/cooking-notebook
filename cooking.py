#!python3

import os, sys
import pandas
import datetime
import argparse

from utils.recipe import Recipe

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
parser.add_argument('--working-dir',
        default = "generated",
        metavar = "DIR",
        type    = str,
        help    = "file to which recipes and buy list must be outputted",
        dest    = "working_dir")
args = parser.parse_args()

sheet_file = "diet.ods"
sheet_name = "main"
recipe_dir = os.path.abspath("recipes")
week_days = [   # заголовки строчек в файле
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье"]

pd_inst = pandas.read_excel(io=sheet_file,
        sheet_name=sheet_name,
        header=0,
        index_col=0)

print("Full pd_inst")
print(pd_inst)

week_day = datetime.datetime.today().weekday()
print("Current week day is: {}".format(week_days[week_day]))

print("pd_inst.loc[\"{}\"]".format(week_days[week_day]))
plan = pd_inst.loc[week_days[(week_day + args.offset) % len(week_days)]]
print(pd_inst.loc[week_days[week_day]])

print("plan")
# массив всех ингредиентов (список покупок)
total_of_ingredients = []
# список рецептов, которые не смогли найти
cant_find = []
recipes = []
for elem in plan:
    # пытаюсь найти рец
    recipe_to_search = os.path.join(recipe_dir,
            elem.lower().replace(" ", "_") + ".txt")
    print(recipe_to_search)
    recipe_inst = Recipe(fn=recipe_to_search)
    # если его нет - составляю список пропущенных рецептов
    if not recipe_inst:
        cant_find.append(elem)
        continue
    print(recipe_inst)
    recipes.append(recipe_inst)
    # TODO: строить бор по собранным именам (для ускорения поиска)
    # собираю вместе все ингредиенты
    for ingredient in recipe_inst.ingredients:
        print("Взяли ингридиент: {}".format(ingredient))
        # проверяю есть ли ингридиент с таким же именем
        found = 0
        for i, target in enumerate(total_of_ingredients):
            print("Сравниваем с ингридиентом: {}".format(target))
            if target.name == ingredient.name:
                print("Складываем {} и {}".format(ingredient, target))
                found = 1
                total_of_ingredients[i] = target + ingredient
                print("Получаем: {}".format(target))
                break
        if not found: total_of_ingredients.append(ingredient)

# open file (if not default)
out_file = sys.stdout
if args.out_file != "stdout": out_file = open(args.out_file, 'w')

# выводим количество дней, даты, дни недели на которые мы все просчитали
print((datetime.date.today() + datetime.timedelta(days=args.offset)).strftime("%d.%m.%Y"),
        file=out_file)
print(", ".join(el for el in plan), file=out_file)

# выводим количество ингридиентов
for ingredient in total_of_ingredients:
    print(ingredient, file=out_file)
for recipe in recipes:
    print("=" * 10, file=out_file)
    print(recipe, file=out_file)
print("+ {}".format(", ".join(e for e in cant_find)), file=out_file)

# ============================================
# выводим все что подсчитали в groff_ms формат

out_file = os.path.join(os.path.abspath(args.working_dir), "plan.ms")
fl = open(out_file, 'w')
print(".TL", file=fl) # Заголовок
print((datetime.date.today() + datetime.timedelta(days=args.offset)).strftime("%d.%m.%Y"),
        file=fl)
print(".PP", file=fl)
print(", ".join(el for el in plan), file=fl)
print(".NH", file=fl)
print("Все ингредиенты", file=fl)
print("\n".join(".IP \[bu]\n{}".format(str(ingr)) for ingr in total_of_ingredients), file=fl)
print(".PP", file=fl)
print("+ {}".format(", ".join(e for e in cant_find)), file=fl)
# если есть хоть какие-то рецепты
if len(recipes):
    print(".NH\nКаждый рецепт", file=fl)
# выводим каждый рецепт
for recipe in recipes:
    print(".NH 2\n{}".format(recipe.name), file=fl)
    print(".PP\nИнгридиенты:", file=fl)
    print("\n".join(".IP \[bu]\n{}".format(str(ingr)) for ingr in recipe.ingredients),
            file=fl)
    print(".nr step 0 1", file=fl)
    print(".PP\nРецепт:", file=fl)
    print("\n".join(".IP \\n+[step]\n{}".format(inst) for inst in recipe.instructions), file=fl)

fl.close()
# ===========================================

if args.out_file != "stdout": out_file.close()
