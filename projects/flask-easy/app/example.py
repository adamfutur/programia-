from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# In-memory storage for events
events = {}
next_event_id = 1

@app.route('/events', methods=['POST'])
def create_event():
    global next_event_id
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    data = request.get_json()
    # Basic validation
    if 'name' not in data or 'date' not in data:
        return jsonify({'error': 'Missing required fields: name, date'}), 400

    event_id = next_event_id
    next_event_id += 1
    event = {
        'id': event_id,
        'name': data['name'],
        'date': data['date'],
        'description': data.get('description', '')
    }
    events[event_id] = event
    return jsonify(event), 201

@app.route('/events', methods=['GET'])
def get_all_events():
    return jsonify(list(events.values())), 200

@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = events.get(event_id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404
    return jsonify(event), 200

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    del events[event_id]
    return jsonify({'message': 'Event deleted'}), 200

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method Not Allowed'}), 405

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad Request'}), 400

if __name__ == '__main__':
    app.run(debug=True)
