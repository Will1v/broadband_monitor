# Purpose

Tiny util to ping router + google.com on a regular basis to see prove short, sporadic and intermitent drops in broadband connection which are otherwise hard to spot.

![image](https://github.com/Will1v/broadband_monitor/assets/24796480/5d5b927e-de4f-447e-acde-9eeb70c89e70)


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

**Note**: it is recommended to use a `ping_interval_in_seconds` of at least `10` to allow for the pings and DB write to happen.

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


# Grafana dashboard

Using Grafana can be a nice way to visualise the collected stats. 

I did this on a Raspberry Pi 4 which runw both Grafana and broadband_monitor to continuously monitor the state of my broadband:

![broadband_monitor_grafana_dashboard](https://github.com/Will1v/broadband_monitor/assets/24796480/3f543fe2-9289-4959-8362-8eedeb9df17f)
