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
    parser.add_argument('--force', help='overwrite any existing files', action='store_true', dest='is_force')
    parser.add_argument('-t', '--target', help='name of systemd target to create', action='store', dest='target', required=True)
    parser.add_argument('-r', '--repo', help='name of rpm repository to filter services', action='store', dest='repo', required=True)
    args = parser.parse_args()
    return args

def create_target(target, repo, is_dryrun, is_force):
    from textwrap import dedent, indent
    from os import path
    from sys import exit
    file_content = dedent('''\
    [Unit]
    Description=Custom Target {t} of Services From RPM Repository {r}
    Requires=multi-user.target network.target
    After=multi-user.target network.target
    Conflicts=emergency.target rescue.target
    AllowIsolate=no''').format(t=target, r=repo)

    file_path = '/etc/systemd/system/' + str(target) + '.target'
    print('INFO: creating systemd target file')

    if path.exists(file_path) and not is_force:
        print(f'ERROR: file already exists \'{file_path}\'')
        exit(1)

    if path.exists(file_path) and is_force:
        print(f'WARNING: overwriting file \'{file_path}\'')

    if is_dryrun:
        print(indent(f'# {file_path}', '    '))
        print(indent(file_content, '    '))
        return

    try:
        with open(file_path, 'w') as file:
            file.write(file_content)
    except PermissionError:
        print('ERROR: permission denied, try running again with root permissions')

#def find_services():
#def modify_services():
#def output():

def main():
    args = argparser()
    target = args.target
    repo = args.repo
    is_dryrun = args.is_dryrun
    is_force = args.is_force

    create_target(target, repo, is_dryrun, is_force)

    inclusions, exceptions = load_config()

main()
