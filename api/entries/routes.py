from flask import jsonify, request, current_app, g, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import io
import magic
from datetime import datetime

from api.entries import bp
from api.core.database import get_db, get_file_storage
from api.core.errors import ValidationError, ResourceNotFoundError
from api.core.models import Entry, Index

@bp.route('', methods=['POST'])
@jwt_required()
def create_entry(index_id):
    """Create a new entry"""
    user_id = ObjectId(get_jwt_identity())
    
    # Get index from URL parameter
    try:
        index = Index.get_collection().find_one({
            '_id': ObjectId(index_id),
            'user_id': user_id
        })
        if not index:
            return jsonify({'msg': 'Index not found'}), 404
    except:
        return jsonify({'msg': 'Invalid index ID'}), 400
    
    file = None
    filename = None
    content_type = None
    file_id = None
    content = None
    entry_type = None
    keywords = []

    # Handle file upload
    if request.files and 'file' in request.files:
        file = request.files['file']
        try:
            # Read file content
            file_data = file.read()
            filename = secure_filename(file.filename)
            
            # Get content type from file object or default to octet-stream
            content_type = file.mimetype or 'application/octet-stream'
            
            # Store file
            file_id = get_file_storage().store_file(
                file_data,
                filename=filename,
                content_type=content_type
            )
            entry_type = 'file'
            content = None
            # Get keywords from form data
            keywords = [k.strip() for k in request.form.get('keywords', '').split(',') if k.strip()]
            
            # Add file metadata
            metadata = {
                'filename': filename,
                'content_type': content_type
            }
        except Exception as e:
            return jsonify({'msg': 'Error processing file upload'}), 400
    # Handle text entry
    elif request.is_json:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'msg': 'Missing content in JSON body'}), 400
            
        entry_type = 'text'
        content = data['content']
        # Handle keywords as array or string
        if isinstance(data.get('keywords'), list):
            keywords = data['keywords']
        else:
            keywords = [k.strip() for k in data.get('keywords', '').split(',') if k.strip()]
        file_id = None
        metadata = None
    else:
        return jsonify({'msg': 'Request must be either multipart/form-data for files or application/json for text'}), 400
    
    # Create entry
    try:
        entry = Entry.create(
            index_id=ObjectId(index_id),
            user_id=user_id,
            type=entry_type,
            content=content,
            file_id=file_id,
            metadata=metadata,
            keywords=keywords
        )
    except Exception as e:
        if file_id:
            try:
                get_file_storage().delete_file(str(file_id))
            except:
                pass
        return jsonify({'msg': 'Error creating entry'}), 400
    
    return jsonify({
        'id': str(entry['_id']),
        'type': entry['type'],
        'content': entry.get('content'),
        'file_id': str(entry['file_id']) if entry.get('file_id') else None,
        'metadata': entry.get('metadata'),
        'keywords': entry.get('keywords', []),
        'created_at': entry['created_at'].isoformat()
    }), 201

@bp.route('', methods=['GET'])
@jwt_required()
def get_entries(index_id):
    """Get entries for an index"""
    user_id = ObjectId(get_jwt_identity())
    
    # Get index from URL parameter
    index_id = request.view_args.get('index_id')
    index = Index.get_collection().find_one({
        '_id': ObjectId(index_id),
        'user_id': user_id
    })
    if not index:
        raise ResourceNotFoundError('Index not found')
    
    # Get entries with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    entries = Entry.find_by_index(
        index_id=ObjectId(index_id),
        skip=(page - 1) * per_page,
        limit=per_page
    )
    
    return jsonify([{
        'id': str(entry['_id']),
        'type': entry['type'],
        'content': entry.get('content'),
        'file_id': str(entry['file_id']) if entry.get('file_id') else None,
        'metadata': entry.get('metadata'),
        'keywords': entry.get('keywords', []),
        'created_at': entry['created_at'].isoformat()
    } for entry in entries])

