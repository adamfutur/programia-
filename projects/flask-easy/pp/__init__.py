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
