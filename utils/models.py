import os
from peewee import *

db_fn     = "recipe.db"
sqlite_db = SqliteDatabase(db_fn, pragmas=[('foreign_keys', 'on')])

class BaseModel(Model):
    """A base model that will use our Sqlite database."""
    class Meta:
        database = sqlite_db

class MealType(BaseModel):
    id   = AutoField()
    name = TextField()

    def output_choices():
        for mtype in MealType.select():
            print(f"{mtype.id}. {mtype.name}")

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
                                    measure_units = measure_unit) # see ^^^^^^^^^


class Ingredient(BaseModel):
    id   = AutoField()
    name = TextField()

class MeasureUnit(BaseModel):
    id   = AutoField()
    name = TextField()

    def output_choices():
        for unit in MeasureUnit.select():
            print(f"{unit.id}. {unit.name}")

class RecipeIngredient(BaseModel):
    id         = AutoField()
    recipe     = ForeignKeyField(Recipe)
    ingredient = ForeignKeyField(Ingredient)
    quantity   = DecimalField(max_digits     = 10,
                              decimal_places = 2,
                              auto_round     = True)
    measure_unit = ForeignKeyField(MeasureUnit)


def create_database(force = False):
    with sqlite_db:
        # create all tables above
        sqlite_db.create_tables([Recipe, MealType, Ingredient, MeasureUnit, RecipeIngredient])