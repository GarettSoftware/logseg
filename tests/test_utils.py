import os
import stat
import shutil
import logging

from importlib import reload

from logseg.utils import create_dir_if_not_exists

from logseg.log_setup import LoggerManager, logger_init


def common_test_setup():
    # Create a test log directory
    create_dir_if_not_exists('tests/data')


def common_test_teardown():
    # Change folder permissions and delete the directory.
    os.chmod('tests/data', stat.S_IWUSR)
    shutil.rmtree('tests/data')


def common_test_setup_w_logger() -> LoggerManager:
    logger_manager: LoggerManager = logger_init()
    return logger_manager


def common_test_teardown_w_logger(logger_manager: LoggerManager):
    # Terminate the logger.
    logger_manager.terminate_logger()
    # Reload the logger
    reload(logging)

    common_test_teardown()
