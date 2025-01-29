import pytest
import io
from flask import json
from bson import ObjectId
from datetime import datetime, UTC

def test_create_text_entry(client, auth_headers, test_index):
    """Test creating a text entry"""
    response = client.post(
        f'/api/indexes/{test_index["_id"]}/entries',
        json={
            'content': 'Test content',
            'keywords': ['test', 'note']
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['type'] == 'text'
    assert data['content'] == 'Test content'
    assert data['keywords'] == ['test', 'note']
    data = json.loads(response.data)
    assert data['type'] == 'text'
    assert data['content'] == 'Test content'
    assert 'test' in data['keywords']
    assert 'note' in data['keywords']

def test_create_file_entry(client, auth_headers, test_index):
    """Test creating a file entry"""
    from werkzeug.datastructures import FileStorage, MultiDict
    
    # Create test file
    test_file_content = b'Test file content'
    test_file = FileStorage(
        stream=io.BytesIO(test_file_content),
        filename='test.txt',
        content_type='text/plain'
    )
    
    # Create request data
    data = {
        'keywords': 'test,file',
        'file': test_file  # Add the file to the data dictionary
    }

    # Send POST request
    response = client.post(
        f'/api/indexes/{test_index["_id"]}/entries',
        data=data,
        headers=auth_headers,
        content_type='multipart/form-data'  # Ensure correct content type
    )
    
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}, Response: {response.data.decode()}"
    data = json.loads(response.data)
    assert data['type'] == 'file'
    assert 'metadata' in data
    assert data['metadata']['filename'] == 'test.txt'
    assert data['metadata']['content_type'] == 'text/plain'
    assert set(data['keywords']) == {'test', 'file'}

def test_create_entry_invalid_index(client, auth_headers):
    """Test creating entry with invalid index"""
    response = client.post(
        f'/api/indexes/{ObjectId()}/entries',
        json={'content': 'Test content'},
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_get_entries(client, auth_headers, test_index, db):
    """Test getting list of entries"""
    # Create some test entries
    entries = [
        {
            '_id': ObjectId(),
            'index_id': test_index['_id'],
            'user_id': test_index['user_id'],
            'type': 'text',
            'content': f'Test content {i}',
            'keywords': ['test'],
            'created_at': datetime.now(UTC)
        }
        for i in range(3)
    ]
    
    db.get_collection('entries').insert_many(entries)
    
    response = client.get(
        f'/api/indexes/{test_index["_id"]}/entries',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 3
    assert all('id' in entry and 'content' in entry for entry in data)
    # Verify we have all entries in the response
    contents = [entry['content'] for entry in data]
    assert all(f'Test content {i}' in contents for i in range(3))
    # Verify we have all entries in the response
    contents = [entry['content'] for entry in data]
    assert all(f'Test content {i}' in contents for i in range(3))

def test_get_entry(client, auth_headers, test_index, db):
    """Test getting a specific entry"""
    entry = {
        '_id': ObjectId(),
        'index_id': test_index['_id'],
        'user_id': test_index['user_id'],
        'type': 'text',
        'content': 'Test content',
        'keywords': ['test'],
        'created_at': datetime.now(UTC)
    }
    
    db.get_collection('entries').insert_one(entry)
    
    response = client.get(
        f'/api/indexes/{test_index["_id"]}/entries/{entry["_id"]}',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['content'] == entry['content']
    assert data['type'] == entry['type']

def test_delete_entry(client, auth_headers, test_index, db):
    """Test deleting an entry"""
    entry = {
        '_id': ObjectId(),
        'index_id': test_index['_id'],
        'user_id': test_index['user_id'],
        'type': 'text',
        'content': 'Test content',
        'keywords': ['test'],
        'created_at': datetime.now(UTC)
    }
    
    db.get_collection('entries').insert_one(entry)
    
    response = client.delete(
        f'/api/indexes/{test_index["_id"]}/entries/{entry["_id"]}',
        headers=auth_headers
    )
    
    assert response.status_code == 204
    assert not response.data  # No content for 204 response
    
    # Verify entry was deleted
    response = client.get(
        f'/api/indexes/{test_index["_id"]}/entries/{entry["_id"]}',
        headers=auth_headers
    )
    assert response.status_code == 404

def test_search_entries(client, auth_headers, test_index, db):
    """Test searching entries"""
    # Create test entries
    entries = [
        {
            '_id': ObjectId(),
            'index_id': test_index['_id'],
            'user_id': test_index['user_id'],
            'type': 'text',
            'content': 'Important meeting notes',
            'keywords': ['meeting', 'important'],
            'created_at': datetime.now(UTC)
        },
        {
            '_id': ObjectId(),
            'index_id': test_index['_id'],
            'user_id': test_index['user_id'],
            'type': 'text',
            'content': 'Shopping list',
            'keywords': ['shopping'],
            'created_at': datetime.now(UTC)
        }
    ]
    
    db.get_collection('entries').insert_many(entries)
    
    # Create text index
    db.get_collection('entries').create_index([('content', 'text'), ('keywords', 'text')])
    
    # Search for 'meeting'
    response = client.get(
        f'/api/indexes/{test_index["_id"]}/entries/search?q=meeting',
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'entries' in data
    assert len(data['entries']) == 1
    assert data['entries'][0]['content'] == 'Important meeting notes'
    assert set(data['entries'][0]['keywords']) == {'meeting', 'important'}

def test_unauthorized_access(client, test_index):
    """Test accessing entries without authentication"""
    # Try to list entries
    response = client.get(f'/api/indexes/{test_index["_id"]}/entries')
    assert response.status_code == 401
    assert 'msg' in response.json
    assert response.json['msg'] == 'Missing Authorization Header'
    
    # Try to create entry
    response = client.post(
        f'/api/indexes/{test_index["_id"]}/entries',
        json={'content': 'Test content'}
    )
    assert response.status_code == 401
    
    # Try to search entries
    response = client.get(f'/api/indexes/{test_index["_id"]}/entries/search?q=test')
    assert response.status_code == 401
    assert 'msg' in response.json
    assert response.json['msg'] == 'Missing Authorization Header'