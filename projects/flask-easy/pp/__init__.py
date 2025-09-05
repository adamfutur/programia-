from flask import Flask, request, jsonify, abort
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
db = SQLAlchemy(app)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None

def format_date(date_obj):
    if not date_obj:
        return None
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'date': self.date.strftime('%d-%m-%Y'),
            'venue': self.venue,
            'available_tickets': self.available_tickets,
            'price': self.price
        }


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%d-%m-%Y').date()
    except (ValueError, TypeError):
        return None


def error_response(message, status_code=400):
    response = jsonify({'error': message})
    response.status_code = status_code
    return response


@app.route('/events', methods=['POST'])
def create_event():
    data = request.get_json()
    if not data:
        return error_response('Invalid JSON data')

    name = data.get('name')
    date_str = data.get('date')
    venue = data.get('venue')
    available_tickets = data.get('available_tickets')
    price = data.get('price')

    if not all([name, date_str, venue, available_tickets, price]):
        return error_response('Missing required fields')

    event_date = parse_date(date_str)
    if not event_date:
        return error_response('Invalid date format, expected dd-mm-yyyy')

    try:
        available_tickets = int(available_tickets)
        price = float(price)
    except (ValueError, TypeError):
        return error_response('Invalid available_tickets or price format')

    if available_tickets < 0 or price < 0:
        return error_response('available_tickets and price must be non-negative')

    event = Event(name=name, date=event_date, venue=venue,
                  available_tickets=available_tickets, price=price)
    try:
        db.session.add(event)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response('Database error', 500)

    return jsonify(event.to_dict()), 201


@app.route('/events', methods=['GET'])
def get_all_events():
    events = Event.query.order_by(Event.date).all()
    return jsonify([e.to_dict() for e in events]), 200


@app.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    event = Event.query.get(id)
    if not event:
        return error_response('Event not found', 404)
    return jsonify(event.to_dict()), 200


@app.route('/events/upcoming', methods=['GET'])
def get_upcoming_events():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    today = date.today()
    start_date = parse_date(start_date_str) if start_date_str else today
    if start_date is None:
        return error_response('Invalid start_date format, expected dd-mm-yyyy')

    end_date = parse_date(end_date_str) if end_date_str else None
    if end_date_str and end_date is None:
        return error_response('Invalid end_date format, expected dd-mm-yyyy')

    query = Event.query.filter(Event.date >= start_date)
    if end_date:
        query = query.filter(Event.date <= end_date)

    events = query.order_by(Event.date).all()
    return jsonify([e.to_dict() for e in events]), 200


@app.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    event = Event.query.get(id)
    if not event:
        return error_response('Event not found', 404)
    try:
        db.session.delete(event)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error_response('Database error', 500)
    return jsonify({'message': 'Event deleted'}), 200


@app.route('/events/purchase', methods=['POST'])
def purchase_tickets():
    data = request.get_json()
    if not data:
        return error_response('Invalid JSON data')

    event_id = data.get('event_id')
    quantity = data.get('quantity')

    if event_id is None or quantity is None:
        return error_response('Missing event_id or quantity')

    try:
        event_id = int(event_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return error_response('Invalid event_id or quantity format')

    if quantity <= 0:
        return error_response('Quantity must be positive')

    event = Event.query.get(event_id)
    if not event:
        return error_response('Event not found', 404)

    if event.available_tickets < quantity:
        return error_response('Not enough tickets available', 400)
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

DATE_FORMAT = "%d-%m-%Y"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.strftime(DATE_FORMAT),
            "venue": self.venue,
            "available_tickets": self.available_tickets,
            "price": self.price
        }

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except ValueError:
        return None

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")

def validate_event_data(data):
    if not data:
        return False
    required_fields = ["name", "date", "venue", "available_tickets", "price"]
    for field in required_fields:
        if field not in data:
            return False
    if not isinstance(data["name"], str) or not data["name"]:
        return False
    if not isinstance(data["venue"], str) or not data["venue"]:
        return False
    if not isinstance(data["available_tickets"], int) or data["available_tickets"] < 0:
        return False
    if not (isinstance(data["price"], float) or isinstance(data["price"], int)) or data["price"] < 0:
        return False
    if parse_date(data["date"]) is None:
        return "invalid_date"
    return True

