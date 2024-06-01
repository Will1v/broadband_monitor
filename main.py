#!/usr/bin/python

import subprocess
import os, sys
import json
from logger import get_logger
from broadband_monitor.config import config
import time
from datetime import datetime
import sqlite3
import re
from typing import Tuple, Union

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logger = get_logger(__name__)


def ping_host(host: str):
    result = subprocess.run(
        ["ping", "-c", "4", host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 0:
        return extract_rtt_stats(result.stdout)
    else:
        logger.error(
            f"Ping to {host} failed. \nStdout: \n{result.stdout} \nStderr: \n{result.stderr}"
        )
        return None


def extract_rtt_stats(
    ping_output: str,
) -> Union[Tuple[float, float, float], None]:
    # Regex pattern to extract min/avg/max/mdev values from ping output
    pattern = r"(?<=rtt min/avg/max/mdev = )(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)"
    match = re.search(pattern, ping_output)
    if match:
        min_rtt = float(match.group(1))
        avg_rtt = float(match.group(2))
        max_rtt = float(match.group(3))
        return min_rtt, avg_rtt, max_rtt
    else:
        logger.error("Could not parse the ping output.")
        return None


def main():
    # Initialize variables...
    counter = 0
    router_ok_counter = 0
    internet_ok_counter = 0
    router_nok_counter = 0
    internet_nok_counter = 0
    interval_in_s = config.ping_interval_in_seconds
    counter_modulo = (
        60 * 60 / interval_in_s
    )  # Will log a heartbreat with some stats every hour
    router_ip, router_alias, internet_address, internet_address_alias = (
        config.router_ip,
        config.router_alias,
        config.internet_address,
        config.internet_address_alias,
    )

    # Init DB
    conn = init_db()

    router_id = register_target(config.router_ip, config.router_alias)
    internet_id = register_target(
        config.internet_address, config.internet_address_alias
    )

    logger.info(
        f"Pinging router at {router_ip} and internet address at {internet_address}"
    )
    while True:
        router_status = ping_host(router_ip)
        # TODO: Duplicate code. Refactor to make just one function to both router and internet (and any other target)
        if router_status:
            router_ok_counter += 1
            router_min, router_avg, router_max = router_status
        else:
            router_nok_counter += 1

        internet_status = ping_host(internet_address)
        if internet_status:
            internet_ok_counter += 1
            internet_min, internet_avg, internet_max = internet_status
        else:
            internet_nok_counter += 1

        counter += 1
        register_status_to_db(
            True if router_status else False,
            router_min,
            router_max,
            router_avg,
            router_id,
        )
        register_status_to_db(
            True if internet_status else False,
            internet_min,
            internet_max,
            internet_avg,
            internet_id,
        )

        if (counter - 1) % counter_modulo == 0:
            logger.info(
                f"{counter} pings run. Router: {router_ok_counter/counter * 100}% success (OK: {router_ok_counter} / KO: {router_nok_counter}) | Internet: {internet_ok_counter/counter * 100}% success (OK: {internet_ok_counter} / KO: {internet_nok_counter})"
            )
        time.sleep(interval_in_s)


def register_target(target: str, target_alias: str) -> int:
    conn = get_db_connection()
    get_id_sql_query = "SELECT target_id FROM targets WHERE ip_or_url = ?"
    res = conn.cursor().execute(get_id_sql_query, [target]).fetchone()
    if not res:
        targets_sql_query = (
            "INSERT OR REPLACE INTO targets (ip_or_url, alias) VALUES (?, ?)"
        )
        conn.cursor().execute(targets_sql_query, [target, target_alias])
        conn.commit()
        res = conn.cursor().execute(get_id_sql_query, [target]).fetchone()
    return res[0]


def register_status_to_db(
    target_status: bool,
    rtt_min: Union[float, None],
    rtt_max: Union[float, None],
    rtt_avg: Union[float, None],
    target_id: int,
):
    conn = get_db_connection()
    # Insert ping status
    sql_status_query = (
        "INSERT INTO ping_results (timestamp, target_id, success) VALUES (?, ?, ?)"
    )
    conn.cursor().execute(sql_status_query, [datetime.now(), target_id, target_status])
    sql_stats_query = "INSERT INTO ping_stats (timestamp, target_id, rtt_min, rtt_max, rtt_avg) VALUES (?, ?, ?, ?, ?)"
    conn.cursor().execute(
        sql_stats_query, [datetime.now(), target_id, rtt_min, rtt_max, rtt_avg]
    )
    conn.commit()


def init_db():
    conn = get_db_connection()
    build_db_path = os.path.expanduser(config.database.build_sql_file_path)
    try:
        with open(build_db_path, "r") as file:
            sql_script = file.read()
        conn.executescript(sql_script)
    except sqlite3.Error as e:
        logger.exception(f"Error executing build DB SQL script: {e}")
    except FileNotFoundError as e:
        logger.exception(f"Error: SQL file not found: {e}")
    logger.info("DB initialized...")


def get_db_connection():
    # Connect to DB
    conn = None
    db_file = os.path.expanduser(config.database.file_path)
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logger.exception(f"Error connecting to database: {e}")
    except FileNotFoundError as e:
        logger.exception(f"Error: DB file not found: {e}")


if __name__ == "__main__":
    main()
