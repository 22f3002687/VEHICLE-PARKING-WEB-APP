from datetime import timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from ..models import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """ User registration endpoint."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"msg": "Username, email, and password are required"}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"msg": "Username or email already exists"}), 409

    new_user = User(username=username, email=email, role='user')
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Login endpoint for both admins and users."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims, expires_delta=timedelta(minutes=10))
        return jsonify(access_token=access_token, role=user.role, username=user.username)

    return jsonify({"msg": "Invalid credentials"}), 401

@auth_bp.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Fetches the profile details for the currently logged-in user or admin."""
    current_user_id = int(get_jwt_identity())

    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    
    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
    }), 200
