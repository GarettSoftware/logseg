import re
import sys
import logging

import logging.handlers

from pathlib import Path

from threading import Thread

from datetime import datetime

from zoneinfo import ZoneInfo

from logging import Logger, Formatter

from configparser import ConfigParser

from typing import Optional, Tuple, Union

from logseg.configurations.config import get_config

from multiprocessing import Manager, current_process
from multiprocessing.queues import Queue

from logseg.utils import create_dir_if_not_exists, delete_dir_contents_if_exists

import logseg.globals


class LoggerManager:

    def __init__(self, logger_thread: Thread):
        """
        This class manages the logger thread.

        Args:
            logger_thread: The logger thread to manage.

        Returns:

        """
        self.logger_thread = logger_thread

    def terminate_logger(self):
        """
        This method terminates the logger thread. It should be called when log is complete during program cleanup.

        Returns:

        """
        # Trigger the logger thread to stop processing from the queue.
        logseg.globals.logger_queue.put(None)
        # Join the thread back to the main thread.
        self.logger_thread.join()

        # Shut down the handlers
        root = logging.getLogger()
        for handler in root.handlers:
            handler.close()
            root.removeHandler(handler)

        # Shutdown logging
        logging.shutdown()


class RedirectToLogger(object):

    def __init__(self, logger, log_level=logging.INFO):
        """
        Used to redirect stdout and stderr to logger in _redirect_stdout_stderr

        Args:
            logger: The logger instance to redirect to.
            log_level: The log level to use for the logger.

        Returns:

        """
        self.logger = logger
        self.log_level = log_level
        self.value = None

    def write(self, message):
        """
        This method writes a message to the logger instance.

        Args:
            message: The message to write to the logger instance.

        Returns:

        """
        self.value = message
        for line in message.rstrip().splitlines():
            line = line.encode('utf-8', errors='replace')
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

    def getvalue(self):
        return self.value


class CreateFileHandlerHandler(logging.Handler):

    def __init__(self, config: ConfigParser):
        """
        This class creates a file handler for a logger instance.

        Args:
            config: A ConfigParser containing the logger configuration.

        Returns:

        """
        super().__init__()
        self.config = config

        self.segregate_regex = re.compile(r'(LOGSEG\(.*?\))')
        self.seg_name_regex = re.compile(r'(?<=\()(.*)(?=\))')

    def _process_logseg(self, log_str: str) -> Tuple[str, str]:
        """
        This method processes a logseg log record.

        Args:
            log_str: The log string to be processed.

        Returns:
            A Tuple containing the final message and the segregate folder name for the log string.

        """
        segregate_folder_name = None
        if re.findall(self.segregate_regex, log_str):
            # Determine the segregate folder name defined in the log string.
            segregate_folder_name = re.findall(
                self.seg_name_regex,
                re.findall(self.segregate_regex, log_str)[0])[0]
            # Rewrite the log message to not include the segregation tag.
            final_message = re.sub(self.segregate_regex, '', log_str)
        else:
            final_message = log_str
        return final_message, segregate_folder_name

    def emit(self, record):
        """
        This method emits a log record to the logger instance.

        Args:
            record: The log record to emit.

        Returns:

        """
        try:
            # Handle logging to separate file, if requested:
            segregate_folder_name = None

            '''
            Note that for the two cases below, we check if the record is a string because it could be an exception 
            instance. If it is an exception, we know it doesn't contain a LOGSEG() substring.
            '''

            # Handle message property
            if hasattr(record, 'message') and isinstance(record.message, str):
                record.message, name = self._process_logseg(record.message)
                segregate_folder_name = name if name else segregate_folder_name
            # Handle msg property
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                record.msg, name = self._process_logseg(record.msg)
                segregate_folder_name = name if name else segregate_folder_name

            if segregate_folder_name:
                logger = logging.getLogger(segregate_folder_name)
                # Don't propagate to the root logger, this would cause infinite recursion.
                logger.propagate = False
                # Add a file handler to the logger instance for the segregate folder.
                _add_file_handler(
                    config=self.config,
                    instance=logger,
                    log_formatter=_get_log_formatter(self.config),
                    folder_name=segregate_folder_name
                )
                logger.handle(record)
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)


