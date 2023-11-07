from multiprocessing import Queue

from typing import Optional

# Global variable is set in logger_init() of log package
logger_queue: Optional[Queue] = None
