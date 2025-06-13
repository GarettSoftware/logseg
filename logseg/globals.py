from typing import Optional
from multiprocessing import Queue

# Global variable is set in logger_init() of log package
logger_queue: Optional[Queue] = None