@bp.route('/<entry_id>', methods=['GET'])
@jwt_required()
def get_entry(index_id, entry_id):
    """Get a specific entry"""
    user_id = ObjectId(get_jwt_identity())
    
    # Find entry
    entry = Entry.get_collection().find_one({
        '_id': ObjectId(entry_id),
        'user_id': user_id
    })
    if not entry:
        raise ResourceNotFoundError('Entry not found')
    
    # If file entry, get file
    if entry['type'] == 'file':
        try:
            file_data, filename, content_type = get_file_storage().get_file(str(entry['file_id']))
            return send_file(
                io.BytesIO(file_data),
                mimetype=content_type,
                as_attachment=True,
                download_name=filename
            )
        except FileNotFoundError:
            raise ResourceNotFoundError('File not found')
    
    return jsonify({
        'id': str(entry['_id']),
        'type': entry['type'],
        'content': entry.get('content'),
        'file_id': str(entry['file_id']) if entry.get('file_id') else None,
        'metadata': entry.get('metadata'),
        'keywords': entry.get('keywords', []),
        'created_at': entry['created_at'].isoformat()
    })

@bp.route('/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_entry(index_id, entry_id):
    """Delete an entry"""
    user_id = ObjectId(get_jwt_identity())
    
    # Find entry
    entry = Entry.get_collection().find_one({
        '_id': ObjectId(entry_id),
        'user_id': user_id
    })
    if not entry:
        raise ResourceNotFoundError('Entry not found')
    
    # Delete file if file entry
    if entry['type'] == 'file':
        try:
            get_file_storage().delete_file(str(entry['file_id']))
        except FileNotFoundError:
            pass  # Ignore if file already deleted
    
    # Delete entry
    Entry.get_collection().delete_one({'_id': ObjectId(entry_id)})
    
    return '', 204

@bp.route('/search', methods=['GET'])
@jwt_required()
def search_entries(index_id):
    """Search entries in an index"""
    if not request.headers.get('Authorization'):
        return jsonify({'msg': 'Missing Authorization Header'}), 401
        
    try:
        user_id = ObjectId(get_jwt_identity())
        index_id = ObjectId(index_id)
    except:
        return jsonify({'msg': 'Missing Authorization Header'}), 401
    
    # Get search query
    query = request.args.get('q')
    if not query:
        return jsonify({'msg': 'Search query is required'}), 400
    
    # Validate index exists and user has access
    try:
        index = Index.get_collection().find_one({
            '_id': index_id,
            'user_id': user_id
        })
        if not index:
            return jsonify({'msg': 'Missing Authorization Header'}), 401
    except:
        return jsonify({'msg': 'Missing Authorization Header'}), 401
    
    # Create text index if it doesn't exist
    Entry.get_collection().create_index([('content', 'text'), ('keywords', 'text')])
    
    # Search entries
    entries = list(Entry.get_collection().find_many({
        'index_id': index_id,
        'user_id': user_id,
        '$text': {'$search': query}
    }))
    
    return jsonify({
        'entries': [{
            'id': str(entry['_id']),
            'type': entry['type'],
            'content': entry.get('content'),
            'file_id': str(entry['file_id']) if entry.get('file_id') else None,
            'metadata': entry.get('metadata'),
            'keywords': entry.get('keywords', []),
            'created_at': entry['created_at'].isoformat()
        } for entry in entries]
    })
    """Search entries in an index"""
    user_id = ObjectId(get_jwt_identity())
    
    # Get index from URL parameter
    index_id = request.view_args.get('index_id')
    index = Index.get_collection().find_one({
        '_id': ObjectId(index_id),
        'user_id': user_id
    })
    if not index:
        raise ResourceNotFoundError('Index not found')
    
    # Get search query
    query = request.args.get('q')
    if not query:
        raise ValidationError('Search query is required')
    
    # Get entries with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    entries = Entry.search(
        index_id=ObjectId(index_id),
        query=query,
        skip=(page - 1) * per_page,
        limit=per_page
    )
    
    return jsonify([{
        'id': str(entry['_id']),
        'type': entry['type'],
        'content': entry.get('content'),
        'file_id': str(entry['file_id']) if entry.get('file_id') else None,
        'metadata': entry.get('metadata'),
        'keywords': entry.get('keywords', []),
        'created_at': entry['created_at'].isoformat()
    } for entry in entries])