from flask import Flask
from models import *
import os
from dotenv import load_dotenv


def create_app():
    app = Flask(__name__)
    load_dotenv()
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
    db.init_app(app)

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(username="Adminstartor", email='admin@park.com', role='admin')
            admin.set_password('admin@#2468')
            db.session.add(admin)
            db.session.commit()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)