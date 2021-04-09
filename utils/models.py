import os
from peewee import *
import pandas as pd

def create_database(db_fn, force = False):
    sqlite_db = SqliteDatabase(db_fn, pragmas=[('foreign_keys', 'on')])

    tables = []

    class BaseModel(Model):
        """A base model that will use our Sqlite database."""
        @classmethod
        def export_model(cls):
            with open(f"{cls.__name__}.csv", "w") as fl:
                pd.DataFrame(list(cls.select().dicts())).to_csv(fl, index=False)

        class Meta:
            database = sqlite_db

    class MealType(BaseModel):
        id   = AutoField()
        name = TextField()

        def output_choices():
            for mtype in MealType.select():
                print(f"{mtype.id}. {mtype.name}")

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

    tables.append(Recipe)


    class Ingredient(BaseModel):
        id   = AutoField()
        name = TextField()

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
