#!/usr/bin/python

import subprocess
import os, sys
import json
from logger import get_logger
from broadband_monitor.config import config
import time
from datetime import datetime
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logger = get_logger(__name__)


def ping_host(host):
    result = subprocess.run(
        ["ping", "-c", "4", host],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    success = True
    if result.returncode == 0:
        logger.debug(f"Ping to {host} was successful.")
        logger.debug(result.stdout)
    else:
        logger.error(f"Ping to {host} failed.")
        logger.error(result.stderr)
        return False
    return True


def main():
    # Initialize variables...
    counter = 0
    router_ok_counter = 0
    internet_ok_counter = 0
    router_nok_counter = 0
    internet_nok_counter = 0
    interval_in_s = 20
    counter_modulo = 60 * 60 / interval_in_s
    router_ip, internet_address = config.router_ip, config.internet_address

    # Init DB
    conn = init_db()

    logger.info(
        f"Pinging router at {router_ip} and internet address at {internet_address}"
    )
    while True:
        router_status = ping_host(router_ip)
        if router_status:
            router_ok_counter += 1
        else:
            router_nok_counter += 1

        internet_status = ping_host(internet_address)
        if internet_status:
            internet_ok_counter += 1
        else:
            internet_nok_counter += 1

        counter += 1
        register_status_to_db(router_status, internet_status)

        if (counter - 1) % counter_modulo == 0:
            logger.info(
                f"{counter} pings run. Router: {router_ok_counter/counter * 100}% success (OK: {router_ok_counter} / KO: {router_nok_counter}) | Internet: {internet_ok_counter/counter * 100}% success (OK: {internet_ok_counter} / KO: {internet_nok_counter})"
            )
        time.sleep(interval_in_s)


def register_status_to_db(router_status, internet_status):
    conn = get_db_connection()
    sql_query = "INSERT INTO ping_results (timestamp, router_success, internet_success) VALUES (?, ?, ?)"
    conn.cursor().execute(sql_query, [datetime.now(), router_status, internet_status])
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
