from typing import Optional, Type
from flask import current_app

from .interface import DatabaseFactory, DatabaseInterface, FileStorageInterface
from .mongodb import MongoDBFactory

class DatabaseProvider:
    """Singleton provider for database factory"""
    _instance: Optional[DatabaseFactory] = None
    _initialized: bool = False
    
    @classmethod
    def initialize(cls, factory_class: Type[DatabaseFactory], **kwargs) -> None:
        """Initialize the database factory"""
        # Reset if already initialized in test environment
        if current_app and current_app.config.get('TESTING'):
            cls.reset()
        
        # Create new instance
        if not cls._initialized:
            cls._instance = factory_class(**kwargs)
            cls._initialized = True
    
    @classmethod
    def get_factory(cls) -> DatabaseFactory:
        """Get the database factory instance"""
        if not cls._initialized:
            raise RuntimeError("DatabaseProvider not initialized")
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the provider (mainly for testing)"""
        if cls._instance:
            try:
                db = cls._instance.create_database()
                db.disconnect()
            except:
                pass
        cls._instance = None
        cls._initialized = False

def get_database() -> DatabaseInterface:
    """Get the database instance"""
    return DatabaseProvider.get_factory().create_database()

def get_file_storage() -> FileStorageInterface:
    """Get the file storage instance"""
    return DatabaseProvider.get_factory().create_file_storage()

def init_database(app) -> None:
    """Initialize database with Flask app"""
    # Initialize database factory based on configuration
    DatabaseProvider.initialize(
        MongoDBFactory,
        uri=app.config['MONGO_URI'],
        database_name=app.config['MONGO_DB_NAME']
    )
    
    # Get database instance
    db = get_database()
    
    # Create indexes
    users = db.get_collection('users')
    users.create_index([('username', 1)], unique=True)
    
    indexes = db.get_collection('indexes')
    indexes.create_index([
        ('user_id', 1),
        ('name', 1)
    ], unique=True)
    
    entries = db.get_collection('entries')
    entries.create_index([
        ('index_id', 1),
        ('created_at', -1)
    ])
    entries.create_index([
        ('user_id', 1),
        ('keywords', 1)
    ])
    entries.create_index([
        ('content', 'text'),
        ('keywords', 'text')
    ])
    
    # Register teardown
    app.teardown_appcontext(lambda exc: db.disconnect())