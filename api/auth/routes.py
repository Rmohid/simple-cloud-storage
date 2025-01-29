from flask import jsonify, request, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from datetime import datetime, UTC

from api.auth import bp
from api.core.database import get_db
from api.core.errors import ValidationError, AuthenticationError
from api.core.models import User

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'msg': 'Username and password are required'}), 400
    
    # Validate username format
    username = data['username'].strip()
    if not username or len(username) < 3:
        return jsonify({'msg': 'Username must be at least 3 characters long'}), 400
    
    # Check if username already exists
    if User.find_by_username(username):
        return jsonify({'msg': 'Username already exists'}), 400
    
    # Create new user
    user = User.create(
        username=username,
        password_hash=generate_password_hash(data['password'])
    )
    
    # Generate tokens
    access_token = create_access_token(identity=str(user['_id']))
    refresh_token = create_refresh_token(identity=str(user['_id']))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': str(user['_id']),
            'username': user['username']
        }
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """Login user and return tokens"""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'msg': 'Username and password are required'}), 400
    
    # Find user by username
    user = User.find_by_username(data['username'])
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'msg': 'Invalid username or password'}), 401
    
    # Generate tokens
    access_token = create_access_token(identity=str(user['_id']))
    refresh_token = create_refresh_token(identity=str(user['_id']))
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': str(user['_id']),
            'username': user['username']
        }
    })

@bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    refresh_token = create_refresh_token(identity=current_user)
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token
    })

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    current_user = get_jwt_identity()
    user = User.get_collection().find_one({'_id': ObjectId(current_user)})
    if not user:
        return jsonify({'msg': 'User not found'}), 401
    
    return jsonify({
        'id': str(user['_id']),
        'username': user['username']
    })