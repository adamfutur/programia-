import time
from tests.helpers import json_of_response
from app.log_processor import LogProcessor


def test_get_metrics_endpoint(client, test_data):
    """GET /metrics endpoint"""
    for log in test_data["logs"]:
        client.post('/logs', json=log)
    response = client.get('/metrics')
    assert response.status_code == 200
    print(response.data)
    metrics = json_of_response(response)
    assert metrics["logs_processed"] > 0


def test_log_valid_data(client, test_data):
    """Test POST /logs with valid data"""
    logs = test_data["logs"]
    for log in logs:
        response = client.post("/logs", json=log)
        assert response.status_code == 201
        assert json_of_response(response)["status"] == "Log processed successfully"


def test_queue_initialization():
    """Verify queue initialize for all log level."""
    log_processor = LogProcessor()
    assert set(log_processor.queues.keys()) == {"CRITICAL", "WARNING", "INFO"}
    assert len(log_processor.consumer_threads) == 3
    assert all(thread.is_alive() for thread in log_processor.consumer_threads)


def test_invalid_log_data(client, test_data):
    """Test POST /logs with invalid log data (missing required fields)."""
    invalid_data = test_data.get('invalid_log_data', [])
    for data in invalid_data:
        response = client.post('/logs', json=data)
        assert response.status_code == 400
        assert "Invalid log data" in response.json["error"]


def test_get_logs_endpoint_with_filter(client, test_data):
    """GET /logs endpoint with level filter."""
    for log in test_data["logs"]:
        client.post('/logs', json=log)
    for level in ["CRITICAL", "WARNING", "INFO"]:
        response = client.get(f'/logs?level={level}')
        assert response.status_code == 200
        logs = json_of_response(response)
        assert all(log["level"] == level for log in logs)


def test_get_logs_endpoint_invalid_filter(client):
    """GET /logs endpoint with invalid level filter"""
    response = client.get('/logs?level=INVALID_LEVEL')
    assert response.status_code == 200
    assert len(json_of_response(response)) == 0


def test_consumer_thread_lifecycles():
    """Test 1: Verify consumer thread lifecycle management"""
    log_processor = LogProcessor()
    assert all(thread.is_alive() for thread in log_processor.consumer_threads)
    log_processor.running = False
    assert len(log_processor.consumer_threads) > 0
    for thread in log_processor.consumer_threads:
        thread.join(timeout=2)
    assert all(not thread.is_alive() for thread in log_processor.consumer_threads)


def test_notification_cooldown_periods(client, test_data):
    """Test 3: Verify notification cooldown periods are respected"""
    log_processor = LogProcessor()
    for log in test_data["logs"]:
        log_processor.process_log(log)
    time.sleep(log_processor.notification_manager.cooldown["CRITICAL"])
    log_processor.process_log(test_data["logs"][0])
    res = json_of_response(client.get("/metrics"))
    assert res["notifications_sent"] > 0
