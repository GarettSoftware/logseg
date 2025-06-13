import os
import time
import datetime
import tracemalloc

import logseg.globals

from threading import Thread

from functools import partial

from unittest import TestCase

import multiprocessing as mp
from multiprocessing import Queue

from zoneinfo import ZoneInfo

from logseg.log_setup import get_logger, logger_init

from tests.test_utils import common_test_setup, common_test_setup_w_logger, common_test_teardown_w_logger

os.environ['LOGSEG_LOG_DIR'] = 'tests/data/logs'


class TestLogger(TestCase):
    """
    This class is responsible for testing the logger for concurrency issues.
    """

    def tearDown(self) -> None:
        # First clean up the logger to ensure all logs are written
        common_test_teardown_w_logger(logger_manager=self.logger_manager)

        # Then reset any environment variables that might affect other tests
        env_vars_to_reset = [
            'LOGSEG_LOG_LEVEL',
            'LOGSEG_MAX_BYTES',
            'LOGSEG_BACKUP_COUNT',
            'LOGSEG_PRE_PURGE',
            'LOGSEG_TIMEZONE'
        ]
        for var in env_vars_to_reset:
            if var in os.environ:
                del os.environ[var]

        # Reset LOGSEG_LOG_DIR to its original value
        os.environ['LOGSEG_LOG_DIR'] = 'tests/data/logs'

    def test_logger(self):
        self.logger_manager = common_test_setup_w_logger()

        logger = get_logger(__name__)

        logger.info('test log')

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 1, f"Only 1 log should be in log file. Found {content_len}.\n{content}"
            assert 'INFO > test log\n' in content[0], f"Log content is not as expected.\n{content}"

    def test_logger_exception(self):
        self.logger_manager = common_test_setup_w_logger()

        logger = get_logger(__name__)

        try:
            raise Exception('Test exception')
        except Exception as e:
            logger.exception(e)

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 5, f"Only 5 logs should be in log file. Found {content_len}.\n{content}"
            assert 'ERROR > Test exception\n' in content[0], f"Log content is not as expected.\n{content}"

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

    def test_memory_usage_doesnt_explode(self):
        """
        This test ensures that repeatedly logging messages does not cause
        a runaway increase in Python memory allocations.
        """
        self.logger_manager = common_test_setup_w_logger()
        logger = get_logger(__name__)

        # Start tracking memory allocations.
        tracemalloc.start()
        initial_current, _ = tracemalloc.get_traced_memory()

        num_logs = 100000
        check_interval = 10000  # Check memory usage every 10,000 logs
        allowed_increase = 10 * 1024 * 1024  # 10 MB in bytes

        for i in range(num_logs):
            logger.info(f"Memory usage test log: {i}")
            if i % check_interval == 0 and i != 0:
                current_memory, _ = tracemalloc.get_traced_memory()
                memory_increase = current_memory - initial_current
                self.assertTrue(
                    memory_increase < allowed_increase,
                    f"Memory usage increased by {memory_increase} bytes after {i} logs, which exceeds the allowed threshold."
                )

        # Allow time for asynchronous logging to complete.
        time.sleep(1)

        final_current, _ = tracemalloc.get_traced_memory()
        total_memory_increase = final_current - initial_current

        self.assertTrue(
            total_memory_increase < allowed_increase,
            f"Total memory usage increased by {total_memory_increase} bytes, which exceeds the allowed threshold."
        )
        tracemalloc.stop()

    def test_custom_timezone_log(self):
        common_test_setup()

        os.environ['LOGSEG_TIMEZONE'] = 'America/New_York'

        self.logger_manager = logger_init()

        logger = get_logger(__name__)

        # Log the current time
        current_time = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f'test log at {current_time}')

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()
            content_len = len(content)
            assert content_len == 1, f"Only 1 log should be in log file. Found {content_len}.\n{content}"

            log_entry = content[0]
            assert 'INFO > test log' in log_entry, f"Log content is not as expected.\n{content}"

            # Extract the timestamp from the log entry
            log_time_str = log_entry.split('INFO > test log at ')[0].strip().removesuffix(":")
            log_time = datetime.datetime.fromisoformat(log_time_str).__str__()

            # Convert the log time to the expected timezone
            expected_time = current_time.astimezone(
                ZoneInfo('America/New_York')
            ).strftime('%Y-%m-%d %H:%M:%S.%f')  # Use ZoneInfo to handle DST correctly

            # Note we ignore the last 4 digits to account for rounding differences
            assert log_time[:-4] == expected_time[:-4], \
                f"Log time {log_time} does not match expected time {expected_time}."

    def test_log_level_from_env_debug(self):
        """
        Test that the LOGSEG_LOG_LEVEL environment variable is used to set the log level to DEBUG.
        """
        common_test_setup()

        # Set log level to DEBUG via environment variable
        os.environ['LOGSEG_LOG_LEVEL'] = 'DEBUG'

        self.logger_manager = logger_init()

        logger = get_logger(__name__)

        # Log messages at different levels
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()

            # Check that all log levels are present (DEBUG and above)
            assert any('DEBUG > debug message' in line for line in content), "DEBUG message not found in logs"
            assert any('INFO > info message' in line for line in content), "INFO message not found in logs"
            assert any('WARNING > warning message' in line for line in content), "WARNING message not found in logs"
            assert any('ERROR > error message' in line for line in content), "ERROR message not found in logs"

    def test_log_level_from_env_warning(self):
        """
        Test that the LOGSEG_LOG_LEVEL environment variable is used to set the log level to WARNING.
        """
        common_test_setup()

        # Set log level to WARNING via environment variable
        os.environ['LOGSEG_LOG_LEVEL'] = 'WARNING'

        self.logger_manager = logger_init()

        logger = get_logger(__name__)

        # Log messages at different levels
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')

        time.sleep(1)

        with open('tests/data/logs/logs.log', 'r') as f:
            content = f.readlines()

            # Check that only WARNING and above are present
            debug_messages = [line for line in content if 'DEBUG > debug message' in line]
            info_messages = [line for line in content if 'INFO > info message' in line]
            warning_messages = [line for line in content if 'WARNING > warning message' in line]
            error_messages = [line for line in content if 'ERROR > error message' in line]

            assert len(debug_messages) == 0, "DEBUG message should not be in logs when level is WARNING"
            assert len(info_messages) == 0, "INFO message should not be in logs when level is WARNING"
            assert len(warning_messages) == 1, "WARNING message should be in logs when level is WARNING"
            assert len(error_messages) == 1, "ERROR message should be in logs when level is WARNING"


