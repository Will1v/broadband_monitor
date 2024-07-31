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
from typing import Tuple, Union, List


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

class Target:
    def __init__(self, ip:str , alias: str):
        self.ip = ip
        self.alias = alias
        self.ok_counter = 0
        self.nok_counter = 0
        self.db_id = None
        self.ping_status = None


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

    targets: List[Target] = []
    targets.append(Target(config.router_ip, config.router_alias))
    targets.append(Target(config.internet_address, config.internet_alias))
    targets.append(Target(config.client_ip, config.client_alias))
    # Add as many targets as necessary
    # Init DB
    conn = init_db()

    for target in targets:
        target.db_id = register_target(target.ip, target.alias)

    while True:
        start_time = time.time()
        ping_statuses = await asyncio.gather(
            *[ping_host(target.ip) for target in targets]
        )

        for i in range(len(targets)):
            targets[i].ping_status = ping_statuses[i]
        for target in targets:
            successful_ping = False
            if target.ping_status:
                successful_ping = True
                target.ok_counter += 1
                rtt_min, rtt_avg, rtt_max = target.ping_status
            else:
                target.nok_counter += 1
            register_status_to_db(
                target_status=successful_ping,
                rtt_min=rtt_min,
                rtt_max=rtt_max,
                rtt_avg=rtt_avg,
                target_id=target.db_id
            )
        counter += 1
        if (counter - 1) % counter_modulo == 0:
            logger.info(
                f"{counter} pings run." + " | ".join([f"{target.ip}: {target.ok_counter / counter * 100.0:.2f}% success (OK: {target.ok_counter} / KO: {target.nok_counter})" for target in targets])
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
