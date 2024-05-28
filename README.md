# Purpose

Tiny util to ping router + google.com on a regular basis to see prove short, sporadic and intermitent drops in broadband connection which are otherwise hard to spot.

## Context

I've been experiencing brief and interminent outages on my broadband. 
So I wrote this script that pings both my router and google.com every X (20) seconds. This should allow me to see whether the issue is internal or external, as well as how often it happens and for how long. 

# Getting started
## Installing required modules

Ensure `pip` is installed, then run:
``` sh
pip install -r requirements.txt
```

## Configuration files

1. Edit `./config/config_template.yaml` and set your router's IP address instead of `<ip to the router>`.
2. Rename `./config/config_template.yaml` to `./config/config.yaml`

## Crontab

You can crontab the run on reboot to constantly monitor. It can be best to allow a bit of a delay after reboot:

1. Edit the crontab:
``` sh
crontab -e
```
2. Then add:
``` sh
@reboot sleep 60; <path to project>/broadband_monitor/broadband_monitor.sh
```
