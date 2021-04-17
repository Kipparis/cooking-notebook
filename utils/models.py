import os
from peewee import *
import pandas as pd

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
            # calculate needed nutrients
            UserNutrients.calculate_nutrients(user)

        @property
        def age(self):
            return (date.today() - self.birth_date).years

        @property
        def sex_rounded(self):
            return (round(self.sex) == 0 ? 'male' : 'female')


    tables.append(User)

    class Nutrient(BaseModel):
        id = AutoField()
        name = TextField(unique = True)
        underdose = TextField(null = True)  # how you fell, if you don't have enough of this nutrient
        overdose = TextField(null = True)   # how you fell, if you have too much of this nutrient

    tables.append(Nutrient)

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

            calcium_underdose = "Osteoporosis (brittle bones) osteomalacia (soft bones), muscle spasms and cramping, rickets (a preventable bone disease in childhood)"
            calcium, created = Nutrient.get_or_create(name = "calcium", underdose = calcium_underdose)
            # calculate qty
            if user.age >= 19 and user.age <= 50:
                quantity = 1000
            elif user.sex_rounded == 'male' and user.age >= 71:
                quantity = 1200
            elif user.sex_rounded == 'female' and user.age >= 51:
                quantity = 1200
            else:
                quantity = 1000
            UserNutrients.create(user = user, nutrient = calcium, quantity = quantity, measure_unit = mg)

            chloride, created = Nutrient.get_or_create(name = "chloride")
            # calculate qty
            if user.age >= 19 and user.age <= 50:
                quantity = 2300
            elif user.age <= 70:
                quantity = 2000
            else:
                quantity = 1800
            UserNutrients.create(user = user, nutrient = chloride, quantity = quantity, measure_unit = mg)

            copper, created = Nutrient.get_or_create(name = "copper")
            quantity = 900
            UserNutrients.create(user = user, nutrient = copper, quantity = quantity, measure_unit = mcg)

            fluoride, created = Nutrient.get_or_create(name = "fluoride")
            if user.sex_rounded == "male":
                quantity = 4
            else:
                quantity = 3
            UserNutrients.create(user = user, nutrient = fluoride, quantity = quantity, measure_unit = mg)

            B9_underdose = "Tiredness and fatigue, problems with nerve functioning, poor growth, weight loss, folate-deficiency anaemia"
            B9, created = Nutrient.get_or_create(name = "B9", underdose = B9_underdose)
            quantity = 400
            UserNutrients.create(user = user, nutrient = B9, quantity = quantity, measure_unit = mcg)

            iodine_underdose = "The thyroid gland becomes enlarged (called goitre) and in the long term, hypothyroidism develops with symptoms including weight gain, hair loss, dry skin, fatigue and slowed reflexes."
            iodine, created = Nutrient.get_or_create(name = "iodine", underdose = iodine_underdose)
            quantity = 150
            UserNutrients.create(user = user, nutrient = iodine, quantity = quantity, measure_unit = mcg)

            iron_underdose = "Tiredness and fatigue, shortness of breath, pale skin, poor memory, and decreased resistance to infection are the most common signs of iron deficiency anaemia."
            iron, created = Nutrient.get_or_create(name = "iron", underdose = iron_underdose)
            if user.sex_rounded == "male":
                quantity = 8
            elif user.age >= 19 and user.age <= 50:
                quantity = 18
            else:
                quantity = 8
            UserNutrients.create(user = user, nutrient = iron, quantity = quantity, measure_unit = mg)

            magnesium_underdose = "Tiredness and fatigue, muscle spasm and weakness, sleep disorders, irritability, agitation and anxiety"
            magnesium, created = Nutrient.get_or_create(name = "magnesium", underdose = magnesium_underdose)
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

            manganese, created = Nutrient.get_or_create(name = "manganese")
            if user.sex_rounded == "male":
                quantity = 2.3
            else:
                quantity = 1.8
            UserNutrients.create(user = user, nutrient = manganese, quantity = quantity, measure_unit = mg)

            molybdenum, created = Nutrient.get_or_create(name = "molybdenum")
            quantity = 45
            UserNutrients.create(user = user, nutrient = molybdenum, quantity = quantity, measure_unit = mcg)

            nickel, created = Nutrient.get_or_create(name = "nickel")
            quantity = 0
            UserNutrients.create(user = user, nutrient = nickel, quantity = quantity, measure_unit = mcg)

            phosphorus, created = Nutrient.get_or_create(name = "phosphorus")
            quantity = 700
            UserNutrients.create(user = user, nutrient = phosphorus, quantity = quantity, measure_unit = mg)

            selenium, created = Nutrient.get_or_create(name = "selenium")
            quantity = 55
            UserNutrients.create(user = user, nutrient = selenium, quantity = quantity, measure_unit = mcg)

            choline, created = Nutrient.get_or_create(name = "choline")
            if user.sex_rounded == "male":
                quantity = 550
            else:
                quantity = 425
            UserNutrients.create(user = user, nutrient = choline, quantity = quantity, measure_unit = mg)

            sodium_underdose = "The issue with sodium is that we have too much! High intakes of salt are associated with high blood pressure, which is a risk factor for kidney disease and cardiovascular disease (such as heart disease and stroke)."
            sodium, created = Nutrient.get_or_create(name = "sodium", underdose = sodium_underdose)
            if user.age >= 19 and user.age <= 50:
                quantity = 1500
            elif user.age <= 70:
                quantity = 1300
            else:
                quantity = 1200
            UserNutrients.create(user = user, nutrient = sodium, quantity = quantity, measure_unit = mg)

            vanadium, created = Nutrient.get_or_create(name = "vanadium")
            quantity = 0
            UserNutrients.create(user = user, nutrient = vanadium, quantity = quantity, measure_unit = mcg)

            A_underdose = "Poor vision, increased susceptibility to infection."
            A, created = Nutrient.get_or_create(name = "A", underdose = A_underdose)
            if user.sex_rounded == "male":
                quantity = 900
            else:
                quantity = 700
            UserNutrients.create(user = user, nutrient = A, quantity = quantity, measure_unit = mcg)

            B3_underdose = "Deficiency is rare, and symptoms include diarrhoea, dementia, dermatitis, dizziness, confusion, swollen tongue, irritability, loss of appetite, weakness."
            B3, created = Nutrient.get_or_create(name = "B3", underdose = B3_underdose)
            if user.sex_rounded == "male":
                quantity = 16
            else:
                quantity = 14
            UserNutrients.create(user = user, nutrient = B3, quantity = quantity, measure_unit = mg)

            B6_underdose = "Smooth tongue, cracks in corners of the mouth, muscle twitching, convulsions, irritability, confusion and dermatitis."
            B6, created = Nutrient.get_or_create(name = "B6", underdose = B6_underdose)
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

            C_underdose = "Dry skin, poor wound healing, bleeding gums, bruising, increased risk of infection."
            C, created = Nutrient.get_or_create(name = "C", underdose = C_underdose)
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

            E, created = Nutrient.get_or_create(name = "E")
            quantity = 15
            UserNutrients.create(user = user, nutrient = E, quantity = quantity, measure_unit = mg)

            zinc_underdose = "Loss of taste, poor growth and wound healing, dry skin, increased susceptibility to infection."
            zinc, created = Nutrient.get_or_create(name = "zinc", underdose = zinc_underdose)
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
