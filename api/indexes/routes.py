from flask import jsonify, request, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId

from api.indexes import bp
from api.entries import bp as entries_bp
from api.core.database import get_db
from api.core.errors import ValidationError, ResourceNotFoundError
from api.core.models import Index

# Register entries blueprint
bp.register_blueprint(entries_bp, url_prefix='/<index_id>/entries')

@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
@jwt_required()
def create_index():
    """Create a new index"""
    data = request.get_json()
    user_id = ObjectId(get_jwt_identity())
    
    # Validate required fields
    if not data or 'name' not in data:
        return jsonify({'msg': 'Name is required'}), 400
    
    # Check for duplicate name
    existing = Index.get_collection().find_one({
        'user_id': user_id,
        'name': data['name']
    })
    if existing:
        return jsonify({'msg': 'Index with this name already exists'}), 400
    
    try:
        # Create new index
        index = Index.create(
            user_id=user_id,
            name=data['name'],
            description=data.get('description', '')
        )
    except Exception as e:
        return jsonify({'msg': 'Error creating index'}), 400
    
    return jsonify({
        'id': str(index['_id']),
        'name': index['name'],
        'description': index['description']
    }), 201

@bp.route('/', methods=['GET'])
@jwt_required()
def get_indexes():
    """Get all indexes for current user"""
    user_id = ObjectId(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get indexes with pagination
    indexes = Index.find_by_user(
        user_id=user_id,
        skip=(page - 1) * per_page,
        limit=per_page
    )
    
    return jsonify([{
        'id': str(index['_id']),
        'name': index['name'],
        'description': index['description']
    } for index in indexes])

@bp.route('/<index_id>', methods=['GET'])
@jwt_required()
def get_index(index_id):
    """Get a specific index"""
    user_id = ObjectId(get_jwt_identity())
    
    # Find index
    index = Index.get_collection().find_one({
        '_id': ObjectId(index_id),
        'user_id': user_id
    })
    if not index:
        raise ResourceNotFoundError('Index not found')
    
    return jsonify({
        'id': str(index['_id']),
        'name': index['name'],
        'description': index['description']
    })

@bp.route('/<index_id>', methods=['PUT'])
@jwt_required()
def update_index(index_id):
    """Update an index"""
    data = request.get_json()
    user_id = ObjectId(get_jwt_identity())
    
    # Validate required fields
    if not data or 'name' not in data:
        raise ValidationError('Name is required')
    
    # Check if index exists
    index = Index.get_collection().find_one({
        '_id': ObjectId(index_id),
        'user_id': user_id
    })
    if not index:
        raise ResourceNotFoundError('Index not found')
    
    # Check if name is already taken
    existing = Index.get_collection().find_one({
        '_id': {'$ne': ObjectId(index_id)},
        'user_id': user_id,
        'name': data['name']
    })
    if existing:
        raise ValidationError('Index name already exists')
    
    # Update index
    success = Index.get_collection().update_one(
        {'_id': ObjectId(index_id), 'user_id': user_id},
        {'$set': {
            'name': data['name'],
            'description': data.get('description', '')
        }}
    )
    if not success:
        raise ResourceNotFoundError('Failed to update index')
    
    # Get updated index
    index = Index.get_collection().find_one({'_id': ObjectId(index_id)})
    return jsonify({
        'id': str(index['_id']),
        'name': index['name'],
        'description': index['description']
    })

@bp.route('/<index_id>', methods=['DELETE'])
@jwt_required()
def delete_index(index_id):
    """Delete an index"""
    user_id = ObjectId(get_jwt_identity())
    
    # Delete index
    success = Index.get_collection().delete_one({
        '_id': ObjectId(index_id),
        'user_id': user_id
    })
    if not success:
        raise ResourceNotFoundError('Index not found')
    
    return '', 204