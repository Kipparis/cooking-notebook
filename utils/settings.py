import os

# api.nal.usda.gov
api_key = os.environ['NAL_USDA_GOV_API_KEY']

# nutrient log file
NUTRIENTS_LOG_FILE = open("log/nutrients.log", "w")


base_mu = ["g", "mg", "mcg"]    # conves to which I parse
