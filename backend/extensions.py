
# Purpose: To hold uninitialized extension instances. This breaks circular imports.

from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Create extension instances without attaching them to a Flask app yet.

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
cache = Cache()
jwt = JWTManager()

# Create a standalone Celery instance. It will be configured by the app factory.
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')