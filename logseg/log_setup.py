import re
import sys
import time
import logging

import logseg.globals

import logging.handlers

from threading import Thread

from typing import Optional, Tuple

from logging import Logger, Formatter

from configparser import ConfigParser

from logseg.configurations.config import get_config

from multiprocessing import Queue, Manager, current_process

from logseg.utils import create_dir_if_not_exists, delete_dir_contents_if_exists


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

        self.segregate_regex = re.compile('(LOGSEG\(.*?\))')
        self.seg_name_regex = re.compile('(?<=\()(.*)(?=\))')

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

            # Handle message property
            if hasattr(record, 'message'):
                record.message, name = self._process_logseg(record.message)
                segregate_folder_name = name if name else segregate_folder_name

            # Handle msg property
            if hasattr(record, 'msg'):
                record.msg, name = self._process_logseg(record.msg)
                segregate_folder_name = name if name else segregate_folder_name

            if segregate_folder_name:
                logger = logging.getLogger(segregate_folder_name)
                # Don't propagate to the root logger, this would cause infinite recursion.
                logger.propagate = False
                # Add a file handler to the logger instance for the segregate folder.
                _add_file_handler(config=self.config, instance=logger, log_formatter=_get_log_formatter(),
                                  folder_name=segregate_folder_name)
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
        base_log_path = config.get('Logger', 'log_dir')
        if folder_name:
            log_path = f'{base_log_path}/{folder_name}'
        else:
            log_path = base_log_path
        create_dir_if_not_exists(log_path)

        # Define the file handler.
        file_handler = logging.handlers.RotatingFileHandler(f"{log_path}/logs.log",
                                                            maxBytes=config.getint('Logger', 'max_bytes'),
                                                            backupCount=config.getint('Logger', 'backup_count'))
        file_handler.set_name(folder_name)

        # Add the file handler.
        file_handler.setFormatter(log_formatter)
        instance.addHandler(file_handler)


def _get_log_formatter():
    """
    This function gets the log formatter.

    Returns:

    """
    # Define the formatter.
    formatter = logging.Formatter("%(asctime)s: %(levelname)7s > %(message)s")
    formatter.converter = time.gmtime
    return formatter


def _get_root_logger():
    """
    This function gets the root logger and sets its level.

    Returns:

    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
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

    # Get the root logger.
    root = _get_root_logger()

    # Define the formatter.
    log_formatter = _get_log_formatter()

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
        queue: A multiprocessing Queue, managed my a multiprocessing Manager.

    Returns:

    """
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def logger_init() -> LoggerManager:
    """
    This function initializes a logger as well as a thread to process logs produced by concurrent processes. Logs
    from concurrent processes should be passed through the multiprocessing queue stored in log.globals.logger_queue.

    Returns:
        A LoggerManager instance which can be used to terminate the logger thread at cleanup time.

    """
    config = get_config()

    logger_dir = config.get('Logger', 'log_dir')

    # Delete the directory contents if the config specifies to do so.
    if config.getboolean('Logger', 'pre_purge'):
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

    Usage:
    1) Call logger_init() and keep the LoggerManager for the life of the program.
    2) Import get_logger(__name__) wherever you want to use the logger.
    3) Use the logger, logger.info('your message')

    4) When using multiprocessing...

        import log.globals
        Pass log.globals.logger_queue as a parameter to the multiprocessing function explicitly
        (needed due to process spawning on Windows OS).

        e.g.
        pool = mp.Pool(processes=mp.cpu_count())
        pool.imap_unordered(func=partial(
            my_function,
            queue=log.globals.logger_queue,
            parameters=parameters
        ))
        pool.close()
        pool.join()

        Set up a logger instance from within the function that multiprocessing is being applied to. It will communicate
        with the root logger using the queue.

        e.g.
        def my_function(queue, parameters):
            multiprocessing_logger = get_logger(__name__, queue=queue)
            multiprocessing_logger.info('testing logger in multiprocessing')

    5) When you are finished logging, close the logger using the LoggerManager returned from logger_init() (step 1)

        e.g.
        logger_manager.terminate_logger()

    Args:
        name: The name for the logger.
        queue: A Queue instance generated by logger_init(), held in the variable log.globals.logger_queue

    Returns:

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
