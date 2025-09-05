# Flask: Log Processing System
Implement a log processing system with Flask and Python scripts, designed to parse, prioritize, notify, and monitor logs. The system supports multiple log formats, allows flexible notification options, and stores logs for querying and analysis.

## Environment
* Python version: 3.11
* Flask version: 3.0.3
* Default Port: 8000

## Read-Only Files
* tests/*

## Commands
- install:

```bash
virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
```

- run:

```bash
flask run -p 8000
```

- test:

```bash
flask --app manage.py test
```

## Sample Data
```json
{
  "timestamp": "2024-11-08T14:23:30",
  "level": "CRITICAL",
  "service": "auth",
  "request_id": "abc123",
  "message": "User authentication failed",
  "data": {
    "user_id": "user123",
    "ip_address": "192.168.1.1"
  }
}
```

## API Endpoint Descriptions

The log processing system should adhere to the following API format and response codes:

`POST /logs`
  * Description: Parses and stores a new log entry. 
  * Request Body: JSON object with log details. 
  * If successful, Response Code: 201 Created, Response Body: "status":"Log processed successfully".
  * If invalid, Response Code: 400, Response Body: "error":"Invalid log data".

`GET /logs`
  * Description: Returns all logs, optionally filtered by level and sorted by timestamp.
  * Query Parameters: level (optional): Filter by log level (e.g., INFO, WARNING, CRITICAL).
  * Response Code: 200 OK
  * Response Body: List of logs.
  
`GET /metrics`
* Description: Returns real-time metrics for log processing and notifications.
* Response Code: 200 OK
* Response Body: JSON object with metrics data, e.g., { "logs_processed": 500, "notifications_sent": 100 }

## Sample Requests & Responses

<details><summary>Expand to view details on sample requests and responses for each endpoint.</summary>

`POST /logs`

Request body:
```
{
  "timestamp": "2024-11-08T14:23:30",
  "level": "CRITICAL",
  "service": "auth",
  "request_id": "abc123",
  "message": "user authentication failed",
  "data": {
    "user_id": "user123",
    "ip_address": "192.168.1.1"
  }
}
```

The response code is 201, and when converted to JSON, the response body is:
```
{
    "status": "Log processed successfully"
}
```

This adds a new object to the collection.

`GET /logs`

This will return all the logs currently present in the queue.

The response code is 200, and when converted to JSON, the response body (assuming that the below objects are all objects in the log) is as follows:
```
[
  {
    "timestamp": "2024-11-08T14:23:30",
    "level": "INFO",
    "service": "auth",
    "request_id": "abc123",
    "message": "user authentication failed",
    "data": {
      "user_id": "user123",
      "ip_address": "192.168.1.1"
    }
  },
  {
    "timestamp": "2024-11-09T14:23:30",
    "level": "WARNING",
    "service": "auth",
    "request_id": "abc123",
    "message": "send notification failed",
    "data": {
      "user_id": "user1234",
      "ip_address": "192.168.1.1"
    }
  }
]
```

`GET /metrics`

This will return the count of logs inserted and processed from the queue.

Assuming there are logs in the system, then the response code is 200 and the response body, when converted to JSON, is as follows:
```
{
    "logs_processed": 50,
    "notifications_sent": 10
}
```
</details>
