#!/usr/bin/python3

def load_config():
    import yaml
    config = 'config.yml'
    with open(config, 'r') as file:
        data = yaml.safe_load(file)
    i = data['inclusions']
    x = data['exclusions']
    return i, x

i, x = load_config()

print(f"inclusions:{i} exclusions {x}")
