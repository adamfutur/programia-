import threading

class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.metrics_data = {"logs_processed": 0, "notifications_sent": 0}

    def increment(self, metric):
        with self._lock:
            if metric in self.metrics_data:
                self.metrics_data[metric] += 1

    def get_all_metrics(self):
        with self._lock:
            return dict(self.metrics_data)
