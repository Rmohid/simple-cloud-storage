import pytest
from bson.objectid import ObjectId
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC

from api import create_app
from api.core.database import DatabaseProvider, get_database, get_file_storage

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'MONGO_URI': 'mongodb://localhost:27017/',
        'MONGO_DB_NAME': 'cloud_storage_test',
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'REGISTER_BLUEPRINTS': True
    })

    with app.app_context():
        # Initialize database for testing
        from api.core.database.factory import init_database
        init_database(app)
        db = get_database()
        db.connect()
    
    # Clean up after all tests
    yield app
    
    with app.app_context():
        try:
            db = get_database()
            # Drop test database
            db.get_collection('users').delete_many({})
            db.get_collection('indexes').delete_many({})
            db.get_collection('entries').delete_many({})
        except:
            pass
        finally:
            DatabaseProvider.reset()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def db(app):
    """Get test database"""
    with app.app_context():
        db = get_database()
        db.connect()  # Ensure database is connected
        # Clear database before each test
        for collection in ['users', 'indexes', 'entries']:
            db.get_collection(collection).delete_many({})
        yield db

@pytest.fixture
def file_storage(app, db):
    """Get file storage instance"""
    with app.app_context():
        fs = get_file_storage()
        yield fs

@pytest.fixture
def test_user(db, app):
    """Create test user"""
    with app.app_context():
        user_data = {
            '_id': ObjectId(),
            'username': 'testuser',
            'password_hash': generate_password_hash('testpass'),
            'created_at': datetime.now(UTC)
        }
        users = db.get_collection('users')
        users.insert_one(user_data)
        return user_data

@pytest.fixture
def auth_headers(app, test_user):
    """Create authentication headers"""
    with app.app_context():
        access_token = create_access_token(identity=str(test_user['_id']))
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def test_index(db, test_user, app):
    """Create test index"""
    with app.app_context():
        index_data = {
            '_id': ObjectId(),
            'user_id': test_user['_id'],
            'name': 'Test Index',
            'description': 'Test Description',
            'created_at': datetime.now(UTC)
        }
        indexes = db.get_collection('indexes')
        indexes.insert_one(index_data)
        return index_data