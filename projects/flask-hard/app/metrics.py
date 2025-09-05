class Metrics:
    def __init__(self):
        self.metrics_data = {"logs_processed": 0, "notifications_sent": 0}

    def increment(self, metric):
        if metric in self.metrics_data:
            self.metrics_data[metric] += 1

    def get_all_metrics(self):
        return self.metrics_data
