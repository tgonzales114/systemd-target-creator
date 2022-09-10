#!/usr/bin/python3.6

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

def progress_bar(progress, total):
    full = '#'
    empty = '-'

    percent = 100 * (progress / float(total))
    bar = full * int(percent) + empty * (100 - int(percent))

    print('\r[' + str(bar) + '] ' + str(round(percent, 2)) + '%', end='\r')

def get_service_files():
    import subprocess
    from sys import exit
    from textwrap import indent

    src1 = '/usr/lib/systemd/system'
    src2 = '/etc/systemd/system'
    cmd = f'find {src1} {src2} -name \'*.service\' ! -type l'

    sp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rc = sp.wait()
    stdout_byte, stderr_byte = sp.communicate()

    stdout = stdout_byte.decode('UTF-8')
    stderr = stderr_byte.decode('UTF-8')

    if rc != 0:
        print(f'ERROR: while getting systemd service files, return code: \'{rc}\', printing stderr')
        print(indent(stderr, '    '))
        exit(rc)

    service_files = stdout.strip().split('\n')
    return service_files


def get_service_name(service_file):
    name = service_file.split('/')[-1]
    return name

def get_service_rpm(service_file):
    import subprocess
    from sys import exit
    from textwrap import indent

    cmd = f'rpm -qf {service_file} --queryformat "%{{NAME}}\n"'

    sp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rc = sp.wait()
    stdout_byte, stderr_byte = sp.communicate()

    stdout = stdout_byte.decode('UTF-8')
    stderr = stderr_byte.decode('UTF-8')

    if rc == 1:
        rpm = 'none'
        return rpm

    if rc > 1:
        print(f'ERROR: while trying to get rpm info for systemd service file \'{service_file}\', return code: \'{rc}\', printing stderr')
        print(indent(stderr, '    '))
        exit(rc)

    rpm = stdout.strip().split('\n')[0]
    return rpm

def get_rpm_from_repo(rpm):
    import dnf

    base = dnf.Base()
    base.fill_sack()

    q = base.sack.query()
    i = q.installed()
    f = i.filter(name=rpm)

    for pkg in f:
        return pkg.from_repo

def get_all_service_data():
    print('INFO: getting all systemd service data, this can take a few minutes')

    service_data = []
    files = get_service_files()
    total = len(files)
    i = 0
    print(f'INFO: found {total} systemd service files')
    for f in files:
        i += 1
        progress_bar(i, total)
        service = get_service_name(f)
        rpm = get_service_rpm(f)
        from_repo = get_rpm_from_repo(rpm)
        data = { 'file': f, 'service': service, 'rpm': rpm, 'from_repo': from_repo }
        service_data.append(data)

    print()
    return service_data

def get_services_to_modify(service_data, repo):
    from sys import exit

    services = []

    for i in service_data:
        from_repo = i['from_repo']
        if from_repo == repo:
            service_file = i['file']
            services.append(service_file)

    if not services:
        print(f'ERROR: could not find any systemd services that were installed from packages from the rpm repository \'{repo}\' is this a typo?')
        exit(1)

    return services

#def modify_services():
#def output():

def main():
    args = argparser()
    target = args.target
    repo = args.repo
    is_dryrun = args.is_dryrun
    is_force = args.is_force

    service_data = get_all_service_data()

    get_services_to_modify(service_data, repo)

    create_target(target, repo, is_dryrun, is_force)

    inclusions, exceptions = load_config()

main()
