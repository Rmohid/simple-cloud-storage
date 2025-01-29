import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # MongoDB settings
    MONGO_URI = os.environ.get('MONGODB_URI')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME') or 'cloud_storage'
    
    # Collections
    USERS_COLLECTION = 'users'
    INDEXES_COLLECTION = 'indexes'
    ENTRIES_COLLECTION = 'entries'
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {
        'text': {'txt', 'md', 'pdf', 'doc', 'docx'},
        'image': {'png', 'jpg', 'jpeg', 'gif'},
        'audio': {'mp3', 'wav', 'ogg'},
        'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    }

    def __init__(self):
        if not self.MONGO_URI:
            raise ValueError("MONGODB_URI environment variable is not set")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    MONGO_DB_NAME = 'cloud_storage_test'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        super().__init__()
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY environment variable is not set")
        if not os.environ.get('JWT_SECRET_KEY'):
            raise ValueError("JWT_SECRET_KEY environment variable is not set")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}