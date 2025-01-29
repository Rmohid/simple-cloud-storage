from flask import current_app, g
from pymongo import MongoClient
from gridfs import GridFS
from typing import Optional

def get_db():
    """Get database connection"""
    if 'db' not in g:
        client = MongoClient(current_app.config['MONGO_URI'])
        g.db = client[current_app.config['MONGO_DB_NAME']]
    return g.db

def get_gridfs() -> Optional[GridFS]:
    """Get GridFS instance"""
    if 'gridfs' not in g:
        db = get_db()
        g.gridfs = GridFS(db, collection=current_app.config['GRIDFS_COLLECTION'])
    return g.gridfs

def init_db(app):
    """Initialize database connection and create indexes"""
    with app.app_context():
        db = get_db()
        
        # Create indexes for users collection
        db[app.config['USERS_COLLECTION']].create_index('username', unique=True)
        
        # Create indexes for indexes collection
        db[app.config['INDEXES_COLLECTION']].create_index([
            ('user_id', 1),
            ('name', 1)
        ], unique=True)
        
        # Create indexes for entries collection
        db[app.config['ENTRIES_COLLECTION']].create_index([
            ('index_id', 1),
            ('created_at', -1)
        ])
        db[app.config['ENTRIES_COLLECTION']].create_index([
            ('user_id', 1),
            ('keywords', 1)
        ])
        
        # Create text index for search
        db[app.config['ENTRIES_COLLECTION']].create_index([
            ('content', 'text'),
            ('keywords', 'text')
        ])

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.client.close()

def init_app(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db)