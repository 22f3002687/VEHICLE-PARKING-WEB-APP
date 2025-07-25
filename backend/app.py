from flask import Flask, jsonify, request, send_from_directory
from flask_jwt_extended import JWTManager
from .models import *
from .extensions import db, cache, jwt, celery
import os
from dotenv import load_dotenv
from .controllers import auth_bp, admin_bp, user_bp
from flask_cors import CORS


basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    frontend_dist_path = os.path.join(basedir, '..', 'frontend', 'dist')
    
    # Configure Flask to serve static files from the root of the 'dist' folder
    app = Flask(__name__, static_folder=frontend_dist_path, static_url_path='')
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_HOST'] = 'localhost'
    app.config['CACHE_REDIS_PORT'] = 6379
    app.config['CACHE_REDIS_DB'] = 0
    app.config['CACHE_DEFAULT_TIMEOUT'] = 600  

    cache.init_app(app)
    load_dotenv()
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'parking.db')
    db.init_app(app)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    jwt.init_app(app)
    CORS(app)

    app.config['broker_url'] = 'redis://localhost:6379/0'
    app.config['result_backend'] = 'redis://localhost:6379/0'

    celery.conf.update(app.config)
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_vue_app(path):
        """Serves the Vue application"""
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        if request.path not in ['/', '/login', '/register', '/admin', '/dashboard', '/profile']:
            return jsonify({"msg": "Endpoint not found"}), 404
        return send_from_directory(app.static_folder, 'index.html')
    
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