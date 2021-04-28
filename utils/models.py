import os
from peewee import *
import pandas as pd

import datetime
from datetime import date

def create_database(db_fn, force = False):
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

        def output_choices():
            for mtype in MealType.select():
                print(f"{mtype.id}. {mtype.name}")

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


        def aggregate_recipe(self):
            """
            return ingredients, algorithm, nutrients
            """
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

    tables.append(Ingredient)

    class MeasureUnit(BaseModel):
        id   = AutoField()
        name = TextField()

        def output_choices():
            for unit in MeasureUnit.select():
                print(f"{unit.id}. {unit.name}")

    tables.append(MeasureUnit)

    class RecipeIngredient(BaseModel):
        id         = AutoField()
        recipe     = ForeignKeyField(Recipe)
        ingredient = ForeignKeyField(Ingredient)
        quantity   = DecimalField(max_digits     = 10,
                                  decimal_places = 2,
                                  auto_round     = True)
        measure_unit = ForeignKeyField(MeasureUnit)

    tables.append(RecipeIngredient)

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
        underdose = TextField(null = True)  # how you fell, if you don't have enough of this nutrient
        overdose = TextField(null = True)   # how you fell, if you have too much of this nutrient

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

    class UserNutrients(BaseModel):
        """
        IMPORTANT: it is not developed for people younger than 19
        all quantities are specified by day
        """
        id = AutoField()
        user = ForeignKeyField(User)
        nutrient = ForeignKeyField(Nutrient)
        quantity = DecimalField(max_digits     = 10,
                                decimal_places = 2,
                                auto_round     = True)
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
                quantity = 1000
            elif user.sex_rounded == 'male' and user.age >= 71:
                quantity = 1200
            elif user.sex_rounded == 'female' and user.age >= 51:
                quantity = 1200
            else:
                quantity = 1000

            # chloride
            # calculate qty
            if user.age >= 19 and user.age <= 50:
                quantity = 2300
            elif user.age <= 70:
                quantity = 2000
            else:
                quantity = 1800

            quantity = 900
            UserNutrients.create(user = user, nutrient = copper, quantity = quantity, measure_unit = mcg)

            if user.sex_rounded == "male":
                quantity = 4
            # copper
            else:
                quantity = 3
            UserNutrients.create(user = user, nutrient = fluoride, quantity = quantity, measure_unit = mg)


            quantity = 150
            UserNutrients.create(user = user, nutrient = iodine, quantity = quantity, measure_unit = mcg)
            # B9
            B9_description = "Folic acid is crucial for proper brain function and plays an important role in mental and emotional health."

            # iodine
            # iron
            if user.sex_rounded == "male":
                quantity = 8
            elif user.age >= 19 and user.age <= 50:
                quantity = 18
            else:
                quantity = 8
            UserNutrients.create(user = user, nutrient = iron, quantity = quantity, measure_unit = mg)

            # magnesium
            if user.sex_rounded == "male":
                if user.age >= 19 and user.age <= 30:
                    quantity = 400
                else:
                    quantity = 420
            else:
                if user.age >= 19 and user.age <= 30:
                    quantity = 310
                else:
                    quantity = 320
            UserNutrients.create(user = user, nutrient = magnesium, quantity = quantity, measure_unit = mg)

            # manganese
            if user.sex_rounded == "male":
                quantity = 2.3
            else:
                quantity = 1.8
            UserNutrients.create(user = user, nutrient = manganese, quantity = quantity, measure_unit = mg)

            # molybdenum

            # phosphorus

            # selenium

            quantity = 55
            UserNutrients.create(user = user, nutrient = selenium, quantity = quantity, measure_unit = mcg)

            # choline
            if user.sex_rounded == "male":
                quantity = 550
            else:
                quantity = 425
            UserNutrients.create(user = user, nutrient = choline, quantity = quantity, measure_unit = mg)

            # sodium
            if user.age >= 19 and user.age <= 50:
                quantity = 1500
            elif user.age <= 70:
                quantity = 1300
            else:
                quantity = 1200
            UserNutrients.create(user = user, nutrient = sodium, quantity = quantity, measure_unit = mg)

            quantity = 0
            UserNutrients.create(user = user, nutrient = vanadium, quantity = quantity, measure_unit = mcg)

            # A
            if user.sex_rounded == "male":
                quantity = 900
            else:
                quantity = 700
            UserNutrients.create(user = user, nutrient = A, quantity = quantity, measure_unit = mcg)

            # B3
            if user.sex_rounded == "male":
                quantity = 16
            else:
                quantity = 14
            UserNutrients.create(user = user, nutrient = B3, quantity = quantity, measure_unit = mg)

            # B6
            if user.sex_rounded == "male":
                if user.age >= 19 and user.age <= 50:
                    quantity = 1.3
                else:
                    quantity = 1.7
            else:
                if user.age >= 19 and user.age <= 50:
                    quantity = 1.3
                else:
                    quantity = 1.5
            UserNutrients.create(user = user, nutrient = B6, quantity = quantity, measure_unit = mg)

            # C
            if user.sex_rounded == "male":
                quantity = 90
            else:
                quantity = 75
            UserNutrients.create(user = user, nutrient = C, quantity = quantity, measure_unit = mg)

            D, created = Nutrient.get_or_create(name = "D")
            if user.age >= 1 and user.age <= 70:
                quantity = 15
            else:
                quantity = 20
            UserNutrients.create(user = user, nutrient = D, quantity = quantity, measure_unit = mcg)

            # E

            # zinc
            if user.sex_rounded == "male":
                quantity = 11
            else:
                quantity = 8
            UserNutrients.create(user = user, nutrient = zinc, quantity = quantity, measure_unit = mg)

    tables.append(UserNutrients)

    with sqlite_db:
        # create all tables above
        sqlite_db.create_tables(tables)

    # return dictionary to update globals() in calling script
    ret_d = {}
    ret_d.update({"sqlite_db": sqlite_db})
    ret_d.update({table.__name__: table for table in tables})
    return ret_d
    # return {"hehe": Recipe.__name__}

def export_database():
    """
    this method uses base model .export_model function
    """
    # export tables
    for table in tables:
        table.export_model()
