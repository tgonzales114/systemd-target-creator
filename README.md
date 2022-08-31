# systemd-target-creator
Have you ever wanted to group together a bunch of systemd services?

# How it works
Given the name of an rpm repository it will find all systemd service files installed by packages from that repository, then create a systemd target to control them.

# Use cases
This is useful if you have a custom repo that provides several systemd services that may be useful to control/monitor all at once

# How to run
First you run `find-service-data.sh` this will generate a file `output.txt`

Then you run `create-target.sh` which takes two positional arguments, target_name and rpm_repo_name
```bash
# example command
sudo ./create-target.sh hashi hashicorp
```
The above command will create a custom systemd target `hashi.target` that will be able to control all systemd services that were installed from packages that came from the repository `hashicorp`

# Controlling the target
```bash
# check for status of target dependencies (a bit verbose)
systemctl list-dependencies hashi.target

# stop all services controlled by target
systemctl stop hashi.target

# start all services controlled by target
systemctl start hashi.target
```