def _add_file_handler(
        config: ConfigParser,
        instance: Logger,
        log_formatter: Formatter,
        folder_name: Optional[str] = None
) -> None:
    """
    This function adds a file handler to a logger instance.

    Args:
        config: A ConfigParser containing the logger configuration.
        instance: The logger instance to add the file handler to.
        log_formatter: The log formatter to use for the file handler.
        folder_name: The name of the folder to segregate logs into.

    Returns:

    """
    # If the file handler doesn't already exist, create it.
    if not folder_name or folder_name and folder_name not in [x.name for x in instance.handlers]:
        # Create the directory for the logs if necessary.
        base_log_path = config.get('LOGSEG', 'log_dir')
        if folder_name:
            log_path = f'{base_log_path}/{folder_name}'
        else:
            log_path = base_log_path
        create_dir_if_not_exists(log_path)

        # Define the file handler.
        file_handler = logging.handlers.RotatingFileHandler(
            f"{log_path}/logs.log",
            maxBytes=config.getint('LOGSEG', 'max_bytes'),
            backupCount=config.getint('LOGSEG', 'backup_count')
        )
        file_handler.set_name(folder_name)

        # Add the file handler.
        file_handler.setFormatter(log_formatter)
        instance.addHandler(file_handler)


def _get_log_formatter(config: ConfigParser):
    """
    This function gets the log formatter with timezone support.

    Args:
        config: A ConfigParser containing the logger configuration.

    Returns:
        A logging.Formatter instance with timezone support.
    """

    timezone = config.get('LOGSEG', 'timezone')

    class TZFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, tz=None):
            super().__init__(fmt, datefmt)
            self.tz = ZoneInfo(tz)

        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, self.tz)
            if datefmt:
                s = dt.strftime(datefmt)
            else:
                s = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            return s

    formatter = TZFormatter("%(asctime)s: %(levelname)7s > %(message)s", tz=timezone)
    return formatter


def _get_root_logger(config: ConfigParser = None):
    """
    This function gets the root logger and sets its level based on configuration.

    Args:
        config: A ConfigParser containing the logger configuration. If None, the default config will be used.

    Returns:
        The root logger with the configured log level.
    """
    root = logging.getLogger()

    # If config is not provided, get the default config
    if config is None:
        config = get_config()

    # Get log level from config, default to INFO if not specified or invalid
    log_level_str = config.get('LOGSEG', 'log_level', fallback='INFO').upper()

    # Map string log level to logging module constants
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    # Set log level from config, default to INFO if not a valid level
    log_level = log_level_map.get(log_level_str, logging.INFO)
    root.setLevel(log_level)

    return root


def _redirect_stdout_stderr(logger: Logger) -> None:
    """
    This function redirects the standard out and standard error to logger instances.

    Args:
        logger: The logger instance to redirect stdout and stderr to.

    Returns:

    """
    # Redirect stdout to the logger instance
    stdout_logger = RedirectToLogger(logger, logging.INFO)
    sys.stdout = stdout_logger

    # Redirect stderr to the logger instance
    stderr_logger = RedirectToLogger(logger, logging.WARNING)
    sys.stderr = stderr_logger


