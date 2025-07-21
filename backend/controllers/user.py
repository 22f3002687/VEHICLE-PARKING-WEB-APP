from functools import wraps
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, verify_jwt_in_request
from models import User


def user_required():
    """Custom decorator to protect routes that require standard user access."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") == "user":
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="User access required!"), 403
        return decorator
    return wrapper

user_bp = Blueprint('user', __name__)

@user_bp.route('/api/user/dashboard', methods=['GET'])
@jwt_required()
@user_required()
def user_dashboard():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(logged_in_as=user.username, message="Welcome to your User Dashboard!")