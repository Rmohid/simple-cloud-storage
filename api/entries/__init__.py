from flask import Blueprint

bp = Blueprint('entries', __name__)

from api.entries import routes