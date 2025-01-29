from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId

from .database import CollectionInterface, get_database

class BaseModel:
    """Base model with common functionality"""
    collection_name: str = None
    
    @classmethod
    def get_collection(cls) -> CollectionInterface:
        if not cls.collection_name:
            raise ValueError("collection_name not set")
        return get_database().get_collection(cls.collection_name)

    @staticmethod
    def to_object_id(id_str: str) -> ObjectId:
        """Convert string ID to ObjectId"""
        try:
            return ObjectId(id_str)
        except:
            raise ValueError("Invalid ID format")

class User(BaseModel):
    """User model"""
    collection_name = 'users'
    
    def __init__(self, username: str, password_hash: str):
        self.username = username.lower()  # Store usernames in lowercase
        self.password_hash = password_hash
        self.created_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for storage"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at
        }
    
    @classmethod
    def find_by_username(cls, username: str) -> Optional[Dict]:
        """Find user by username (case insensitive)"""
        return cls.get_collection().find_one({
            'username': username.lower()
        })
    
    @classmethod
    def create(cls, username: str, password_hash: str) -> Dict:
        """Create a new user"""
        user = cls(username=username, password_hash=password_hash)
        data = user.to_dict()
        data['_id'] = ObjectId()
        cls.get_collection().insert_one(data)
        return data

class Index(BaseModel):
    """Index model"""
    collection_name = 'indexes'
    
    def __init__(self, user_id: ObjectId, name: str, description: str = ''):
        self.user_id = user_id
        self.name = name.strip()
        self.description = description.strip()
        self.created_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert index to dictionary for storage"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at
        }
    
    @classmethod
    def find_by_user(cls, user_id: ObjectId, skip: int = 0, limit: int = 0) -> List[Dict]:
        """Find all indexes for a user"""
        return cls.get_collection().find_many(
            {'user_id': user_id},
            sort=[('created_at', DESCENDING)],
            skip=skip,
            limit=limit
        )
    
    @classmethod
    def create(cls, user_id: ObjectId, name: str, description: str = '') -> Dict:
        """Create a new index"""
        index = cls(user_id=user_id, name=name, description=description)
        data = index.to_dict()
        data['_id'] = ObjectId()
        cls.get_collection().insert_one(data)
        return data

class Entry(BaseModel):
    """Entry model"""
    collection_name = 'entries'
    
    def __init__(self, index_id: ObjectId, user_id: ObjectId, type: str, 
                 content: Optional[str] = None, file_id: Optional[ObjectId] = None,
                 metadata: Optional[Dict] = None, keywords: Optional[List[str]] = None):
        self.index_id = index_id
        self.user_id = user_id
        self.type = type
        self.content = content.strip() if content else None
        self.file_id = file_id
        self.metadata = metadata or {}
        self.keywords = [k.strip().lower() for k in (keywords or [])]
        self.created_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for storage"""
        entry_dict = {
            'index_id': self.index_id,
            'user_id': self.user_id,
            'type': self.type,
            'metadata': self.metadata,
            'keywords': self.keywords,
            'created_at': self.created_at
        }
        if self.content is not None:
            entry_dict['content'] = self.content
        if self.file_id is not None:
            entry_dict['file_id'] = self.file_id
        return entry_dict
    
    @classmethod
    def find_by_index(cls, index_id: ObjectId, skip: int = 0, limit: int = 0) -> List[Dict]:
        """Find all entries in an index"""
        return cls.get_collection().find_many(
            {'index_id': index_id},
            sort=[('created_at', DESCENDING)],
            skip=skip,
            limit=limit
        )
    
    @classmethod
    def search(cls, index_id: ObjectId, query: str, skip: int = 0, limit: int = 0) -> List[Dict]:
        """Search entries in an index"""
        collection = cls.get_collection()
        return collection.find_many(
            {
                '$and': [
                    {'index_id': index_id},
                    {
                        '$or': [
                            {'$text': {'$search': query}},
                            {'keywords': {'$in': [query.lower()]}}
                        ]
                    }
                ]
            },
            sort=[('score', {'$meta': 'textScore'}), ('created_at', DESCENDING)],
            skip=skip,
            limit=limit
        )
    
    @classmethod
    def create(cls, index_id: ObjectId, user_id: ObjectId, type: str,
               content: Optional[str] = None, file_id: Optional[ObjectId] = None,
               metadata: Optional[Dict] = None, keywords: Optional[List[str]] = None) -> Dict:
        """Create a new entry"""
        entry = cls(
            index_id=index_id,
            user_id=user_id,
            type=type,
            content=content,
            file_id=file_id,
            metadata=metadata,
            keywords=keywords
        )
        data = entry.to_dict()
        data['_id'] = ObjectId()
        cls.get_collection().insert_one(data)
        return data