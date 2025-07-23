from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, verify_jwt_in_request
import pytz
from sqlalchemy import func
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

IST = pytz.timezone("Asia/Kolkata")
user_bp = Blueprint('user', __name__)

@user_bp.route('/api/user/lots', methods=['GET'])
@jwt_required()
def get_available_lots():
    """User: Get a list of all parking lots."""
    lots = ParkingLot.query.all()
    return jsonify([lot.to_dict() for lot in lots]), 200

@user_bp.route('/api/user/reservations', methods=['GET'])
@jwt_required()
def get_user_reservations():
    """User: Get their own active and past reservations."""
    user_id = int(get_jwt_identity())
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.booking_timestamp.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200

@user_bp.route('/api/user/reservations/book', methods=['POST'])
@user_required
def book_spot():
    """User: Book one or more available spots in a given lot."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    lot_id = data.get('lot_id')
    number_of_spots = data.get('number_of_spots', 1)

    if not lot_id:
        return jsonify({"msg": "Lot ID is required"}), 400
    
    try:
        number_of_spots = int(number_of_spots)
        if number_of_spots <= 0:
            return jsonify({"msg": "Number of spots must be a positive integer."}), 400
    except (ValueError, TypeError):
        return jsonify({"msg": "Invalid number of spots provided."}), 400

    # Find available spots in the lot
    available_spots = ParkingSpot.query.filter_by(lot_id=int(lot_id), status='Available').order_by(ParkingSpot.spot_number).limit(number_of_spots).all()

    # Check if there are enough spots
    if len(available_spots) < number_of_spots:
        return jsonify({"msg": f"Not enough spots available. Only {len(available_spots)} spots are free."}), 404

    new_reservations = []
    # Book the spots
    for spot in available_spots:
        spot.status = 'Booked'
        new_reservation = Reservation(spot_id=spot.id, user_id=user_id)
        db.session.add(new_reservation)
        new_reservations.append(new_reservation)

    db.session.commit()
    
    message = f"{number_of_spots} spot{'s' if number_of_spots > 1 else ''} booked successfully!"
    
    return jsonify({
        "msg": message,
        "reservations": [r.to_dict() for r in new_reservations]
    }), 201

@user_bp.route('/api/user/reservations/park', methods=['PUT'])
@user_required
def park_vehicle():
    """User: Confirm that they have parked their vehicle for a specific reservation."""
    user_id = int(get_jwt_identity())
    reservation_id = request.get_json().get('reservation_id')
    if not reservation_id:
        return jsonify({"msg": "Reservation ID is required."}), 400

    reservation = Reservation.query.filter_by(id=int(reservation_id), user_id=user_id, is_active=True).first()
    if not reservation: return jsonify({"msg": "Active booking for this reservation not found."}), 404
    if reservation.parking_timestamp: return jsonify({"msg": "Vehicle already parked for this reservation."}), 400

    spot = reservation.spot
    spot.status = 'Occupied'
    reservation.parking_timestamp = datetime.now(pytz.UTC).astimezone(IST)
    db.session.commit()
    return jsonify({"msg": "Vehicle parked successfully.", "reservation": reservation.to_dict()}), 200

@user_bp.route('/api/user/reservations/vacate', methods=['PUT'])
@user_required
def vacate_spot():
    user_id = int(get_jwt_identity())
    reservation_id = request.get_json().get('reservation_id')
    if not reservation_id:
        return jsonify({"msg": "Reservation ID is required."}), 400
        
    reservation = Reservation.query.filter_by(id=int(reservation_id), user_id=user_id, is_active=True).first()
    if not reservation: 
        return jsonify({"msg": "Active reservation not found."}), 404

    spot = reservation.spot
    

    if reservation.parking_timestamp:
        lot = spot.lot
        reservation.leaving_timestamp = datetime.now(pytz.UTC).astimezone(IST)
        duration = reservation.leaving_timestamp.replace(tzinfo=None) - reservation.parking_timestamp.replace(tzinfo=None)
        hours = max(1, duration.total_seconds() / 3600)
        reservation.parking_cost = round(hours * lot.price_per_hour, 2)
        message = f"Spot vacated successfully. Total cost: ₹{reservation.parking_cost:.2f}"
    else:
        reservation.leaving_timestamp = datetime.now(pytz.UTC).astimezone(IST)
        reservation.parking_cost = 0.0
        message = "Booking cancelled successfully."

    spot.status = 'Available'
    reservation.is_active = False
    
    db.session.commit()
    return jsonify({"msg": message, "reservation": reservation.to_dict()}), 200

@user_bp.route('/api/user/analytics', methods=['GET'])
@jwt_required()
def get_user_analytics():
    """User: Get personal analytics data."""
    user_id = get_jwt_identity()

    # Lot usage frequency
    lot_usage = db.session.query(
        ParkingLot.location_name,
        func.count(Reservation.id)
    ).join(ParkingSpot, ParkingSpot.lot_id == ParkingLot.id)\
     .join(Reservation, Reservation.spot_id == ParkingSpot.id)\
     .filter(Reservation.user_id == user_id)\
     .group_by(ParkingLot.location_name).all()

    # Spending per month
    spending_per_month = db.session.query(
        func.strftime('%Y-%m', Reservation.parking_timestamp),
        func.sum(Reservation.parking_cost)
    ).filter(Reservation.user_id == user_id, Reservation.parking_cost.isnot(None))\
     .group_by(func.strftime('%Y-%m', Reservation.parking_timestamp))\
     .order_by(func.strftime('%Y-%m', Reservation.parking_timestamp)).all()

    return jsonify({
        'lotUsage': {
            'labels': [item[0] for item in lot_usage],
            'data': [item[1] for item in lot_usage]
        },
        'spendingPerMonth': {
            'labels': [item[0] for item in spending_per_month],
            'data': [item[1] for item in spending_per_month]
        }
    })