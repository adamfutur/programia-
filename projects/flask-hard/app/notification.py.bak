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

    @staticmethod
    def send_notification(log_entry):
        """
        This method will increment the count for 'notifications_sent' & return notification sent successfully!
        """
        print(f"Notification sent for {log_entry['level']}: {log_entry['message']}")
        return "notification sent successfully!"
