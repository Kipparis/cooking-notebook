import requests
import json
from bs4 import BeautifulSoup
import re

def find_nutrients(name):
    """
    return array of tuples (nutrient, qty, mu)
    """
    url_food_search = "https://api.nal.usda.gov/fdc/v1/foods/search"
    url_nutrient_search = "https://api.nal.usda.gov/fdc/v1/food/{fdcId}"
    api_key    = "H0hI6Je1QeGfGpr0J7AtbsrMp6cjS7jeAwaSGXnj"

    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    headers    = {'User-Agent': user_agent}
    data       = {'api_key': api_key,
                  'query':   name}

    query   = requests.get(url_food_search, params=data)
    print(query.url)
    content = query.json()
    with open(f"cache/{name}.json", "w") as fl:
        print(content, file=fl)

    print("webcontent:", content, sep="\n")
    soup = BeautifulSoup(content, "html.parser")
    print("searching for elements")
    for element in soup.find_all(string=re.compile(f'{name}, nfs', re.IGNORECASE)):
        print(element)
    return None, None, None

if __name__ == "__main__":
    find_nutrients('potato')
