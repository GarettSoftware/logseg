from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing import Queue

# Global variable is set in logger_init() of log package
logger_queue: Optional['Queue'] = None
