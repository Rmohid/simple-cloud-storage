from typing import Any, Dict, List, Optional, TypeVar, Generic
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from gridfs import GridFS
from bson.objectid import ObjectId
import io

from .interface import (
    DatabaseInterface,
    CollectionInterface,
    FileStorageInterface,
    DatabaseFactory
)

T = TypeVar('T')

class MongoDBCollection(CollectionInterface[T]):
    """MongoDB implementation of CollectionInterface"""
    
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def find_one(self, query: Dict) -> Optional[T]:
        return self.collection.find_one(query)
    
    def find_many(self, query: Dict, sort: Optional[List] = None,
                 skip: int = 0, limit: int = 0) -> List[T]:
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    
    def insert_one(self, document: Dict) -> str:
        if '_id' not in document:
            document['_id'] = ObjectId()
        result = self.collection.insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, documents: List[Dict]) -> List[str]:
        for doc in documents:
            if '_id' not in doc:
                doc['_id'] = ObjectId()
        result = self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    def update_one(self, query: Dict, update: Dict) -> bool:
        if '$set' in update:
            result = self.collection.update_one(query, update)
        else:
            result = self.collection.update_one(query, {'$set': update})
        return result.modified_count > 0
    
    def update_many(self, query: Dict, update: Dict) -> int:
        result = self.collection.update_many(query, {'$set': update})
        return result.modified_count
    
    def delete_one(self, query: Dict) -> bool:
        result = self.collection.delete_one(query)
        return result.deleted_count > 0
    
    def delete_many(self, query: Dict) -> int:
        result = self.collection.delete_many(query)
        return result.deleted_count
    
    def count_documents(self, query: Dict) -> int:
        return self.collection.count_documents(query)
    
    def create_index(self, keys: List[tuple], unique: bool = False) -> str:
        return self.collection.create_index(keys, unique=unique)
    
    def drop_index(self, index_name: str) -> None:
        self.collection.drop_index(index_name)

class MongoDBFileStorage(FileStorageInterface):
    """MongoDB GridFS implementation of FileStorageInterface"""
    
    def __init__(self, database: Database):
        self.database = database
        self._fs = None
    
    @property
    def fs(self) -> GridFS:
        """Lazy initialization of GridFS"""
        if self._fs is None:
            self._fs = GridFS(self.database)
        return self._fs
    
    def store_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        file_id = self.fs.put(
            file_data,
            filename=filename,
            content_type=content_type
        )
        return str(file_id)
    
    def get_file(self, file_id: str) -> tuple[bytes, str, str]:
        obj_id = ObjectId(file_id)
        if not self.fs.exists(obj_id):
            raise FileNotFoundError(f"File {file_id} not found")
        
        grid_out = self.fs.get(obj_id)
        return (
            grid_out.read(),
            grid_out.filename,
            grid_out.content_type
        )
    
    def delete_file(self, file_id: str) -> bool:
        obj_id = ObjectId(file_id)
        if not self.fs.exists(obj_id):
            return False
        self.fs.delete(obj_id)
        return True

class MongoDB(DatabaseInterface):
    """MongoDB implementation of DatabaseInterface"""
    
    def __init__(self, uri: str, database_name: str):
        self.uri = uri
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._file_storage: Optional[MongoDBFileStorage] = None
    
    def connect(self) -> None:
        if not self.client:
            self.client = MongoClient(self.uri)
            self._db = self.client[self.database_name]
            self._file_storage = MongoDBFileStorage(self._db)
    
    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self._db = None
            self._file_storage = None
    
    def get_collection(self, name: str) -> CollectionInterface:
        if self._db is None:
            raise RuntimeError("Database not connected")
        return MongoDBCollection(self._db[name])

class MongoDBFactory(DatabaseFactory):
    """Factory for creating MongoDB instances"""
    
    def __init__(self, uri: str, database_name: str):
        self.uri = uri
        self.database_name = database_name
        self._db_instance: Optional[MongoDB] = None
    
    def create_database(self) -> DatabaseInterface:
        if not self._db_instance or self._db_instance._db is None:
            if self._db_instance:
                self._db_instance.disconnect()
            self._db_instance = MongoDB(self.uri, self.database_name)
            self._db_instance.connect()
        return self._db_instance
    
    def create_file_storage(self) -> FileStorageInterface:
        db = self.create_database()
        if not isinstance(db, MongoDB) or db._db is None:
            raise RuntimeError("Database not properly initialized")
        return db._file_storage