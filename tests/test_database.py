import pytest
from datetime import datetime, UTC
from bson import ObjectId

from api.core.database import (
    DatabaseProvider,
    get_database,
    get_file_storage,
    DatabaseInterface,
    FileStorageInterface
)

def test_database_provider_initialization(app):
    """Test database provider initialization"""
    with app.app_context():
        db = get_database()
        assert isinstance(db, DatabaseInterface)
        
        fs = get_file_storage()
        assert isinstance(fs, FileStorageInterface)

def test_collection_operations(app, db):
    """Test basic collection operations"""
    with app.app_context():
        # Get test collection
        collection = db.get_collection('test_collection')
        
        # Test insert
        doc = {
            '_id': ObjectId(),
            'name': 'test',
            'created_at': datetime.now(UTC)
        }
        inserted_id = collection.insert_one(doc)
        assert inserted_id
        
        # Test find one
        found = collection.find_one({'name': 'test'})
        assert found
        assert found['name'] == 'test'
        
        # Test update
        updated = collection.update_one(
            {'_id': doc['_id']},
            {'name': 'updated'}
        )
        assert updated
        
        found = collection.find_one({'_id': doc['_id']})
        assert found['name'] == 'updated'
        
        # Test delete
        deleted = collection.delete_one({'_id': doc['_id']})
        assert deleted
        
        found = collection.find_one({'_id': doc['_id']})
        assert not found

def test_file_storage_operations(app, file_storage):
    """Test file storage operations"""
    with app.app_context():
        # Test file storage
        content = b'Test file content'
        filename = 'test.txt'
        content_type = 'text/plain'
        
        # Store file
        file_id = file_storage.store_file(content, filename, content_type)
        assert file_id
        
        # Retrieve file
        retrieved_content, retrieved_filename, retrieved_content_type = file_storage.get_file(file_id)
        assert retrieved_content == content
        assert retrieved_filename == filename
        assert retrieved_content_type == content_type
        
        # Delete file
        deleted = file_storage.delete_file(file_id)
        assert deleted
        
        # Verify file is deleted
        with pytest.raises(FileNotFoundError):
            file_storage.get_file(file_id)

def test_database_provider_reset(app):
    """Test database provider reset"""
    with app.app_context():
        # Get initial instances
        db1 = get_database()
        fs1 = get_file_storage()
        
        # Reset provider
        DatabaseProvider.reset()
        
        # Initialize again
        with pytest.raises(RuntimeError):
            # Should raise error because provider not initialized
            get_database()

def test_collection_pagination(app, db):
    """Test collection pagination and sorting"""
    with app.app_context():
        collection = db.get_collection('test_collection')
        
        # Insert test documents
        docs = [
            {'_id': ObjectId(), 'value': i, 'created_at': datetime.now(UTC)}
            for i in range(10)
        ]
        collection.insert_many(docs)
        
        # Test pagination
        results = collection.find_many(
            query={},
            sort=[('value', -1)],
            skip=2,
            limit=3
        )
        
        assert len(results) == 3
        assert [doc['value'] for doc in results] == [7, 6, 5]

def test_collection_count(app, db):
    """Test document counting"""
    with app.app_context():
        collection = db.get_collection('test_collection')
        
        # Insert test documents
        docs = [
            {'_id': ObjectId(), 'type': 'test', 'value': i}
            for i in range(5)
        ]
        collection.insert_many(docs)
        
        # Test count
        count = collection.count_documents({'type': 'test'})
        assert count == 5

def test_collection_indexes(app, db):
    """Test index operations"""
    with app.app_context():
        collection = db.get_collection('test_collection')
        
        # Clear collection first
        collection.delete_many({})
        
        # Create index
        index_name = collection.create_index(
            [('value', 1)],
            unique=True
        )
        assert index_name
        
        # Test unique constraint
        collection.insert_one({'value': 1})
        with pytest.raises(Exception):  # Should raise duplicate key error
            collection.insert_one({'value': 1})
        
        # Drop index
        collection.drop_index(index_name)
        
        # After dropping index, should be able to insert duplicate
        collection.insert_one({'value': 1})