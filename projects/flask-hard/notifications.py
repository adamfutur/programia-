import time
import threading
from config import config, FLASK_CONFIG


class NotificationManager:
    def __init__(self):
        # Cooldown per level in seconds
        self.cooldown = {
            "CRITICAL": config[FLASK_CONFIG].CRITICAL,
            "WARNING": config[FLASK_CONFIG].WARNING,
            "INFO": config[FLASK_CONFIG].INFO
        }
        self.last_notification_time = {}
        self.lock = threading.Lock()

    def send_notification(self, log_entry):
        level = log_entry.get('level', '').upper()
        if level not in ('WARNING', 'CRITICAL'):
            # Only send notifications for WARNING or CRITICAL
            return False

        now = time.time()

        with self.lock:
            last_time = self.last_notification_time.get(level, 0)
            cooldown_period = self.cooldown.get(level, 0)
            if now - last_time < cooldown_period:
                # Cooldown active, skip notification
                return False

            # Send notification (placeholder logic)
            self._notify(log_entry)

            # Update last notification time
            self.last_notification_time[level] = now

            return True

    def _notify(self, log_entry):
        # Placeholder for actual notification sending logic
        # For now, just print
        print(f"Notification sent for {log_entry.get('level')}: {log_entry.get('message')}")
