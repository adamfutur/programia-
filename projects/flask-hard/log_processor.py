import threading
import queue
import time
from collections import defaultdict
from notifications import NotificationManager

class LogProcessor:
    def __init__(self):
        # Queue for incoming logs
        self.log_queue = queue.Queue()

        # Storage for logs (in-memory list for simplicity)
        self.logs = []
        self.logs_lock = threading.Lock()

        # Metrics
        self.metrics = {
            'total_logs_processed': 0,
            'notifications_sent': 0
        }
        self.metrics_lock = threading.Lock()

        # Notification manager handles cooldowns and sending
        self.notification_manager = NotificationManager()

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consume_logs, daemon=True)
        self.consumer_thread.start()

    def enqueue_log(self, log_entry):
        self.log_queue.put(log_entry)

    def _consume_logs(self):
        while True:
            try:
                log_entry = self.log_queue.get()
                self.process_log(log_entry)
                self.log_queue.task_done()
            except Exception as e:
                # Log the exception or handle it
                print(f"Error processing log: {e}")

    def process_log(self, log_entry):
        # Store the log
        with self.logs_lock:
            self.logs.append(log_entry)

        # Update metrics
        with self.metrics_lock:
            self.metrics['total_logs_processed'] += 1

        # Check if notification needed
        level = log_entry.get('level', '').upper()
        if level in ['ERROR', 'CRITICAL']:
            notified = self.notification_manager.send_notification(log_entry)
            if notified:
                with self.metrics_lock:
                    self.metrics['notifications_sent'] += 1

    def get_logs(self, level_filter=None):
        with self.logs_lock:
            if level_filter:
                filtered = [log for log in self.logs if log.get('level') == level_filter]
                return filtered
            else:
                return list(self.logs)

    def get_metrics(self):
        with self.metrics_lock:
            return dict(self.metrics)
