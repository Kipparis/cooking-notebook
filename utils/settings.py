import os

def get_env_var(env_name):
    if env_name in os.environ:
        return os.environ[env_name]
    print(f"WARN: {env_name} is not in environments")
    return ""

# api.nal.usda.gov
api_key = get_env_var('NAL_USDA_GOV_API_KEY')

base_mu = ["g", "mg", "mcg"]    # conves to which I parse


base_mu = ["g", "mg", "mcg"]    # conves to which I parse
