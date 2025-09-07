import threading

class ConsumerThread(threading.Thread):
    def __init__(self, level, queue, log_processor, stop_event):
        super().__init__(daemon=True)
        self.level = level
        self.queue = queue
        self.log_processor = log_processor
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            try:
                log_entry = self.queue.get(timeout=1)
                self.log_processor.process_log(log_entry)
                self.queue.task_done()
            except Exception:
                continue

    def stop(self):
        self.stop_event.set()
