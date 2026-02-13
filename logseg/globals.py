from typing import Optional
from multiprocessing import Queue
from multiprocessing.managers import SyncManager

# Global variables are set in logger_init() of log package
logger_queue: Optional[Queue] = None
logger_manager: Optional[SyncManager] = None
