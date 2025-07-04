# LOGSEG

![](https://github.com/GarettSoftware/logseg/actions/workflows/ci.yml/badge.svg)

A Multiprocessing capable Python logger with easy per-log file segmentation.

```python
from logseg import get_logger, logger_init

logger_manager = logger_init()
logger = get_logger(__name__)

logger.info(f'LOGSEG(folder_name) My log')

logger_manager.terminate_logger()
```

This logger is specifically designed to be compatible with Unix and Windows.

For full setup and configuration instructions, see below or read the 
[documentation](https://logseg.readthedocs.io/en/latest/).

## Installation

[PyPi](https://pypi.org/project/logseg/)

```bash
pip install logseg
```

## Usage

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

### Log Segregation

Prepend a `LOGEG(folder-name)` if you want to segregate your logs into different folders.
This is particularly useful when you have multiple processes writing logs simultaneously, and you
want to make them easier to read.

Don't worry, all the logs will still be written to a root-level log file so that you can still
understand the order of events.

```python
from logseg import get_logger
logger = get_logger(__name__)

logger.info(f'LOGSEG(folder-name) My log')
```

### Clean Up

Close the logger using the LoggerManager returned from logger_init() during setup.

```python
logger_manager.terminate_logger()
```

### Customization Options

You can customize the logger in two different ways.

#### Config File

You can pass `logger_init()` a path to a config file.

```python
from logseg import LoggerManager
from logseg import logger_init

logger_manager: LoggerManager = logger_init(config_file='path/to/my_configuration.config')
```

The config file should be a `.config` file. Here is a complete example:

```config
[LOGSEG]
log_dir = logs
max_bytes = 10000000
backup_count = 6
pre_purge = true
timezone = UTC
log_level = INFO
```

#### Environment Variable Overrides

You can override the default config or your custom config on a per-environment basis with the following
environment variables.

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

_Time Zone_

The timezone to use for the logger.

`LOGSEG_TIMEZONE = UTC`

_Log Level_

The log level to use for the logger.

One of:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

`LOGSEG_LOG_LEVEL = INFO`
