from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

utc = pytz.UTC

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)  # stored as Date type
    venue = db.Column(db.String(120), nullable=False)
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
