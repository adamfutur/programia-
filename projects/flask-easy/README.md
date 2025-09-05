# Flask: Event Ticketing System

## Project Specifications

**Read-Only Files**

- tests/\*

**Environment**

- Python version: 3.11
- Flask version: 3.0.3
- Flask-SQLAlchemy: 3.1.1
- Default Port: 8000

**Commands**

- install:

```bash
virtualenv venv && source venv/bin/activate && pip install -r requirements.txt
```

- run:

```bash
flask init-db && flask run -p 8000
```

- test:

```bash
flask test
```

## Question description

Implement a REST API to manage events in an Event Ticketing System. The system should allow users to create events, retrieve events, purchase tickets, delete events, and get event details. Each event has key attributes, and the API will handle various operations related to event management.

Event Model

- `id`: The unique ID of the event (Integer)
- `name`: The name of the event (String)
- `date`: The event's date (dd-mm-yyyy format)
- `venue`: The event's location (String)
- `available_tickets`: Number of tickets available (Integer)
- `price`: Price of a single ticket (Float)

### Example of an Event JSON object:

```
{
  "id": 1,
  "name": "Music Concert",
  "date": "15-10-2024",
  "venue": "City Arena",
  "available_tickets": 100,
  "price": 50.00
}
```

## Requirements:

The REST service should expose the following endpoints:

`POST /events`

- Description: Creates a new event.
- Request: A JSON event object (without id).
- Response Code: 201 on success, 400 on error.
- Response Body:
  - Success: Created event with a unique id.
  - Errors:
    - Missing data: `{"error": "Invalid request body"}`
    - Invalid date format: `{"error": "Invalid date format. Use dd-mm-yyyy"}`

`POST /events/purchase`

- Description: Purchases tickets for an event.
- Request: A JSON object with event_id and quantity.
- Response Code: 201 on success, 400/404 on error.
- Response Body:
  - Success: Confirmation of the purchase, total amount, and remaining tickets.
  - Errors:
    - Missing data: `{"error": "Invalid request body"}`
    - Event not found: `{"error": "Event not found"}`
    - Not enough tickets: `{"error": "Not enough tickets available"}`

`GET /events`

- Description: Returns a list of all events sorted by date.
- Response Code: 200
- Response Body: A list of events sorted by their date.

`GET /events/{id}`

- Description: Retrieves the details of an event by its ID.
- Response Code: 200 on success, 404 on error.
- Response Body:
  - Success: The event details.
  - Error: `{"error": "Event not found"}`

`GET /events/upcoming`:

- Description: Returns a list of upcoming events within a specified date range.
  - Query Parameters:
    - `startDate`: Optional (default is today’s date).
    - `endDate`: Optional.
  - Response Code: 200 on success, 400 on error.
  - Response Body:
    - Success: An array of upcoming events.
    - Errors:
      - Invalid date format: `{"error": "Invalid date format. Use dd-mm-yyyy"}`
      - Start date after end date: `{"error": "Start date cannot be after end date"}`

`DELETE /events/{id}`:

- Description: Deletes an event by its ID.
- Response Code: 200 on success, 404 on error.
- Response Body:
  - Success: `{"message": "Event deleted"}`
  - Error: `{"error": "Event not found"}`
