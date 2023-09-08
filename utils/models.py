import os
from peewee import *
import pandas as pd

import datetime
from datetime import date

from .settings import *

def create_database(db_fn, force = False):
    """
    return dictionary to update globals (sqlite_db and model classes)
           and list of model Classes
    """
    sqlite_db = SqliteDatabase(db_fn, pragmas=[('foreign_keys', 'on')])

    tables = []

    class BaseModel(Model):
        """A base model that will use our Sqlite database."""
        @classmethod
        def export_table(cls):
            with open(f"{cls.__name__}.csv", "w") as fl:
                pd.DataFrame(list(cls.select().dicts())).to_csv(fl, index=False, sep="|")

        @classmethod
        def import_table(cls):
            """
            WARNING: should be used only on empty tables
            """
            with open(f"{cls.__name__}.csv", "r") as fl:
                df = pd.read_csv(fl, index_col=0, sep="|")
                for index, row in df.iterrows():
                    try:
                        cls.create(**row)
                    except IntegrityError:
                        pass

        class Meta:
            database = sqlite_db

    class MealType(BaseModel):
        id   = AutoField()
        name = TextField()

        # TODO: make **kvargs use, so you pass various select options
        #       and make this classmethod in base model
        def output_choices():
            for mtype in MealType.select():
                print(f"\t{mtype.id}. {mtype.name}")

        def choose():
            MealType.output_choices()
            mealtype = input("enter id or name: ")
            if mealtype.isdigit():
                mealtype = MealType.get(MealType.id == mealtype)
            else:
                mealtype = MealType.get(MealType.name == mealtype)
            return mealtype


    tables.append(MealType)

    class Recipe(BaseModel):
        id   = AutoField()
        name = TextField()
        algorithm = TextField()
        meal_type = ForeignKeyField(MealType, backref='recipes')

        def create_new(name: str, meal_type: str, algorithm: list[str], ingredients):
            """
            name:        recipe name
            meal type:   how to categorize this recipe
            algorithm:   cooking algorithm for this recipe
            ingredients: dict of ingredient name to list of [quantity, measure units]

            creates recipe and fills side fields

            return: new Recipe object
            """
            # get or create meal_type
            meal, created = MealType.get_or_create(name = meal_type)
            # create recipe
            algo_concatenated = "".join([f"\n{i+1}. {line}"
                                        for i, line in enumerate(algorithm)])
            recipe = Recipe.create(name = name,
                                meal_type = meal,
                                algorithm = algo_concatenated)
            # fill ingredients
            for key, [quantity, mu] in ingredients.items():
                ingredient, created = Ingredient.get_or_create(name = key)
                measure_unit, created = MeasureUnit.get_or_create(name = mu)
                RecipeIngredient.create(recipe = recipe,
                                        ingredient = ingredient,
                                        quantity = quantity,          # see docstring
                                        measure_unit = measure_unit)  # see ^^^^^^^^^

        def choose_by_mealtype(mealtype):
            query = Recipe.select().where(Recipe.meal_type == mealtype).where(Recipe.meal_type == mealtype)
            for recipe in query:
                print("\t{}. {}".format(recipe.id, recipe.name))
            recipe = input("enter id or name: ")
            if recipe.isdigit():
                recipe = Recipe.get(Recipe.id == recipe)
            else:
                recipe = Recipe.get(Recipe.name == recipe)
            return recipe

        def aggregate_recipes():
            """return query of aggregated recipes"""
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
                     .group_by(Recipe.name, Nutrient.name, nutrientMu.name))
            return query

        def aggregate_recipe(self):
            """
            return ingredients, algorithm, nutrients
            """
            # TODO:
            #   + first fetch ingredients, then use them as subquery and join
            #     nutrients
            #   + when calculating nutrients, consider conversion to g and than
            #     to 100 g
            ingr_columns = ['ingr_name', 'ingr_quantity', 'ingr_mu']    # ingredients info
            nutr_columns = ['nutr_name', 'nutr_quantity', 'nutr_mu']    # nutrient info
            ingredientMu = MeasureUnit.alias()  # create alias so we can
            nutrientMu   = MeasureUnit.alias()  # use double joins
            query = (Recipe
                     .select(Recipe.name, Recipe.algorithm,
                             Ingredient.name.alias(ingr_columns[0]),    # join ingredients
                             RecipeIngredient.quantity.alias(ingr_columns[1]),
                             ingredientMu.name.alias(ingr_columns[2]),
                             Nutrient.name.alias(nutr_columns[0]),      # join nutrients
                             IngredientNutrient.quantity.alias(nutr_columns[1]),
                             nutrientMu.name.alias(nutr_columns[2]))
                     .join(RecipeIngredient)
                     .join(Ingredient)
                     .join_from(RecipeIngredient, ingredientMu)
                     .join(IngredientNutrient,
                           join_type=JOIN.LEFT_OUTER,
                           on=(IngredientNutrient.ingredient_id == Ingredient.id))
                     .join(Nutrient,
                           join_type=JOIN.LEFT_OUTER,
                           on=(IngredientNutrient.nutrient_id == Nutrient.id))
                     .join_from(IngredientNutrient, nutrientMu,
                                join_type=JOIN.LEFT_OUTER)
                     .where(Recipe.id == self.id))

            df = pd.DataFrame(list(query.dicts()))
            assert len(df['algorithm'].unique()) == 1, "different algorithms for recipe {}".format(self.name)
            algorithm = df.at[0, 'algorithm']

            ingr = df[ingr_columns].drop_duplicates()
            nutr = df[nutr_columns].groupby([nutr_columns[0], nutr_columns[-1]]).agg('sum')
            return ingr, algorithm, nutr


    tables.append(Recipe)


    class Ingredient(BaseModel):
        id   = AutoField()
        name = TextField(unique = True)

        def prompt():
            query = Ingredient.select(Ingredient.id, Ingredient.name)
            df = pd.DataFrame(list(query.dicts())).set_index("id").sort_values("name")
            pd.set_option('display.max_rows', None)
            print(df)
            return input("enter name or id: ")

        def find(ingr):
            """
            return Ingredient entity by id or name
            """
            if ingr.isdigit():
                ingr = Ingredient.get(Ingredient.id == ingr)
            else:
                ingr = Ingredient.get(Ingredient.name == ingr)
            return ingr


    tables.append(Ingredient)

    class MeasureUnit(BaseModel):
        id   = AutoField()
        name = TextField()

        def output_choices():
            for unit in MeasureUnit.select():
                print(f"{unit.id}. {unit.name}")

        def find(inp):
            if inp.isdigit():
                mu = MeasureUnit.get(MeasureUnit.id == int(inp))
            else:
                mu = MeasureUnit.get(MeasureUnit.name ** inp)
            return mu

    tables.append(MeasureUnit)

    class RecipeIngredient(BaseModel):
        id         = AutoField()
        recipe     = ForeignKeyField(Recipe)
        ingredient = ForeignKeyField(Ingredient)
        quantity   = DecimalField(max_digits     = 10,
                                  decimal_places = 2,
                                  auto_round     = True)
        measure_unit = ForeignKeyField(MeasureUnit)

        class Meta:
                indexes = (
                    # create a unique on ingredient/nutrient
                    (('recipe', 'ingredient'), True),
                )

    tables.append(RecipeIngredient)

    class IngredientConv(BaseModel):
        """
        if you want get new measure unit, you should
        find source mu in `from_mu` and dest mu in `to_mu`
        than multiply quantity that you have by `multiplier`
        """
        id = AutoField()
        ingredient = ForeignKeyField(Ingredient)       # cacao
        from_mu    = ForeignKeyField(MeasureUnit)      # tbsp
        to_mu      = ForeignKeyField(MeasureUnit)      # g
        multiplier = DecimalField(max_digits     = 14, # 10 (1 tbsp of cacao = 10 g of cacao)
                                  decimal_places = 4,
                                  auto_round     = True)

        def return_all():
            """
            return df containing all conversions
            """
            toMu   = MeasureUnit.alias() # create alias so we can
            fromMu = MeasureUnit.alias() # use double joins
            query = (IngredientConv
                     .select(IngredientConv.id.alias("id"),
                             Ingredient.name.alias("ingr"),
                             fromMu.name.alias("fromMu"),
                             IngredientConv.multiplier.alias("multiplier"),
                             toMu.name.alias("toMu"))
                     .join(Ingredient)
                     .join_from(IngredientConv, toMu,
                                on=(IngredientConv.to_mu_id == toMu.id))
                     .join_from(IngredientConv, fromMu,
                                on=(IngredientConv.from_mu_id == fromMu.id)))
            df = pd.DataFrame(list(query.dicts())).set_index("id")
            return df

        def prompt():
            """
            select ingredient entries with no conversion to base MeasureUnit's
            """
            ingr_alias = "ingr"
            mu_alias   = "mu"
            # conves we already done
            done_query = (IngredientConv
                          .select(Ingredient.name.alias(ingr_alias),
                                  MeasureUnit.name.alias(mu_alias))
                          .join(Ingredient)
                          .join_from(IngredientConv, MeasureUnit,
                                     on=(IngredientConv.from_mu_id == MeasureUnit.id)))
            # all entries in all recipes
            all_entries = (RecipeIngredient
                     .select(Ingredient.name.alias(ingr_alias),
                             MeasureUnit.name.alias(mu_alias))
                     .join(Ingredient, on=(Ingredient.id == RecipeIngredient.ingredient_id))
                     .join_from(RecipeIngredient, MeasureUnit)
                     .where(MeasureUnit.name.not_in(base_mu))
                     .distinct())
            query = all_entries - done_query
            df = pd.DataFrame(list(query.dicts()))
            print(df)
            conv = int(input("enter id: "))
            return df.iloc[conv]

    tables.append(IngredientConv)

    class User(BaseModel):
        id = AutoField()
        birth_date = DateField()
        # 0 for male, 1 for female
        sex = FloatField(constraints = [Check('sex <= 1'), Check('sex >= 0')])

        def create_user(birth_date, sex):
            # create user index
            user = User.create(birth_date = birth_date,
                        sex = sex)

        def input_prompt():
            birth_date_str = input("enter birth date (YYYY/MM/DD): ")
            birth_date = datetime.datetime.strptime(birth_date_str, '%Y/%m/%d')
            sex = float(input("enter sex from 0 to 1 (0 - male, 1 - female): "))
            return birth_date, sex

        @property
        def age(self):
            return (date.today() - self.birth_date).years

        @property
        def sex_rounded(self):
            return ('male' if round(self.sex) == 0 else 'female')


    tables.append(User)

    class Nutrient(BaseModel):
        id = AutoField()
        name = TextField(unique = True)
        fullname = TextField(default = "")
        underdose = TextField(null = True)  # how you fell, if you don't have enough of this nutrient
        overdose = TextField(null = True)   # how you fell, if you have too much of this nutrient

        def prompt():
            query = Nutrient.select(Nutrient.id, Nutrient.name, Nutrient.fullname)
            print(pd.DataFrame(list(query.dicts())).set_index('id'))
            inp = input("enter id or name: ")
            return inp

        def find(inp):
            if not inp.isdigit():
                nutrient = Nutrient.get(Nutrient.name ** inp)
            else:
                nutrient = Nutrient.get(Nutrient.id == int(inp))
            return nutrient

        def modify_interactive(self):
            name = input("enter new name (leave empty for unchanged): ")
            if name not in "":
                self.name = name
            fullname = input("enter new fullname (leave empty for unchanged): ")
            if fullname not in "":
                self.fullname = fullname
            underdose = input("enter new underdose (leave empty for unchanged): ")
            if underdose not in "":
                self.underdose = underdose
            overdose = input("enter new overdose (leave empty for unchanged): ")
            if overdose not in "":
                self.overdose = overdose

            self.save()

    tables.append(Nutrient)

    class IngredientNutrient(BaseModel):
        id = AutoField()
        ingredient   = ForeignKeyField(Ingredient)
        nutrient     = ForeignKeyField(Nutrient)
        # quantity usually stored per 100g
        quantity     = DecimalField(max_digits = 10,
                                    decimal_places = 4,
                                    auto_round = True)
        measure_unit = ForeignKeyField(MeasureUnit)

        class Meta:
                indexes = (
                    # create a unique on ingredient/nutrient
                    (('ingredient', 'nutrient'), True),
                )

    tables.append(IngredientNutrient)

    class NutrientBound(BaseModel):
        """
        rules depending on age, sex, pregrancy. how to choose correct nutrient intake
        if you use pills, you pregnant or something else special, you should double check recommended doses. in rare cases I skip some details to simplify output
        """
        id = AutoField()
        nutrient  = ForeignKeyField(Nutrient, backref="bounds")
        age_lower = DecimalField(max_digits = 8,
                                 decimal_places = 4,
                                 auto_round = True)
        age_upper = DecimalField(max_digits = 8,
                                 decimal_places = 4,
                                 auto_round = True)
        sex = TextField(choices=[('male', 'male'), ('female', 'female')])
        # Adequate Intakes (AIs) aka lower bound (use RDA when possible)
        AI = DecimalField(max_digits     = 10,
                          decimal_places = 2,
                          auto_round     = True,
                          null           = True)
        # Tolerable Upper Intake Levels (ULs) aka upper bound
        UL = DecimalField(max_digits     = 10,
                          decimal_places = 2,
                          auto_round     = True,
                          null           = True)
        measure_unit = ForeignKeyField(MeasureUnit)

        class Meta:
                indexes = (
                    # create a unique on ingredient/nutrient
                    (('nutrient', 'age_lower', 'age_upper', 'sex'), True),
                )

        def create_prompt(nutrient):
            age_lower = float(input("enter lower age bound: "))
            age_upper = float(input("enter upper age bound: "))
            sex = str(input("enter sex: "))
            AI = input("enter rda (or ai): ")
            UL = input("enter ul: ")
            mu = MeasureUnit.find(input("enter measure unit: "))
            bound = NutrientBound.create(nutrient = nutrient,
                                         age_lower = age_lower,
                                         age_upper = age_upper,
                                         sex = sex,
                                         AI = AI,
                                         UL = UL,
                                         measure_unit = mu)
            return bound

    tables.append(NutrientBound)

    class UserNutrients(BaseModel):
        """
        IMPORTANT: it is not developed for people younger than 19
        all quantities are specified by day
        """
        id = AutoField()
        user = ForeignKeyField(User)
        nutrient = ForeignKeyField(Nutrient)
        measure_unit = ForeignKeyField(MeasureUnit)

        def calculate_nutrients(user):
            """
            calculate nutrients depending on information in table
            also creates unexisting nutrients in Nutrient table
            """
            print("calculating nutrients for age: {user.age} and sex: {user.sex_rounded}")
            mg, created = MeasureUnit.get_or_create(name = "mg")    # will be used later
            mcg, created = MeasureUnit.get_or_create(name = "mcg")  # will be used later

            # calcium
            # calculate qty
            if user.age >= 19 and user.age <= 50:
                ai = 1000
            elif user.sex_rounded == 'male' and user.age >= 71:
                ai = 1200
            elif user.sex_rounded == 'female' and user.age >= 51:
                ai = 1200
            else:
                ai = 1000

            # chloride
            # The recommendation doesn't change for women who are pregnant or breastfeeding.
            # calculate qty
            if user.age >= 1 and user.age <= 3:
                ai = 1500
            elif user.age <= 8:
                ai = 1900
            elif user.age <= 50:
                ai = 2300
            elif user.age <= 70:
                ai = 2000
            else:
                ai = 1800

            # copper
            description = "Together with iron, it enables the body to form red blood cells."
            ai = 900

            # fluoride
            if user.age <= 1:
                print("WARNING: chloride quantity for age below 6 months should be 0.01 mg/day")
                ai = 0.5
            elif user.age <= 3:
                ai = 0.7
            elif user.age <= 8:
                ai = 1
            elif user.age <= 13:
                ai = 2
            elif user.age <= 18:
                ai = 3
            elif user.sex_rounded == "male":
                ai = 4
            else:
                ai = 3

            B_description = "All B vitamins help the body convert food (carbohydrates) into fuel (glucose), which is used to produce energy. These B vitamins, often referred to as B-complex vitamins, also help the body use fats and protein. B-complex vitamins are needed for a healthy liver, and healthy skin, hair, and eyes."
            # B9
            B9_description = "Folic acid is crucial for proper brain function and plays an important role in mental and emotional health."
            ai = 400

            # iodine
            if user.age >= 1 and user.age <= 8:
                ai = 90
            elif user.age <= 13:
                ai = 120
            else:
                ai = 150

            # iron
            if user.sex_rounded == "male":
                ai = 8
            elif user.age >= 19 and user.age <= 50:
                ai = 18
            else:
                ai = 8

            # magnesium
            if user.sex_rounded == "male":
                if user.age >= 19 and user.age <= 30:
                    ai = 400
                else:
                    ai = 420
            else:
                if user.age >= 19 and user.age <= 30:
                    ai = 310
                else:
                    ai = 320

            # manganese
            if user.sex_rounded == "male":
                ai = 2.3
            else:
                ai = 1.8

            # molybdenum
            ai = 45

            # phosphorus
            ai = 700

            # selenium
            ai = 55

            # choline
            if user.sex_rounded == "male":
                ai = 550
            else:
                ai = 425

            # sodium
            if user.age >= 19 and user.age <= 50:
                ai = 1500
            elif user.age <= 70:
                ai = 1300
            else:
                ai = 1200

            # A
            if user.sex_rounded == "male":
                ai = 900
            else:
                ai = 700

            # B3
            if user.sex_rounded == "male":
                ai = 16
            else:
                ai = 14

            # B6
            if user.sex_rounded == "male":
                if user.age >= 19 and user.age <= 50:
                    ai = 1.3
                else:
                    ai = 1.7
            else:
                if user.age >= 19 and user.age <= 50:
                    ai = 1.3
                else:
                    ai = 1.5

            # C
            if user.sex_rounded == "male":
                ai = 90
            else:
                ai = 75

            # D
            if user.age >= 1 and user.age <= 70:
                ai = 15
            else:
                ai = 20

            # E
            ai = 15

            # zinc
            if user.sex_rounded == "male":
                ai = 11
            else:
                ai = 8

    tables.append(UserNutrients)

    with sqlite_db:
        # create all tables above
        sqlite_db.create_tables(tables)

    # return dictionary to update globals() in calling script
    ret_d = {}
    ret_d.update({"sqlite_db": sqlite_db})
    ret_d.update({table.__name__: table for table in tables})
    return ret_d, tables

def export_database(tables):
    """
    this method uses base model .export_model function
    """
    # export tables
    for table in tables:
        table.export_table()
