from datetime import datetime
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
    
    response = client.get('/events')
    assert response.status_code == 200
    events = json_of_response(response)
    assert isinstance(events, list)
    assert len(events) > 0  

def test_get_event_by_id(client):
    """Test retrieving an event by its ID."""
    # Create an event first
    event_data = {
        'name': 'Tech Conference',
        'date': '15-10-2024',
        'venue': 'Convention Center',
        'available_tickets': 200,
        'price': 150.00
    }
    response = client.post('/events', json=event_data)
    event = json_of_response(response)

    response = client.get(f"/events/{event['id']}")
    assert response.status_code == 200
    fetched_event = json_of_response(response)
    assert fetched_event['id'] == event['id']

def test_purchase_tickets(client):
    """Test purchasing tickets for an event."""
    event_data = {
        'name': 'Food Festival',
        'date': '20-10-2024',
        'venue': 'Park Grounds',
        'available_tickets': 50,
        'price': 20.00
    }
    response = client.post('/events', json=event_data)
    event = json_of_response(response)

    purchase_data = {'event_id': event['id'], 'quantity': 5}
    response = client.post('/events/purchase', json=purchase_data)
    assert response.status_code == 201
    purchase_response = json_of_response(response)
    assert purchase_response['message'] == 'Purchase successful'
    assert purchase_response['available_tickets'] == 45  # 50 - 5

def test_purchase_tickets_insufficient(client):
    """Test purchasing more tickets than available."""
    event_data = {
        'name': 'Art Gallery Opening',
        'date': '25-10-2024',
        'venue': 'Modern Art Museum',
        'available_tickets': 10,
        'price': 30.00
    }
    response = client.post('/events', json=event_data)
    event = json_of_response(response)

    purchase_data = {'event_id': event['id'], 'quantity': 20}
    response = client.post('/events/purchase', json=purchase_data)
    assert response.status_code == 400
    assert json_of_response(response)['error'] == 'Not enough tickets available'

def test_get_upcoming_events_no_events(client):
    """Test retrieving upcoming events when no events exist."""
    response = client.get('/events/upcoming?startDate=01-01-2025')
    assert response.status_code == 200
    upcoming_events = json_of_response(response)
    assert isinstance(upcoming_events, list)  # Ensure the response is a list
    assert len(upcoming_events) == 0  # Expecting no upcoming events

def test_get_upcoming_events_with_start_and_end_date(client):
    """Test retrieving upcoming events with start and an end date filter."""
    # Create future events
    event1_data = {
        'name': 'Concert',
        'date': '05-11-2024',
        'venue': 'Stadium',
        'available_tickets': 150,
        'price': 75.00
    }
    event2_data = {
        'name': 'Exhibition',
        'date': '10-12-2024',
        'venue': 'Gallery',
        'available_tickets': 200,
        'price': 20.00
    }
    client.post('/events', json=event1_data)
    client.post('/events', json=event2_data)

    response = client.get('/events/upcoming?startDate=01-11-2024&endDate=09-12-2024')
    assert response.status_code == 200
    upcoming_events = json_of_response(response)
    assert isinstance(upcoming_events, list) 
    assert len(upcoming_events) == 1  
    assert upcoming_events[0]['name'] == 'Concert'  

def test_get_upcoming_events_invalid_start_date_format(client):
    """Test retrieving upcoming events with an invalid start date format."""
    response = client.get('/events/upcoming?startDate=2024-11-05')
    assert response.status_code == 400
    assert json_of_response(response)['error'] == 'Invalid date format. Use dd-mm-yyyy'

def test_get_upcoming_events_invalid_end_date_format(client):
    """Test retrieving upcoming events with an invalid end date format."""
    response = client.get('/events/upcoming?startDate=01-11-2024&endDate=2024-12-10')
    assert response.status_code == 400
    assert json_of_response(response)['error'] == 'Invalid date format. Use dd-mm-yyyy'

def test_get_upcoming_events_start_date_after_end_date(client):
    """Test retrieving upcoming events where start date is after end date."""
    response = client.get('/events/upcoming?startDate=10-12-2024&endDate=01-12-2024')
    assert response.status_code == 400
    assert json_of_response(response)['error'] == 'Start date cannot be after end date'

def test_get_upcoming_events_with_no_events_after_start_date(client):
    """Test retrieving upcoming events when there are no events after the specified start date."""
    event_data = {
        'name': 'Past Event',
        'date': '01-01-2024',
        'venue': 'Old Venue',
        'available_tickets': 0,
        'price': 10.00
    }
    client.post('/events', json=event_data)

    response = client.get('/events/upcoming?startDate=01-11-2024')
    assert response.status_code == 200
    upcoming_events = json_of_response(response)
    assert isinstance(upcoming_events, list)  # Ensure the response is a list
    assert len(upcoming_events) == 0  # Expecting no upcoming events

def test_get_upcoming_events_with_only_start_date(client):
    """Test retrieving upcoming events using only the start date."""
    # Create multiple future events
    event1_data = {
        'name': 'Music Festival',
        'date': '15-11-2024',
        'venue': 'Central Park',
        'available_tickets': 300,
        'price': 100.00
    }
    event2_data = {
        'name': 'Art Fair',
        'date': '20-12-2024',
        'venue': 'Exhibition Hall',
        'available_tickets': 150,
        'price': 50.00
    }
    client.post('/events', json=event1_data)
    client.post('/events', json=event2_data)

    # Fetch upcoming events from a specific start date
    response = client.get('/events/upcoming?startDate=10-11-2024')
    assert response.status_code == 200
    upcoming_events = json_of_response(response)
    assert isinstance(upcoming_events, list)  # Ensure the response is a list
    assert len(upcoming_events) == 2  # Both events should be returned
    assert upcoming_events[0]['name'] == 'Music Festival'  # Check the first event
    assert upcoming_events[1]['name'] == 'Art Fair'  # Check the second event

def test_get_upcoming_events_edge_case_today(client):
    """Test retrieving events where the start date is today."""
    today = datetime.utcnow().strftime('%d-%m-%Y')
    event_data = {
        'name': 'Live Show',
        'date': today,
        'venue': 'Theater',
        'available_tickets': 100,
        'price': 30.00
    }
    client.post('/events', json=event_data)

    response = client.get(f'/events/upcoming?startDate={today}')
    assert response.status_code == 200
    upcoming_events = json_of_response(response)
    assert len(upcoming_events) == 1  # Expecting the live show event
    assert upcoming_events[0]['name'] == 'Live Show'  # Check the name of the event

def test_delete_event(client):
    response = client.post('/events', json={
        "name": "Test Event",
        "date": "15-10-2024",
        "venue": "Test Venue",
        "available_tickets": 100,
        "price": 50.00
    })
    event = json_of_response(response)
    event_id = event['id']
    response = client.delete(f'/events/{event_id}')
    assert response.status_code == 200
    assert json_of_response(response)['message'] == "Event deleted"

    # Check if the event is deleted
    response = client.get(f'/events/{event_id}')
    assert response.status_code == 404
