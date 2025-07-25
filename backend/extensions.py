
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
cache = Cache()
jwt = JWTManager()
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')