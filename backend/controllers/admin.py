from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from sqlalchemy import func
from ..models import *
from ..extensions import cache, db
from ..tasks import announce_new_lot


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify(msg="Admins access required!"), 403
        return fn(*args, **kwargs)
    return wrapper


admin_bp = Blueprint('admin',__name__)


@admin_bp.route('/api/admin/lots', methods=['POST'])
@admin_required
def create_parking_lot():
    """Admin: Create a new parking lot and its spots."""
    data = request.get_json()
    location_name = data.get('location_name')
    address = data.get('address')
    pincode = data.get('pincode')
    total_spots = data.get('total_spots')
    price_per_hour = data.get('price_per_hour')

    if not all([location_name, address, pincode, total_spots, price_per_hour]):
        return jsonify({"msg": "Missing required fields"}), 400

    try:
        total_spots = int(total_spots)
        price_per_hour = float(price_per_hour)
        if total_spots <= 0 or price_per_hour <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"msg": "Total spots and price must be valid positive numbers"}), 400

    new_lot = ParkingLot(location_name=location_name, address=address, pincode=pincode, total_spots=total_spots, price_per_hour=price_per_hour)
    db.session.add(new_lot)
    db.session.flush()

    # Automatically create parking spots for the new lot
    for i in range(1, total_spots + 1):
        new_spot = ParkingSpot(spot_number=i, lot_id=new_lot.id, status='Available')
        db.session.add(new_spot)

    db.session.commit()

    # TRIGGER THE BACKGROUND TASK to send a notification
    announce_new_lot.delay(lot_name=new_lot.location_name, address=new_lot.address)

    cache.clear()
    return jsonify({"msg": "Parking lot created successfully", "lot": new_lot.to_dict()}), 201

@admin_bp.route('/api/admin/lots', methods=['GET'])
@admin_required
@cache.cached()
def get_all_lots():
    """Admin: Get a list of all parking lots."""
    lots = ParkingLot.query.all()
    return jsonify([lot.to_dict() for lot in lots]), 200

@admin_bp.route('/api/admin/lots/<int:lot_id>', methods=['GET'])
@admin_required
@cache.cached()
def get_lot_details(lot_id):
    """Admin: Get details for a specific lot, including its spots."""
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
    lot_data = lot.to_dict()
    lot_data['spots'] = [spot.to_dict() for spot in spots]
    return jsonify(lot_data), 200

@admin_bp.route('/api/admin/lots/<int:lot_id>', methods=['PUT'])
@admin_required
def update_parking_lot(lot_id):
    """Update a parking lot's details"""
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Request body cannot be empty"}), 400

    try:
    
        lot.location_name = data.get('location_name', lot.location_name)
        lot.address = data.get('address', lot.address)
        lot.pincode = data.get('pincode', lot.pincode)
        
        if 'price_per_hour' in data:
            price = float(data['price_per_hour'])
            if price <= 0:
                raise ValueError("Price must be a positive number.")
            lot.price_per_hour = price

        # Handle updating the number of spots if provided
        if 'total_spots' in data:
            new_total_spots = int(data['total_spots'])
            if new_total_spots < 0:
                 raise ValueError("Total spots cannot be negative.")

            current_spots_count = lot.total_spots

            if new_total_spots > current_spots_count:
                # Increase the number of spots
                for i in range(current_spots_count + 1, new_total_spots + 1):
                    new_spot = ParkingSpot(spot_number=i, lot_id=lot.id, status='Available')
                    db.session.add(new_spot)
            
            elif new_total_spots < current_spots_count:
                # Decrease the number of spots
                spots_to_remove_count = current_spots_count - new_total_spots
                spots_to_remove = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number.desc()).limit(spots_to_remove_count).all()

                # CRITICAL SAFETY CHECK: Ensure spots to be deleted are not occupied
                for spot in spots_to_remove:
                    if spot.status == 'Occupied':
                        db.session.rollback() # Abort the transaction
                        return jsonify({"msg": f"Cannot reduce spot count. Spot number {spot.spot_number} is currently occupied."}), 400
                
                # If all checks pass, proceed with deletion
                for spot in spots_to_remove:
                    db.session.delete(spot)

            lot.total_spots = new_total_spots

        db.session.commit()

        cache.clear()
        return jsonify({"msg": "Parking lot updated successfully", "lot": lot.to_dict()}), 200

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"msg": "Invalid input. Total spots and price must be valid positive numbers."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "An unexpected error occurred."}), 500



@admin_bp.route('/api/admin/lots/<int:lot_id>', methods=['DELETE'])
@admin_required
def delete_parking_lot(lot_id):
    """Admin: Delete a parking lot if all its spots are available."""
    lot = ParkingLot.query.get_or_404(lot_id)
    
    # Check if any spot in the lot is occupied
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='Occupied').count()
    if occupied_spots > 0:
        return jsonify({"msg": "Cannot delete lot. Some parking spots are occupied."}), 400


    db.session.delete(lot)
    db.session.commit()
    cache.clear()
    return jsonify({"msg": "Parking lot deleted successfully"}), 200

@admin_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """Admin: Get a list of all registered users."""
    users = User.query.filter_by(role='user').all()
    return jsonify([user.to_dict() for user in users]), 200

@admin_bp.route('/api/admin/reservations', methods=['GET'])
@admin_required
def get_all_reservations():
    """Admin: Get a list of all reservations across all users."""
    reservations = Reservation.query.order_by(Reservation.booking_timestamp.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200

@admin_bp.route('/api/admin/analytics', methods=['GET'])
@admin_required
def get_admin_analytics():
    """Admin: Get aggregated analytics data for charts."""
    # Revenue per lot
    revenue_per_lot = db.session.query(
        ParkingLot.location_name,
        func.sum(Reservation.parking_cost)
    ).join(ParkingSpot, ParkingSpot.lot_id == ParkingLot.id)\
     .join(Reservation, Reservation.spot_id == ParkingSpot.id)\
     .group_by(ParkingLot.location_name).all()

    # Bookings per lot
    bookings_per_lot = db.session.query(
        ParkingLot.location_name,
        func.count(Reservation.id)
    ).join(ParkingSpot, ParkingSpot.lot_id == ParkingLot.id)\
     .join(Reservation, Reservation.spot_id == ParkingSpot.id)\
     .group_by(ParkingLot.location_name).all()

    return jsonify({
        'revenuePerLot': {
            'labels': [item[0] for item in revenue_per_lot],
            'data': [item[1] for item in revenue_per_lot]
        },
        'bookingsPerLot': {
            'labels': [item[0] for item in bookings_per_lot],
            'data': [item[1] for item in bookings_per_lot]
        }
    })