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


![image](https://github.com/user-attachments/assets/e2c0e43a-d5a3-48d0-b8ab-43e39af475e5)


# Limitations

Because Grafana doens't support read-only databases, you need to give the sqlite3 file write permissions to the `grafana` user.
This tends to lock the database and get the script to crash.
To get around this, you can enable [Write Ahead Logging (WAL)](https://grafana.com/docs/loki/latest/operations/storage/wal/)

Alternatively, you may want to switch to another database (postrgres, mysql,..).

## Configuring WAL

1. Enable WAL in Grafana:
- Edit `grafana.ini`:
``` sh
 sudo vi /etc/grafana/grafana.ini
```
- Set `wal` to `true`:
``` sh
# For "sqlite3" only. Enable/disable Write-Ahead Logging, https://sqlite.org/wal.html. Default is false.
;wal = true
```
2. In sqlite3, connect and enable WAL:
``` sh
# Connect to the DB
sqlite3 <database_name>

# Enable WAL mode
sqlite> PRAGMA journal_mode = WAL;
wal

# Verify the change
sqlite> PRAGMA journal_mode;
wal
```
3. Restart Grafana 

