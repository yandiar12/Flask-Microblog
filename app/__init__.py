from flask import Flask
from flask.ext.pymongo import PyMongo


# Initialize the Flask application
app = Flask(__name__)
app.config.from_object('config')
mongo = PyMongo(app)

from app import views, user_views