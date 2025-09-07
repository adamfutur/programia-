import threading
from datetime import datetime

# Thread-safe storage
_logs_lock = threading.Lock()
_logs = []  # Stored logs
_processed_logs = []  # Logs processed by consumers

# Metrics
_total_logs_processed = 0

ALLOWED_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}


def validate_log_data(log):
    # Required fields: timestamp, level, message
    if not isinstance(log, dict):
        return False, "Log data must be a JSON object"
    for field in ['timestamp', 'level', 'message']:
        if field not in log:
            return False, f"Missing required field: {field}"
    # Validate timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(log['timestamp'])
    except Exception:
        return False, "Invalid timestamp format, must be ISO 8601"
    # Validate level
    if log['level'].upper() not in ALLOWED_LEVELS:
        return False, f"Invalid log level: {log['level']}"
    # Validate message
    if not isinstance(log['message'], str) or not log['message'].strip():
        return False, "Message must be a non-empty string"
    return True, None


def store_log(log):
    # Add log to queue for processing
    from log_processor import enqueue_log
    enqueue_log(log)


def add_processed_log(log):
    global _total_logs_processed
    with _logs_lock:
        _processed_logs.append(log)
        _total_logs_processed += 1


def get_logs(level_filter=None):
    with _logs_lock:
        filtered = _processed_logs
        if level_filter:
            filtered = [log for log in filtered if log['level'].upper() == level_filter]
        # Sort by timestamp ascending
        try:
            filtered.sort(key=lambda l: datetime.fromisoformat(l['timestamp']))
        except Exception:
            # If timestamp parsing fails, fallback to no sorting
            pass
        # Return a copy to avoid mutation
        return [log.copy() for log in filtered]


def get_metrics():
    from notifications import get_notifications_sent
    with _logs_lock:
        return {
            "total_logs_processed": _total_logs_processed,
            "notifications_sent": get_notifications_sent()
        }
