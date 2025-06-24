import os
from helpers.logging import setup_logging
from dotenv import load_dotenv

load_dotenv()


def get_log_file(default: str, env_var: str = "LOG_FILE") -> str:
    """
    Get the log file path from the environment variable
    `LOG_FILE`, or the default path.

    :param default: The default log file path.
    :return: The log file path.
    """
    log_file = os.getenv(env_var) or os.path.join(os.path.dirname(__file__), default)
    log_file = os.path.abspath(log_file)
    return log_file


# setup_logging(get_log_file("logs/ek_global.log"))


__author__ = "Daniel T. Afolayan (ti-oluwa@github)"
