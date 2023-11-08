import os
import time
import datetime

import logseg.globals

from threading import Thread

from functools import partial

from unittest import TestCase

import multiprocessing as mp
from multiprocessing import Queue

from logseg.log_setup import get_logger, logger_init

from tests.test_utils import common_test_setup, common_test_setup_w_logger, common_test_teardown_w_logger


os.environ['LOGSEG_LOG_DIR'] = 'tests/data/logs'


class TestLogger(TestCase):
    """
    This class is responsible for testing the logger for concurrency issues.
    """

    def tearDown(self) -> None:
        common_test_teardown_w_logger(logger_manager=self.logger_manager)

    def test_multiprocessing_logger_and_redirects(self):
        self.logger_manager = common_test_setup_w_logger()

        sequential_logger = get_logger(__name__)
        sequential_logger.info(f'Starting thread...')

        _multiprocessing_logger_and_redirects_helper(sequential_logger)

        # Run assertions on log files.
        with open('tests/data/logs/thread_1/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 11, f"Only 11 logs should be in thread_1 log file. Found {content_len}.\n{content}"
        with open('tests/data/logs/thread_2/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 11, f"Only ll logs should be in thread_2 log file. Found {content_len}.\n{content}"
        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 53, f"Only 53 logs should be in log file. Found {content_len}.\n{content}"

    def test_multiprocessing_logger_file_rotation(self):
        common_test_setup()

        # Use custom configurations for this test.
        os.environ['LOGSEG_MAX_BYTES'] = '100'
        os.environ['LOGSEG_BACKUP_COUNT'] = '2'
        os.environ['LOGSEG_PRE_PURGE'] = 'true'

        self.logger_manager = logger_init()

        _multiprocessing_logger_file_rotation_helper()

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 1, f"Only one log should be in log file. Found {content_len}.\n{content}"
        with open('tests/data/logs/logs.log.1', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 1, f'Only one log should be in log file. Found {content_len}.\n{content}'


# ---- test_multiprocessing_logger_and_redirects helpers ---- #

def _multiprocessing_logger_and_redirects_helper(sequential_logger):
    iterable = [i for i in range(10)]

    for i in iterable:
        sequential_logger.info(f'sequential logger: {i}')

    # Start up new threads for the two inbound queues.
    t1 = Thread(target=_multiprocessing_logger_and_redirects_threading_helper,
                args=(1, iterable),
                daemon=False)
    t2 = Thread(target=_multiprocessing_logger_and_redirects_threading_helper,
                args=(2, iterable),
                daemon=False)
    t1.start()
    t2.start()

    # Join threads back to main thread.
    t1.join()
    t2.join()


def _multiprocessing_logger_and_redirects_threading_helper(thread_num: int, iterable: list):
    thread_logger = get_logger(f'{__name__}_{thread_num}')

    thread_logger.info(f'LOGSEG(thread_{thread_num})Thread {thread_num} started')
    pool = mp.Pool(processes=mp.cpu_count())
    pool.map(func=partial(_multiprocessing_logger_and_redirects_multiprocessing_helper,
                          thread_num=thread_num,
                          logger_queue=logseg.globals.logger_queue),
             iterable=iterable)
    pool.close()
    pool.join()


def _multiprocessing_logger_and_redirects_multiprocessing_helper(i: int, thread_num: int, logger_queue: Queue):
    multiprocessing_logger = get_logger(name=__name__, queue=logger_queue)
    multiprocessing_logger.info(f'Thread: {thread_num}, Multiprocessing logger: {i}')

    # Print to sys.stdout to check if logger redirect is working.
    print(f'LOGSEG(thread_{thread_num})Thread: {thread_num}, Multiprocessing sys.stdout logger: {i}')


# ---- multiprocessing_logger_file_rotation helpers ---- #

def _multiprocessing_logger_file_rotation_helper():
    # Create a list of times to print so that processes attempt to print at exact same time.
    current_time = datetime.datetime.now()
    print_time = current_time + datetime.timedelta(seconds=5)

    processes = []
    for i in range(2):
        processes.append(mp.Process(target=partial(_multiprocessing_logger_file_rotation_process_helper,
                                                   process_num=i,
                                                   print_time=print_time,
                                                   logger_queue=logseg.globals.logger_queue)))
    # Start the processes.
    for process in processes:
        process.start()
    # Join processes back to main thread
    for process in processes:
        process.join()
    # Close the processes.
    for process in processes:
        process.close()


def _multiprocessing_logger_file_rotation_process_helper(
        process_num: int,
        print_time: datetime.datetime,
        logger_queue: Queue
):
    multiprocessing_logger = get_logger(name=__name__, queue=logger_queue)

    # Wait until the print time arrives.
    while datetime.datetime.now() < print_time:
        pass

    # Print now that the processes are in sync.
    multiprocessing_logger.info(f'Process: {process_num} printing at {datetime.datetime.now()}')
