## systemd-target-creator
Have you ever wanted to group together a bunch of systemd services?

### How it works
Given the name of an rpm repository this script will find all systemd service files installed by packages from that repository, then create a systemd target to control them.

### Use cases
This is useful if you have a custom repo that provides several systemd services that may be useful to control (start, stop, or monitor) with a single command

### Supported Platforms
The Current implementation only supports **Red Hat Enterprise Linux 8/7**

### Requirements
```
required packages (rpms) for el8:
  - python36
  - python3-pyyaml
  - python3-dnf

required packages (rpms) for el7:
  - python3
  - python36-PyYAML
  - yum-utils
```

### How to run
- Ensure you have a copy of `systemd-target-creator.py` and `config.yml` in a local directory on your system.
- Wanna get an idea of what this script will try to do?
  - do a dryrun `./systemd-target-creator.py -t TARGET -r REPO --dryrun`
- Still not sure what is going on?
  - try adding the verbose flag. `./systemd-target-creator.py -t TARGET -r REPO --dryrun -v`
- Want to add or remove a service?
  - modify the `config.yml`
- Not sure how to edit the `.yml` or yaml files?
  - check the [online yaml documentation](https://yaml.org/spec/1.2.2/#22-structures)
- Ready to try it out for real?
  - re-run with root permission `sudo ./systemd-target-creator.py -t TARGET -r REPO`
- Did the script stop due to a file already existing?
  - verify this file is safe to overwrite or make a backup just in case!
  - then add the force flag `sudo ./systemd-target-creator.py -t TARGET -r REPO --force`
- Not happy with the result?
  - add the undo flag `sudo ./systemd-target-creator.py -t TARGET -r REPO --undo`
- Not sure if you want to undo?
  - add the dryrun flag too `sudo ./systemd-target-creator.py -t TARGET -r REPO --undo --dryrun`

### Command Help
```bash
usage: systemd-target-creator.py [-h] [--dryrun] [--force] [--undo] [-v] -t TARGET -r REPO

create custom systemd targets to control multiple systemd services at once!

optional arguments:
  -h, --help            show this help message and exit
  --dryrun              show changes without making them
  --force               overwrite any existing files
  --undo                undo changes
  -v, --verbose         show more output
  -t TARGET, --target TARGET
                        name of systemd target to create
  -r REPO, --repo REPO  name of rpm repository to filter services

```

### Example
```bash
# create custom systemd target named 'hashi'
# that will be able to control all systemd services
# that were installed by packages from the hashicorp rpm repository
sudo ./systemd-target-creator.py -t hashi -r hashicorp
```

### Controlling the target
```bash
# check for status of target dependencies
systemctl list-dependencies hashi.target

# stop all services controlled by target
systemctl stop hashi.target

# start all services controlled by target
systemctl start hashi.target
```
