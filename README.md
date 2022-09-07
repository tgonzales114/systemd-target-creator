## systemd-target-creator
Have you ever wanted to group together a bunch of systemd services?

### How it works
Given the name of an rpm repository it will find all systemd service files installed by packages from that repository, then create a systemd target to control them.

### Use cases
This is useful if you have a custom repo that provides several systemd services that may be useful to control/monitor all at once

### How to run
First run `find-service-data.sh` this will create a file `output.txt`

Finally run `create-target.sh` which takes two positional arguments, target_name and rpm_repo_name
```bash
# create output.txt with systemd service data
./find-service-data.sh

# create custom systemd target hashi that will be able to control all systemd services installed by packages from the hashicorp rpm repository
sudo ./create-target.sh hashi hashicorp
```

### Controlling the target
```bash
# check for status of target dependencies (a bit verbose)
systemctl list-dependencies hashi.target

# stop all services controlled by target
systemctl stop hashi.target

# start all services controlled by target
systemctl start hashi.target
```
