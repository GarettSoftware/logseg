# LOGSEG

A Multiprocessing focused Python logger with easy-to-use log file segmentation for a better multiprocessing logging experience.

This logger is specifically designed to be compatible with Unix and Windows. It requires you to explicitly
pass a multiprocessing queue to each process that intends to use logging.

## Installation

https://pypi.org/project/logseg/

```bash
pip install logseg
```

## Usage

Prepend a `LOGEG(folder-name)` to your log messages to segregate your logs into different folders.
This is particularly useful when you have multiple processes writing logs simultaneously and you
want to make them easier to read.

Don't worry, all the logs will still be written to a root-level log file so that you can still
understand the order of events.

```python
from logseg import get_logger
logger = get_logger(__name__)

folder_name = 'log-folder-name'
logger.info(f'LOGSEG({folder_name}) Your message')
```

### Setup

Call logger_init() and keep the LoggerManager instance for the life of the program.

```python
from logseg import LoggerManager
from logseg import logger_init

logger_manager: LoggerManager = logger_init()
```

### Without Multiprocessing

```python
from logseg import get_logger

logger = get_logger(__name__)
logger.info('Your message')
```

### With Multiprocessing

```python
import logseg.globals
from logseg import get_logger

import multiprocessing as mp
from functools import partial

def my_function(queue, parameters):
    multiprocessing_logger = get_logger(__name__, queue=queue)
    multiprocessing_logger.info(f'testing logger in multiprocessing with parameters: {parameters}')

pool = mp.Pool(processes=mp.cpu_count())
pool.imap_unordered(func=partial(
    my_function,
    queue=logseg.globals.logger_queue,
    parameters='my parameters'
))

pool.close()
pool.join()
```

### Clean Up

Close the logger using the LoggerManager returned from logger_init() during setup.

```python
logger_manager.terminate_logger()
```

### Customization Options

You can customize the following settings with environment variables:

_Log Directory_

The directory to store the log files.

`LOGSEG_LOG_DIR = logs`

_Max Bytes_

How many bytes to allow in a single log file before creating a new one.

`LOGSEG_MAX_BYTES = 10000000`

_Backup Count_

How many log files to keep before deleting the oldest.

`LOGSEG_BACKUP_COUNT = 6`

_Pre Purge_

Whether to purge the log directory on startup.

`LOGSEG_PRE_PURGE = true`