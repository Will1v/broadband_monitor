import logging
import os
from datetime import datetime
from broadband_monitor.config import config

logs_dir = "/var/log/broadband_monitor"


def configure_logger():
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Define the logging format
    log_format = "%(asctime)s [%(levelname)s] - %(message)s - %(filename)s:%(lineno)d"
    log_file_timestamp = datetime.now().strftime("%Y%m%d")
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(
                f"{logs_dir}/broadband_monitor-{os.getpid()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log",
                mode="w",
            ),  # Log to a file
            logging.StreamHandler(),  # Log to console
        ],
    )


# Configure the logger when the module is imported
configure_logger()


def get_logger(name: str = None):
    return logging.getLogger(name)
