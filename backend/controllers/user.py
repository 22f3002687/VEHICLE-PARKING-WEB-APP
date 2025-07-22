from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, verify_jwt_in_request
from models import *


def user_required(fn):
    """Custom decorator to protect routes that require standard user access."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "user":
            return jsonify(msg="User access required!"), 403
        return fn(*args, **kwargs)
    return wrapper

user_bp = Blueprint('user', __name__)

