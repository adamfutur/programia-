from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from .models import CustomUser, db

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/register/', methods=['POST'])
def register_user():
    """Register a new user."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if CustomUser.query.filter_by(username=username).first():
        return jsonify({"detail": "User already exists"}), 400

    new_user = CustomUser(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"detail": "User created successfully"}), 201

@user_blueprint.route('/token/', methods=['POST'])
def login():
    """Authenticate user and return access and refresh tokens."""
    pass
# Your code

@user_blueprint.route('/list/', methods=['GET'])
# Implement authorization
def list_users():
    """Return all user records for authenticated users."""
    pass
# Your code


