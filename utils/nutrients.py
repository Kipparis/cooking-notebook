import requests
import json
import re
import os

from .settings import *

def parse_fdc_measure_unit(mu, qty, name):
    """
    CAUTION: UI is used to show biological activity for different vitamins
    example: 0.3ug of retinol is same biological activity as 0.6ug beta-carotene,
    so watch out which nutrient you intake
    """
    if mu == "ug":
        return qty, "mcg"
    elif mu == "iu":
        if name == "a":
            return qty * 0.3, "mcg"
        elif name == "c":
            return qty * 50, "mcg"
        elif name == "d":
            return qty / 40, "mcg"
        elif name == "e":
            return qty * 0.78, "mg"  # it's not a typo

    return qty, mu

def parse_fdc_nutrient_name(name):
    """
    remove shit and try to extract nutrient name same as in my database
    """
    # store nutrient name in group `name`
    # store B number in group `number`
    vitamin_re       = re.compile(r'vitamin (?P<name>[^,$ ]+)')
    vitamin_b_re     = re.compile(r'b-(?P<number>[0-9]+)')
    micronutrient_re = re.compile(r'.*, (?P<name>\w{1,2})\Z')
    total_marker     = re.compile(r'\A(?P<name>[^,]+), total')
    food_marker      = re.compile(r'\A(?P<name>[^,]+), food')

    match = vitamin_re.match(name)
    if match:
        vitamin_name = match.group('name')
        b_match = vitamin_b_re.match(vitamin_name)
        if b_match:
            vitamin_name = "B{}".format(b_match.group('number'))
        print("found match:", vitamin_name, "\tfor name:", name,
              file=NUTRIENTS_LOG_FILE)
        return vitamin_name

    match = micronutrient_re.match(name)
    if match:
        vitamin_name = match.group('name')
        print("found match:", vitamin_name, "\tfor name:", name,
              file=NUTRIENTS_LOG_FILE)
        return vitamin_name

    match = total_marker.match(name)
    if match:
        vitamin_name = match.group('name')
        print("found match:", vitamin_name, "\tfor name:", name,
              file=NUTRIENTS_LOG_FILE)
        return vitamin_name

    match = food_marker.match(name)
    if match:
        vitamin_name = match.group('name')
        print("found match:", vitamin_name, "\tfor name:", name,
              file=NUTRIENTS_LOG_FILE)
        return vitamin_name
    return name

def find_nutrients(name):
    """
    return array of tuples (nutrient, qty, mu)
    """
    url_food_search     = "https://api.nal.usda.gov/fdc/v1/foods/search"
    url_nutrient_search = "https://api.nal.usda.gov/fdc/v1/food/{fdcId}"
    json_filename       = f'cache/{name}.json'

    data       = {'api_key': api_key,
                  'query':   name}

    if os.path.isfile(json_filename): # file exists
        # read json from file
        with open(json_filename, "r") as fl:
            content = json.load(fl)
    else:                             # file doesn't exist
        # making request
        query   = requests.get(url_food_search, params=data)
        print(query.url)
        content = query.json()
        with open(json_filename, "w") as fl:
            json.dump(content, fl, indent=4)

    # TODO:    calculate average across nutrients which are in center 75%
    # WHY:     because top score products might have out of range vitamins
    # EXAMPLE: top score product have 5000UI of vitamin A, but other have up to 200
    foods = sorted(content['foods'], key=lambda entry: entry['score'], reverse=True)   # descending order by `score` field
    for food in foods:   # search food
        descr = food['lowercaseDescription']
        if descr == name or descr == f"{name}, nfs":
            print("|using entry named: '{}'".format(descr), file=NUTRIENTS_LOG_FILE)
            print("|score: {}".format(food["score"]), file=NUTRIENTS_LOG_FILE)
            print("|brandOwner: {}".format(food.get("brandOwner"), ""), file=NUTRIENTS_LOG_FILE)
            for nutrient in food['foodNutrients']:
                qty = nutrient['value']
                if qty == 0:
                    continue
                name = parse_fdc_nutrient_name(nutrient['nutrientName'].lower())
                qty, mu = parse_fdc_measure_unit(nutrient['unitName'].lower(), qty, name)
                yield name, qty, mu
            break

if __name__ == "__main__":
    for name, qty, mu in find_nutrients('salt'):
        print(f"\t{name}\t{qty}\t{mu}")
