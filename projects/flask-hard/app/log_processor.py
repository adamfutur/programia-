import threading
from queue import PriorityQueue
from app.notification import NotificationManager


class LogProcessor:
    def __init__(self):
        self.queues = {
            "CRITICAL": PriorityQueue(),
            "WARNING": PriorityQueue(),
            "INFO": PriorityQueue()
        }
        self.notification_manager = NotificationManager()

        # Start consumer threads for each log level
        self._start_consumers()

    def _start_consumers(self):
        # Start a separate thread for each queue to consume logs
        self.consumer_threads = []
        for level in self.queues:
            thread = threading.Thread(target=self._consume_queue, args=(level,), daemon=True)
            thread.start()

    def _consume_queue(self, level):
        """ Continuously consumes logs from the queue for the given log level. """
        # Write your code here
        pass

    def process_log(self, log_data):
        # Write your code here
        pass

    def get_logs(self, level=None):
        # Access all items in the queue without removing them

        # Write your code here
        pass
