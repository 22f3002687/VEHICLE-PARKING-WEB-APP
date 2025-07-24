from ..extensions import db
import pytz

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import event, DDL, text

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
    parking_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    leaving_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    booking_timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC).astimezone(IST), nullable=False)
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
            'lot': self.spot.lot.to_dict() if self.spot and self.spot.lot else None, 
            'user_name' : self.user.username if self.user else None
        }
    

# --- FTS5 Virtual Table Creation using DDL Events ---

@event.listens_for(db.metadata, 'after_create')
def create_fts_tables(target, connection, **kw):
    """Create FTS5 virtual tables after all standard tables are created."""
    connection.execute(text('''
        CREATE VIRTUAL TABLE IF NOT EXISTS parking_lot_fts USING fts5(
            location_name, 
            address, 
            pincode, 
            content='parking_lots', 
            content_rowid='id'
        );
    '''))
    connection.execute(text('''
        CREATE VIRTUAL TABLE IF NOT EXISTS user_fts USING fts5(
            username, 
            email, 
            content='users', 
            content_rowid='id'
        );
    '''))

# --- FTS5 Synchronization Triggers using DDL Events ---

@event.listens_for(db.metadata, 'after_create')
def create_fts_triggers(target, connection, **kw):
    """Create triggers to keep FTS tables in sync with main tables."""
    # Triggers for ParkingLot
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS parking_lots_after_insert
        AFTER INSERT ON parking_lots
        BEGIN
            INSERT INTO parking_lot_fts(rowid, location_name, address, pincode)
            VALUES (new.id, new.location_name, new.address, new.pincode);
        END;
    '''))
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS parking_lots_after_delete
        AFTER DELETE ON parking_lots
        BEGIN
            INSERT INTO parking_lot_fts(parking_lot_fts, rowid, location_name, address, pincode)
            VALUES ('delete', old.id, old.location_name, old.address, old.pincode);
        END;
    '''))
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS parking_lots_after_update
        AFTER UPDATE ON parking_lots
        BEGIN
            INSERT INTO parking_lot_fts(parking_lot_fts, rowid, location_name, address, pincode)
            VALUES ('delete', old.id, old.location_name, old.address, old.pincode);
            INSERT INTO parking_lot_fts(rowid, location_name, address, pincode)
            VALUES (new.id, new.location_name, new.address, new.pincode);
        END;
    '''))

    # Triggers for User
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS users_after_insert
        AFTER INSERT ON users
        BEGIN
            INSERT INTO user_fts(rowid, username, email)
            VALUES (new.id, new.username, new.email);
        END;
    '''))
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS users_after_delete
        AFTER DELETE ON users
        BEGIN
            INSERT INTO user_fts(user_fts, rowid, username, email)
            VALUES ('delete', old.id, old.username, old.email);
        END;
    '''))
    connection.execute(text('''
        CREATE TRIGGER IF NOT EXISTS users_after_update
        AFTER UPDATE ON users
        BEGIN
            INSERT INTO user_fts(user_fts, rowid, username, email)
            VALUES ('delete', old.id, old.username, old.email);
            INSERT INTO user_fts(rowid, username, email)
            VALUES (new.id, new.username, new.email);
        END;
    '''))