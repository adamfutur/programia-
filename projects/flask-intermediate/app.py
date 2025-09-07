from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create DB and add a test user if not exists
@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='testuser').first():
        user = User(username='testuser')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()


def create_access_token(identity):
    payload = {
        'sub': identity,
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    # PyJWT >= 2.0 returns str, else bytes
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def create_refresh_token(identity):
    payload = {
        'sub': identity,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

@app.route('/token/', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"detail": "Invalid username or password"}), 401

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"detail": "Invalid username or password"}), 401

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        return jsonify({"access": access, "refresh": refresh}), 200
    else:
        return jsonify({"detail": "Invalid username or password"}), 401

@app.route('/list/', methods=['GET'])
def list_users():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"detail": "Invalid username or password."}), 401

    token = parts[1]

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload.get('sub')
        if not user_id:
            return jsonify({"detail": "Invalid username or password."}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"detail": "Invalid username or password."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"detail": "Invalid username or password."}), 401

    users = User.query.all()
    users_list = [{"id": u.id, "username": u.username} for u in users]
    return jsonify(users_list), 200

if __name__ == '__main__':
    app.run(debug=True)
