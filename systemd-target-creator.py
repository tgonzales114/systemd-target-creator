#!/usr/bin/python3

def load_config(is_verbose):
    import yaml
    from sys import exit
    config = 'config.yml'
    print(f'INFO: loading exclusions and inclusions from config file \'{config}\'')
    with open(config, 'r') as file:
        try:
            data = yaml.safe_load(file)
            inclusions = data['inclusions']
            exclusions = data['exclusions']
        except:
            print(f'ERROR: could not properly load data from config file \'{config}\' try running running \'yamllint {config}\' for more details')
            exit(1)

    if is_verbose:
        for i in inclusions:
            print(f'INFO: loaded inclusion of \'{i}\' will attempt to include later')
        for x in exclusions:
            print(f'INFO: loaded exclusion of \'{x}\' will attempt to remove later')

    return inclusions, exclusions

def argparser():
    import argparse
    parser = argparse.ArgumentParser(description='create custom systemd targets to control multiple systemd services at once!')
    parser.add_argument('--dryrun', help='show changes without making them', action='store_true', dest='is_dryrun')
    parser.add_argument('--force', help='overwrite any existing files', action='store_true', dest='is_force')
    parser.add_argument('--undo', help='undo changes', action='store_true', dest='is_undo')
    parser.add_argument('-v', '--verbose', help='show more output', action='store_true', dest='is_verbose')
    parser.add_argument('-t', '--target', help='name of systemd target to create', action='store', dest='target', required=True)
    parser.add_argument('-r', '--repo', help='name of rpm repository to filter services', action='store', dest='repo', required=True)
    args = parser.parse_args()
    return args

def create_target(target, repo, is_dryrun, is_force, is_verbose, is_undo):
    from textwrap import dedent, indent
    from os import path
    from os import remove
    from sys import exit
    file_content = dedent('''\
    [Unit]
    Description=Custom Target {t} of Services From RPM Repository {r}
    After=multi-user.target network.target
    Conflicts=emergency.target rescue.target
    AllowIsolate=no''').format(t=target, r=repo)

    file_path = '/etc/systemd/system/' + str(target) + '.target'
    if not is_undo:
        if is_dryrun:
            print('INFO: would create systemd target file')
        else:
            print('INFO: creating systemd target file')

        if path.exists(file_path) and not is_force:
            print(f'ERROR: file already exists \'{file_path}\' if you are sure you want to overwrite this file re-run with --force')
            exit(1)

        if path.exists(file_path) and is_force:
            print(f'WARNING: overwriting file \'{file_path}\'')

        if is_verbose:
            print(indent(f'# {file_path}', '    '))
            print(indent(file_content, '    '))

        if not is_dryrun:
            try:
                with open(file_path, 'w') as file:
                    file.write(file_content)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

    if path.exists(file_path) and is_undo:
        if is_dryrun:
            print(f'WARNING: would remove systemd target file \'{file_path}\'')
        else:
            print(f'WARNING: removing systemd target file \'{file_path}\'')
            try:
                remove(file_path)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

def get_os_release():
    import csv
    import pathlib
    from sys import platform
    if platform == 'linux':
        path = pathlib.Path('/etc/os-release')
        with open(path) as stream:
            stream_non_empty = []
            for line in stream.readlines():
                if line.strip():
                    stream_non_empty.append(line)
            reader = csv.reader(stream_non_empty, delimiter='=')
            os_release = dict(reader)
        return os_release
    else:
        print('ERROR: unsupported platform')

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

    cmd = f'rpm -qf {service_file} --queryformat \'%{{NAME}}\n\''

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

