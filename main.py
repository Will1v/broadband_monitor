#!/usr/bin/python

import subprocess
import asyncio
import os, sys
from logger import get_logger
from broadband_monitor.config import config
import time
from datetime import datetime
import psycopg2
import re
from typing import Tuple, Union


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logger = get_logger(__name__)

db_conn = psycopg2.connect(database=config.database.db_name,
                    host=config.database.db_host,
                    user=config.database.db_user,
                    password=config.database.password,
                    port=config.database.db_port)
db_conn.autocommit = True

async def ping_host(host: str):
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


async def main():
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
        start_time = time.time()
        router_status, internet_status = await asyncio.gather(
            ping_host(router_ip), ping_host(internet_address)
        )
        # TODO: Duplicate code. Refactor to make just one function to both router and internet (and any other target)
        if router_status:
            router_ok_counter += 1
            router_min, router_avg, router_max = router_status
        else:
            router_nok_counter += 1

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
        elapsed_time = time.time() - start_time
        if interval_in_s - elapsed_time <= 0:
            logger.warning(
                f"One cycle took {elapsed_time}s, interval configured of {interval_in_s}s is likely too short. Consider increasing it."
            )
        else:
            logger.debug(f"Loop took {elapsed_time}s")
            await asyncio.sleep(interval_in_s - elapsed_time)


def register_target(target: str, target_alias: str) -> int:
    cur = db_conn.cursor()
    get_id_sql_query = "SELECT target_id FROM targets WHERE ip_or_url = %s"
    cur.execute(cur.mogrify(get_id_sql_query, [target]))
    res = cur.fetchone()
    if not res:
        targets_sql_query = ("INSERT INTO targets (ip_or_url, alias) VALUES (%s, %s) ON CONFLICT (ip_or_url) DO UPDATE SET alias = EXCLUDED.alias")
        full_query = cur.mogrify(targets_sql_query, [target, target_alias])

        cur.execute(full_query)
        cur.execute(get_id_sql_query, [target])
        res = cur.fetchone()
    return res[0]


def register_status_to_db(
    target_status: bool,
    rtt_min: Union[float, None],
    rtt_max: Union[float, None],
    rtt_avg: Union[float, None],
    target_id: int,
):
    cur = db_conn.cursor()
    # Insert ping status
    sql_status_query = (
        "INSERT INTO ping_results (timestamp, target_id, success) VALUES (%s, %s, %s)"
    )
    cur.execute(cur.mogrify(sql_status_query, [datetime.now(), target_id, target_status]))
    sql_stats_query = "INSERT INTO ping_stats (timestamp, target_id, rtt_min, rtt_max, rtt_avg) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(cur.mogrify(sql_stats_query, [datetime.now(), target_id, rtt_min, rtt_max, rtt_avg]))


def init_db():
    build_db_path = os.path.expanduser(config.database.build_sql_file_path)
    try:
        with open(build_db_path, "r") as file:
            sql_script = file.read()
        with db_conn.cursor() as cursor:
            cursor.execute(sql_script)
        logger.info(f"Executed build DB SQL script from {build_db_path} successfully")
    except FileNotFoundError as e:
        logger.exception(f"Error: SQL file not found: {e}")




if __name__ == "__main__":
    asyncio.run(main())
