import json
import random
import string

def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

    return config

def random_char(y):
    return ''.join(random.choice(string.ascii_letters) for x in range(y))