def get_rpm_from_repo_el7(rpm):
    import subprocess
    from sys import exit
    from textwrap import indent

    if rpm == 'none':
        return rpm

    cmd = f'yumdb get from_repo {rpm} | grep \'=\' | tail -n 1 | awk \'{{print $NF}}\''

    sp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rc = sp.wait()
    stdout_byte, stderr_byte = sp.communicate()

    stdout = stdout_byte.decode('UTF-8')
    stderr = stderr_byte.decode('UTF-8')

    if rc != 0:
        print(f'ERROR: while getting rpm from_repo value for \'{rpm}\', return code: \'{rc}\', printing stderr')
        print(indent(stderr, '    '))
        exit(rc)

    from_repo = stdout.strip()
    return from_repo

def get_rpm_from_repo_el8(rpm):
    import dnf

    if rpm == 'none':
        return rpm

    base = dnf.Base()
    base.fill_sack()

    q = base.sack.query()
    i = q.installed()
    f = i.filter(name=rpm)

    latest_rpm = f[-1]
    from_repo = latest_rpm.from_repo
    return from_repo

def get_all_service_data(os_version, is_verbose):
    from re import match
    print('INFO: getting all systemd service data, this can take a few minutes')
    service_data = []
    files = get_service_files()
    total = len(files)
    i = 0

    if is_verbose:
        print(f'INFO: found {total} systemd service files')

    for f in files:
        i += 1
        progress_bar(i, total)
        service = get_service_name(f)
        rpm = get_service_rpm(f)
        if os_version == '8' or match('^8\.[0-9]$', os_version):
            from_repo = get_rpm_from_repo_el8(rpm)
        elif os_version == '7' or match('^7\.[0-9]$', os_version):
            from_repo = get_rpm_from_repo_el7(rpm)
        else:
            print(f'ERROR: unsupported operating system major version \'{os_version}\'')
        data = { 'file': f, 'service': service, 'rpm': rpm, 'from_repo': from_repo }
        service_data.append(data)

    print()
    return service_data

def get_services_to_modify(service_data, repo, inclusions, exclusions):
    from sys import exit
    from operator import itemgetter

    services = []

    for i in service_data:
        from_repo = i['from_repo']
        if from_repo == repo:
            services.append(i)

    print('INFO: adding inclusions to list of systemd services to be modified')
    for i in inclusions:
        if not i in map(itemgetter('service'), service_data):
            print(f'WARNING: systemd service \'{i}\' does not exist, not including in list')
            continue
        if i in map(itemgetter('service'), services):
            print(f'NOTICE: systemd service \'{i}\' already added, do not need to include in list')
            continue
        print(f'NOTICE: adding systemd service \'{i}\'')
        for s in service_data:
            if i == s['service']:
                services.append(s)

    print('INFO: removing exclusions from list of systemd services to be modified')
    for i in exclusions:
        if not i in map(itemgetter('service'), service_data):
            print(f'WARNING: systemd service \'{i}\' does not exist, not removing from list')
            continue
        if not i in map(itemgetter('service'), services):
            print(f'NOTICE: could not find systemd service \'{i}\' in list, do not need to remove from list')
            continue
        print(f'NOTICE: removing systemd service \'{i}\'')
        for s in service_data:
            if i == s['service']:
                services.remove(s)

    if not services:
        print(f'ERROR: could not find any systemd services that were installed from packages from the rpm repository \'{repo}\' is this a typo?')
        exit(1)

    return services

