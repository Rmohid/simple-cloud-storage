import pytest
from flask import json
from bson import ObjectId
from datetime import datetime, UTC

def test_create_index(client, auth_headers):
    """Test creating a new index"""
    response = client.post('/api/indexes/', json={
        'name': 'Work Notes',
        'description': 'Notes from work meetings'
    }, headers=auth_headers)
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['name'] == 'Work Notes'
    assert data['description'] == 'Notes from work meetings'

def test_create_index_missing_name(client, auth_headers):
    """Test creating index without name"""
    response = client.post('/api/indexes/', json={
        'description': 'Test description'
    }, headers=auth_headers)
    
    assert response.status_code == 400

def test_create_duplicate_index(client, auth_headers, test_index):
    """Test creating index with duplicate name"""
    response = client.post('/api/indexes', json={
        'name': test_index['name'],
        'description': 'Another description'
    }, headers=auth_headers)
    
    assert response.status_code == 400
    assert 'msg' in response.json
    assert response.json['msg'] == 'Index with this name already exists'
    
    assert response.status_code == 400

def test_get_indexes(client, auth_headers, test_index, db):
    """Test getting list of indexes"""
    # Create another index
    db.get_collection('indexes').insert_one({
        '_id': ObjectId(),
        'user_id': test_index['user_id'],
        'name': 'Another Index',
        'description': 'Another Description',
        'created_at': datetime.now(UTC)
    })
    
    response = client.get('/api/indexes/', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 2
    assert all('id' in index and 'name' in index for index in data)
    assert len(data) == 2
    assert all(isinstance(index, dict) for index in data)
    assert all('id' in index and 'name' in index and 'description' in index for index in data)
    # Verify we have both indexes in the response
    names = [index['name'] for index in data]
    assert 'Test Index' in names
    assert 'Another Index' in names

def test_get_index(client, auth_headers, test_index):
    """Test getting a specific index"""
    response = client.get(f'/api/indexes/{test_index["_id"]}', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['id'] == str(test_index['_id'])
    assert data['name'] == test_index['name']
    assert data['description'] == test_index['description']

def test_get_nonexistent_index(client, auth_headers):
    """Test getting a nonexistent index"""
    response = client.get(f'/api/indexes/{ObjectId()}', headers=auth_headers)
    assert response.status_code == 404

def test_update_index(client, auth_headers, test_index):
    """Test updating an index"""
    response = client.put(
        f'/api/indexes/{test_index["_id"]}',
        json={
            'name': 'Updated Name',
            'description': 'Updated Description'
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Updated Name'
    assert data['description'] == 'Updated Description'

def test_update_index_duplicate_name(client, auth_headers, test_index, db):
    """Test updating index with duplicate name"""
    # Create another index
    db.get_collection('indexes').insert_one({
        '_id': ObjectId(),
        'user_id': test_index['user_id'],
        'name': 'Existing Name',
        'description': 'Another Description',
        'created_at': datetime.now(UTC)
    })
    
    response = client.put(
        f'/api/indexes/{test_index["_id"]}',
        json={'name': 'Existing Name'},
        headers=auth_headers
    )
    
    assert response.status_code == 400

def test_delete_index(client, auth_headers, test_index):
    """Test deleting an index"""
    response = client.delete(
        f'/api/indexes/{test_index["_id"]}',
        headers=auth_headers
    )
    
    assert response.status_code == 204
    assert not response.data  # No content for 204 response
    
    # Verify index was deleted
    response = client.get(
        f'/api/indexes/{test_index["_id"]}',
        headers=auth_headers
    )
    assert response.status_code == 404

def test_unauthorized_access(client, test_index):
    """Test accessing indexes without authentication"""
    # Try to list indexes
    response = client.get('/api/indexes/')
    assert response.status_code == 401
    
    # Try to create index
    response = client.post('/api/indexes/', json={
        'name': 'Test Index',
        'description': 'Test Description'
    })
    assert response.status_code == 401
    
    # Try to get specific index
    response = client.get(f'/api/indexes/{test_index["_id"]}')
    assert response.status_code == 401
    
    # Try to update index
    response = client.put(f'/api/indexes/{test_index["_id"]}', json={
        'name': 'Updated Name'
    })
    assert response.status_code == 401
    
    # Try to delete index
    response = client.delete(f'/api/indexes/{test_index["_id"]}')
    assert response.status_code == 401