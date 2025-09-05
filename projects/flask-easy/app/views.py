from datetime import datetime
from flask import Blueprint, jsonify, request
from app import db
from app.models import Event

event_blueprint = Blueprint("events", __name__, url_prefix="/events")

@event_blueprint.route("")
def __event():
    pass
# Write your code here

# Write your code here