@app.route("/events", methods=["POST"])
def create_event():
    data = request.get_json()
    valid = validate_event_data(data)
    if not valid:
        return jsonify({"error": "Invalid request body"}), 400
    if valid == "invalid_date":
        return jsonify({"error": "Invalid date format. Use dd-mm-yyyy"}), 400
    event_date = parse_date(data["date"])
    event = Event(
        name=data["name"],
        date=event_date,
        venue=data["venue"],
        available_tickets=data["available_tickets"],
        price=float(data["price"])
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

@app.route("/events/purchase", methods=["POST"])
def purchase_tickets():
    data = request.get_json()
    if not data or "event_id" not in data or "quantity" not in data:
        return jsonify({"error": "Invalid request body"}), 400
    event_id = data["event_id"]
    quantity = data["quantity"]
    if not isinstance(event_id, int) or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Invalid request body"}), 400
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.available_tickets < quantity:
        return jsonify({"error": "Not enough tickets available"}), 400
    event.available_tickets -= quantity
    total_amount = quantity * event.price
    db.session.commit()
    return jsonify({
        "message": "Purchase successful",
        "total_amount": total_amount,
        "remaining_tickets": event.available_tickets
    }), 201

@app.route("/events", methods=["GET"])
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

DATE_FORMAT = "%d-%m-%Y"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # stored as dd-mm-yyyy string
    venue = db.Column(db.String(100), nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "venue": self.venue,
            "available_tickets": self.available_tickets,
            "price": self.price
        }

def validate_date_format(datestr):
    try:
        datetime.strptime(datestr, DATE_FORMAT)
        return True
    except ValueError:
        return False

def parse_date(datestr):
    return datetime.strptime(datestr, DATE_FORMAT).date()

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized")

@app.route('/events', methods=['POST'])
def create_event():
    if not request.is_json:
        return jsonify({"error": "Invalid request body"}), 400
    data = request.get_json()
    required_fields = ['name', 'date', 'venue', 'available_tickets', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Invalid request body"}), 400
    if not validate_date_format(data['date']):
        return jsonify({"error": "Invalid date format. Use dd-mm-yyyy"}), 400
    try:
        available_tickets = int(data['available_tickets'])
        price = float(data['price'])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid request body"}), 400
    event = Event(
        name=data['name'],
        date=data['date'],
        venue=data['venue'],
        available_tickets=available_tickets,
        price=price
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

@app.route('/events/purchase', methods=['POST'])
def purchase_tickets():
    if not request.is_json:
        return jsonify({"error": "Invalid request body"}), 400
    data = request.get_json()
    if 'event_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Invalid request body"}), 400
    try:
        event_id = int(data['event_id'])
        quantity = int(data['quantity'])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid request body"}), 400
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if quantity <= 0:
        return jsonify({"error": "Invalid request body"}), 400
    if event.available_tickets < quantity:
        return jsonify({"error": "Not enough tickets available"}), 400
    event.available_tickets -= quantity
    db.session.commit()
    total_amount = round(quantity * event.price, 2)
    return jsonify({
        "message": f"Purchased {quantity} tickets for event {event.name}",
        "total_amount": total_amount,
        "remaining_tickets": event.available_tickets
    }), 201

@app.route('/events', methods=['GET'])
def get_all_events():
    events = Event.query.all()
    # Sort by date ascending
    try:
        events_sorted = sorted(events, key=lambda e: parse_date(e.date))
    except Exception:
        events_sorted = events
    return jsonify([e.to_dict() for e in events_sorted]), 200

@app.route('/events/<int:event_id>', methods=['GET'])
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # dd-mm-yyyy
    venue = db.Column(db.String(100), nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date,
            "venue": self.venue,
            "available_tickets": self.available_tickets,
            "price": self.price
        }


def validate_date_format(date_str):
    # Check dd-mm-yyyy format and valid date
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def parse_date(date_str):
    return datetime.strptime(date_str, "%d-%m-%Y").date()


@app.route('/events', methods=['POST'])
def create_event():
    if not request.is_json:
        return jsonify({"error": "Invalid request body"}), 400
    data = request.get_json()
    required_fields = ['name', 'date', 'venue', 'available_tickets', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Invalid request body"}), 400
    if not validate_date_format(data['date']):
        return jsonify({"error": "Invalid date format. Use dd-mm-yyyy"}), 400
    try:
        available_tickets = int(data['available_tickets'])
        price = float(data['price'])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid request body"}), 400

    event = Event(
        name=data['name'],
        date=data['date'],
        venue=data['venue'],
        available_tickets=available_tickets,
        price=price
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@app.route('/events/purchase', methods=['POST'])
def purchase_tickets():
    if not request.is_json:
        return jsonify({"error": "Invalid request body"}), 400
    data = request.get_json()
    if 'event_id' not in data or 'quantity' not in data:
        return jsonify({"error": "Invalid request body"}), 400