# ---- test_multiprocessing_logger_and_redirects helpers ---- #

def _multiprocessing_logger_and_redirects_helper(sequential_logger):
    iterable = [i for i in range(10)]

    for i in iterable:
        sequential_logger.info(f'sequential logger: {i}')

    # Start up new threads for the two inbound queues.
    t1 = Thread(
        target=_multiprocessing_logger_and_redirects_threading_helper,
        args=(1, iterable),
        daemon=False
    )
    t2 = Thread(
        target=_multiprocessing_logger_and_redirects_threading_helper,
        args=(2, iterable),
        daemon=False
    )
    t1.start()
    t2.start()

    # Join threads back to main thread.
    t1.join()
    t2.join()


def _multiprocessing_logger_and_redirects_threading_helper(thread_num: int, iterable: list):
    thread_logger = get_logger(f'{__name__}_{thread_num}')

    thread_logger.info(f'LOGSEG(thread_{thread_num})Thread {thread_num} started')

    pool = mp.Pool(processes=mp.cpu_count())
    pool.map(
        func=partial(
            _multiprocessing_logger_and_redirects_multiprocessing_helper,
            thread_num=thread_num,
            logger_queue=logseg.globals.logger_queue
        ),
        iterable=iterable
    )
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
        processes.append(mp.Process(
            target=partial(
                _multiprocessing_logger_file_rotation_process_helper,
                process_num=i,
                print_time=print_time,
                logger_queue=logseg.globals.logger_queue
            )
        ))
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