def _configure_logging_handlers(config: ConfigParser) -> Logger:
    """
    This function configures the logging handlers for the logger instance.

    Args:
        config: A ConfigParser containing the logger configuration.

    Returns:
        A Logger instance.

    """

    # Get the root logger with the configured log level.
    root = _get_root_logger(config)

    # Define the formatter.
    log_formatter = _get_log_formatter(config)

    # Add the file handler
    _add_file_handler(config, root, log_formatter)

    # Create the handler that creates more file handlers.
    file_handler_handler = CreateFileHandlerHandler(config=config)
    root.addHandler(file_handler_handler)

    # Define the stream handler for outputting to the console.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_formatter)
    root.addHandler(stdout_handler)

    # Redirect stdout and stderr to the root logger instance.
    _redirect_stdout_stderr(root)

    return root


def _lt(queue: Queue):
    """
    This function acts as the thread that listens to the logger queue and sends queued logs to the logger instance.

    Args:
        queue: A multiprocessing Queue, managed by a multiprocessing Manager.

    Returns:

    """
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def logger_init(config_file: Union[Path, str] = None) -> LoggerManager:
    """
    This function initializes a logger as well as a thread to process logs produced by concurrent processes. Logs
    from concurrent processes should be passed through the multiprocessing queue stored in log.globals.logger_queue.

    Args:
        config_file: A path to a configuration file containing a LOGSEG section. If not provided, the default
        configuration will be used. See the documentation for an example configuration file.

    Returns:
        A LoggerManager instance which can be used to terminate the logger thread at cleanup time.

    """
    config = get_config(config_file=config_file)

    logger_dir = config.get('LOGSEG', 'log_dir')

    # Delete the directory contents if the config specifies to do so.
    if config.getboolean('LOGSEG', 'pre_purge'):
        # Note that we don't delete the directory itself since it might be volume mounted (for argo workflows).
        delete_dir_contents_if_exists(logger_dir)

    create_dir_if_not_exists(logger_dir)

    logseg.globals.logger_queue = Manager().Queue()

    _configure_logging_handlers(config)

    logger_thread = Thread(target=_lt, args=(logseg.globals.logger_queue,))
    logger_thread.start()

    return LoggerManager(logger_thread=logger_thread)


def get_logger(name: str, queue: Optional[Queue] = None) -> Logger:
    """
    This function gets a logger instance.

    Setup ::

        from logseg import LoggerManager
        from logseg import logger_init

        logger_manager: LoggerManager = logger_init()

    Without multiprocessing ::

        from logseg import get_logger

        logger = get_logger(__name__)
        logger.info('your message')

    With multiprocessing ::

        import multiprocessing as mp
        import log.globals

        def my_function(queue: mp.Queue, parameter: str):
            logger = get_logger(__name__, queue)
            logger.info(f'Your message: {parameter}')

        pool = mp.Pool(processes=mp.cpu_count())
        pool.imap_unordered(func=partial(
            my_function,
            queue=log.globals.logger_queue,
            parameter='example'
        ))
        pool.close()
        pool.join()

    Shutdown ::

        logger_manager.terminate_logger()

    Args:
        name: The name for the logger.
        queue: A Queue instance generated by logger_init(), held in the variable log.globals.logger_queue

    Returns:
        A logseg logger instance.

    """
    logger = logging.getLogger(name=name)

    if current_process().name != 'MainProcess' and not queue:
        '''
        Don't create the logger, state reached may be due to Windows process spawning (imports may be re-evaluated
        upon spawn of a new process).
        '''
        pass
    elif queue is not None and current_process().name != 'MainProcess':
        # Set up the queue handler for the logger instance.
        queue_handler = logging.handlers.QueueHandler(queue)
        queue_handler.set_name(name=current_process().pid.__str__())

        # Get the root logger instance.
        root = _get_root_logger()

        # Redirect stdout of this process to the logger instance
        _redirect_stdout_stderr(logger)

        # Clean up existing handlers on the root logger if they exist.
        for handler in root.handlers:
            handler.close()
            root.removeHandler(handler)

        # Add the handler if it doesn't already exist.
        if queue_handler.name not in [x.name for x in root.handlers]:
            # Add the queue handler.
            root.addHandler(queue_handler)

    return logger
