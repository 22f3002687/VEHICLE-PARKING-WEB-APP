from flask_sqlalchemy import SQLAlchemy
import pytz
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

IST = pytz.timezone("Asia/Kolkata")

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    reservations = db.relationship('Reservation', backref='user',cascade="all, delete-orphan", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }

# Parking Lot Model
class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(150), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    total_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        available_count = ParkingSpot.query.filter_by(lot_id=self.id, status='Available').count()

        return {
            'id': self.id,
            'location_name': self.location_name,
            'address': self.address,
            'pincode': self.pincode,
            'total_spots': self.total_spots,
            'price_per_hour': self.price_per_hour,
            'available_spots': available_count
        }

# Parking Spot Model
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.Integer, nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status = db.Column(db.String(10), default='Available', nullable=False)
    reservations = db.relationship('Reservation', backref='spot',cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'spot_number': self.spot_number,
            'lot_id': self.lot_id,
            'status': self.status
        }

# Reservation Model
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, nullable=True)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    booking_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC).astimezone(IST), nullable=False)
    parking_cost = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'user_id': self.user_id,
            'booking_timestamp': self.booking_timestamp.isoformat() if self.booking_timestamp else None,
            'parking_timestamp': self.parking_timestamp.isoformat() if self.parking_timestamp else None,
            'leaving_timestamp': self.leaving_timestamp.isoformat() if self.leaving_timestamp else None,
            'parking_cost': self.parking_cost,
            'is_active': self.is_active,
            'spot': self.spot.to_dict() if self.spot else None,
            'lot': self.spot.lot.to_dict() if self.spot and self.spot.lot else None
        }