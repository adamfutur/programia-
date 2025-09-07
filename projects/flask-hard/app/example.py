from flask import Flask, request, jsonify
import threading
import queue

app = Flask(__name__)

class LogProcessor:
    def __init__(self):
        # Initialize queues for different log levels
        self.queues = {
            'info': queue.Queue(),
            'warning': queue.Queue(),
            'error': queue.Queue()
        }
        self.consumer_threads = []
        self._stop_event = threading.Event()
        self._start_consumer_threads()

    def _start_consumer_threads(self):
        # Start one consumer thread per queue
        for level, q in self.queues.items():
            t = threading.Thread(target=self._consume_logs, args=(level, q), daemon=True)
            t.start()
            self.consumer_threads.append(t)

    def _consume_logs(self, level, q):
        while not self._stop_event.is_set():
            try:
                log = q.get(timeout=1)
                # Process the log here (e.g., store, notify, etc.)
                # For demonstration, just print
                print(f"Consumed {level} log: {log}")
                q.task_done()
            except queue.Empty:
                continue

    def process_log(self, log):
        # Determine log level and enqueue
        level = log.get('level', 'info').lower()
        if level not in self.queues:
            level = 'info'
        self.queues[level].put(log)

    def stop(self):
        self._stop_event.set()
        for t in self.consumer_threads:
            t.join()

log_processor = LogProcessor()

@app.route('/logs', methods=['POST'])
def add_log():
    log_data = request.get_json()
    if not log_data:
        return jsonify({'error': 'Invalid log data'}), 400
    # Process the log
    log_processor.process_log(log_data)
    return jsonify({'message': 'Log added'}), 201

@app.route('/logs', methods=['GET'])
def get_logs():
    # Example: get logs filtered by level
    level = request.args.get('level')
    if level and level.lower() not in log_processor.queues:
        return jsonify({'error': 'Invalid log level filter'}), 400
    # For demonstration, just return a dummy response
    # Real implementation would fetch logs from storage
    return jsonify({'logs': [], 'filter': level}), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    # Dummy metrics endpoint
    return jsonify({'metrics': 'some metrics data'}), 200

if __name__ == '__main__':
    app.run(debug=True)
