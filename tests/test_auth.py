from datetime import datetime, UTC
from werkzeug.security import generate_password_hash

def test_register_success(client, db):
    """Test successful user registration"""
    response = client.post('/auth/register', json={
        'username': 'newuser',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json
    assert 'user' in response.json
    assert response.json['user']['username'] == 'newuser'

def test_register_missing_fields(client):
    """Test registration with missing fields"""
    # Missing password
    response = client.post('/auth/register', json={
        'username': 'newuser'
    })
    assert response.status_code == 400
    assert 'msg' in response.json
    
    # Missing username
    response = client.post('/auth/register', json={
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'msg' in response.json

def test_register_invalid_username(client):
    """Test registration with invalid username"""
    response = client.post('/auth/register', json={
        'username': 'a',  # Too short
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'msg' in response.json
    assert response.json['msg'] == 'Username must be at least 3 characters long'

def test_register_duplicate_username(client, test_user):
    """Test registration with existing username"""
    response = client.post('/auth/register', json={
        'username': test_user['username'],
        'password': 'password123'
    })
    assert response.status_code == 400
    assert 'msg' in response.json
    assert response.json['msg'] == 'Username already exists'

def test_login_success(client, test_user):
    """Test successful login"""
    response = client.post('/auth/login', json={
        'username': test_user['username'],
        'password': 'testpass'
    })
    
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json
    assert 'user' in response.json
    assert response.json['user']['username'] == test_user['username']

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    # Wrong password
    response = client.post('/auth/login', json={
        'username': test_user['username'],
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    assert 'msg' in response.json
    assert response.json['msg'] == 'Invalid username or password'

    # Wrong username
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'testpass'
    })
    assert response.status_code == 401
    assert 'msg' in response.json
    assert response.json['msg'] == 'Invalid username or password'

def test_refresh_token(client, auth_headers):
    """Test token refresh"""
    response = client.post('/auth/refresh', headers=auth_headers)
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'refresh_token' in response.json

def test_get_current_user(client, auth_headers, test_user):
    """Test getting current user info"""
    response = client.get('/auth/me', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['id'] == str(test_user['_id'])
    assert response.json['username'] == test_user['username']

def test_unauthorized_access(client):
    """Test accessing protected endpoint without token"""
    response = client.get('/auth/me')
    assert response.status_code == 401
    assert 'msg' in response.json
    assert response.json['msg'] == 'Missing Authorization Header'