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

class Recipe(BaseModel):
    id   = AutoField()
    name = TextField()
    meal_type = ForeignKeyField(MealType, backref='recipes')

class Ingredient(BaseModel):
    id   = AutoField()
    name = TextField()

class RecipeIngredient(BaseModel):
    id         = AutoField()
    recipe     = ForeignKeyField(Recipe)
    ingredient = ForeignKeyField(Ingredient)
    quantity   = DecimalField(max_digits     = 10,
                              decimal_places = 2,
                              auto_round     = True)
    measure_units = TextField()


def create_database(force = False):
    with sqlite_db:
        # create all tables above
        sqlite_db.create_tables([Recipe, MealType, Ingredient, RecipeIngredient])
