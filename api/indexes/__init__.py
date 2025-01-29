from flask import Blueprint

bp = Blueprint('indexes', __name__)

from api.indexes import routes