def modify_services(service, target, is_dryrun, is_force, is_verbose, is_undo):
    from textwrap import dedent, indent
    from os import path
    from os import mkdir
    from os import rmdir
    from os import remove
    from sys import exit

    file_content = dedent('''\
    [Unit]
    StopWhenUnneeded=yes
    PartOf={t}.target

    [Install]
    WantedBy={t}.target''').format(t=target)

    file_dir = f'/etc/systemd/system/{service}.d'
    file_name = f'override.conf'
    file_path = f'{file_dir}/{file_name}'

    append_content = f'\nWants={service}'
    target_path = f'/etc/systemd/system/{target}.target'

    if not is_undo:
        if not path.exists(file_dir):
            if is_dryrun:
                print(f'INFO: would create override directory for systemd service {service}')
            else:
                print(f'INFO: creating override directory for systemd service {service}')

            if is_verbose:
                print(indent(f'# {file_dir}', '    '))
            if not is_dryrun:
                try:
                    mkdir(file_dir)
                except PermissionError:
                    print('ERROR: permission denied, try running again with root permissions')
                    exit(1)

        if is_dryrun:
            print(f'INFO: would create override file for systemd service {service}')
        else:
            print(f'INFO: creating override file for systemd service {service}')

        if path.exists(file_path) and not is_force:
            print(f'ERROR: file already exists \'{file_path}\' if you are sure you want to overwrite this file re-run with --force')
            exit(1)

        if path.exists(file_path) and is_force:
            print(f'WARNING: overwriting file \'{file_path}\'')

        if is_verbose:
            print(indent(f'# {file_path}', '    '))
            print(indent(file_content, '    '))

        if not is_dryrun:
            try:
                with open(file_path, 'w') as file:
                    file.write(file_content)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

        if is_dryrun:
            print(f'INFO: would append service to target file')
        else:
            print(f'INFO: appending service to target file')

        if is_verbose:
            print(indent(f'# {target_path}', '    '))
            print(indent(append_content, '    '))

        if not is_dryrun:
            try:
                with open(target_path, 'a') as file:
                    file.write(append_content)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

    if path.exists(file_path) and is_undo:
        if is_dryrun:
            print(f'WARNING: would remove override file \'{file_path}\'')
        else:
            print(f'WARNING: removing override file \'{file_path}\'')
            try:
                remove(file_path)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

    if path.exists(file_dir) and is_undo:
        if is_dryrun:
            print(f'WARNING: would remove override directory \'{file_dir}\'')
        else:
            print(f'WARNING: removing override directory \'{file_dir}\'')
            try:
                rmdir(file_dir)
            except PermissionError:
                print('ERROR: permission denied, try running again with root permissions')
                exit(1)

def daemon_reload(is_dryrun):
    import subprocess
    from sys import exit
    from textwrap import indent

    cmd = f'systemctl daemon-reload'

    if is_dryrun:
        print(f'INFO: would run command \'{cmd}\' for systemd file changes to take affect')
    else:
        print(f'INFO: running command \'{cmd}\' for systemd file changes to take affect')
        sp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        rc = sp.wait()
        stdout_byte, stderr_byte = sp.communicate()

        stdout = stdout_byte.decode('UTF-8')
        stderr = stderr_byte.decode('UTF-8')

        if rc != 0:
            print(f'ERROR: while running command \'{cmd}\', return code: \'{rc}\', printing stderr')
            print(indent(stderr, '    '))
            exit(rc)

def instructions(target, is_dryrun):
    from textwrap import dedent, indent

    message = dedent('''\
    # check the status of all services controlled by the target
    systemctl list-dependencies {t}.target

    # stop all services controlled by the target
    sudo systemctl stop {t}.target

    # start all services controlled by the target
    sudo systemctl start {t}.target''').format(t=target)

    if is_dryrun:
        print(f'INFO: would finish creating custom target: {target}.target')
    else:
        print(f'INFO: finished creating custom target: {target}.target')
    print('INFO: control commands:')
    print(indent(message, '    '))

def main():
    args = argparser()
    target = args.target
    repo = args.repo
    is_dryrun = args.is_dryrun
    is_force = args.is_force
    is_verbose = args.is_verbose
    is_undo = args.is_undo

    inclusions, exclusions = load_config(is_verbose)

    os_release = get_os_release()
    os_version = os_release['VERSION_ID']

    service_data = get_all_service_data(os_version, is_verbose)
    modify_service_data = get_services_to_modify(service_data, repo, inclusions, exclusions)
    create_target(target, repo, is_dryrun, is_force, is_verbose, is_undo)
    for item in modify_service_data:
        service=item['service']
        modify_services(service, target, is_dryrun, is_force, is_verbose, is_undo)

    daemon_reload(is_dryrun)
    if not is_undo:
        instructions(target, is_dryrun)

main()
