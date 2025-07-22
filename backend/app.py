import datetime
from flask import Flask
from flask_jwt_extended import JWTManager
from models import *
import os
from dotenv import load_dotenv
from controllers import auth_bp, admin_bp, user_bp
from flask_cors import CORS

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'parking.db')
    db.init_app(app)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    jwt = JWTManager()
    jwt.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(username="Adminstartor", email='admin@park.com', role='admin')
            admin.set_password('admin@#2468')
            db.session.add(admin)
            db.session.commit()
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)