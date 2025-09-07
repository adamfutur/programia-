from flask import Blueprint, request, jsonify
from models import User

user = Blueprint('user', __name__)

@user.route('/token/', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user_obj = User.query.filter_by(username=username).first()
    if user_obj and user_obj.check_password(password):
        token = create_jwt_token(user_obj)
        return jsonify({'access_token': token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@user.route('/list/', methods=['GET'])
def list_users():
    users = User.query.all()
    users_data = [{'id': u.id, 'username': u.username} for u in users]
    return jsonify(users_data), 200
