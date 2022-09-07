#!/usr/bin/python3

def load_config():
    import yaml
    config = 'config.yml'
    with open(config, 'r') as file:
        data = yaml.safe_load(file)
    i = data['inclusions']
    x = data['exclusions']
    return i, x

def argparser():
    import argparse
    parser = argparse.ArgumentParser(description='create custom systemd targets to control multiple systemd services at once!')
    parser.add_argument('--dryrun', help='show changes without making them', action='store_true', dest='is_dryrun')
    args = parser.parse_args()
    return args

#def output():
#def create_target():
#def find_services():
#def modify_services():

def main():
    args = argparser()
    i, x = load_config()
    print(f"inclusions: {i} exclusions: {x}")
    print(f"is_dryrun: {args.is_dryrun}")

main()
