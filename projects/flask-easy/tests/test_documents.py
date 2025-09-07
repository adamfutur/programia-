from datetime import datetime, timezone
from tests.helpers import json_of_response

def test_create_event(client):
    """Test creating a new event."""
    event_data = {
        'name': 'Music Concert',
        'date': '01-10-2024',
        'venue': 'City Arena',
        'available_tickets': 100,
        'price': 50.00
    }
    response = client.post('/events', json=event_data)
    assert response.status_code == 201
    event = json_of_response(response)
    assert event['name'] == event_data['name']
    assert event['venue'] == event_data['venue']
    assert event['available_tickets'] == event_data['available_tickets']
    assert event['price'] == event_data['price']


def test_get_all_events(client):
    """Test retrieving all events."""
    event_data = {
        'name': 'Music Concert',
        'date': '01-10-2024',
        'venue': 'City Arena',
        'available_tickets': 100,
        'price': 50.00
    }
    response = client.post('/events', json=event_data)
    assert response.status_code == 201

    response = client.get('/events')
    assert response.status_code == 200
    events = json_of_response(response)
    assert any(e['name'] == 'Music Concert' for e in events)

# Example of timezone-aware datetime usage in tests

def test_datetime_timezone_aware():
    now = datetime.now(timezone.utc)
    assert now.tzinfo is not None
