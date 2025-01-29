from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')

class DatabaseInterface(ABC):
    """Base interface for database operations"""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def get_collection(self, name: str) -> 'CollectionInterface':
        """Get a collection by name"""
        pass

class CollectionInterface(ABC, Generic[T]):
    """Base interface for collection operations"""
    
    @abstractmethod
    def find_one(self, query: Dict) -> Optional[T]:
        """Find a single document"""
        pass
    
    @abstractmethod
    def find_many(self, query: Dict, sort: Optional[List] = None, 
                 skip: int = 0, limit: int = 0) -> List[T]:
        """Find multiple documents"""
        pass
    
    @abstractmethod
    def insert_one(self, document: Dict) -> str:
        """Insert a single document"""
        pass
    
    @abstractmethod
    def insert_many(self, documents: List[Dict]) -> List[str]:
        """Insert multiple documents"""
        pass
    
    @abstractmethod
    def update_one(self, query: Dict, update: Dict) -> bool:
        """Update a single document"""
        pass
    
    @abstractmethod
    def update_many(self, query: Dict, update: Dict) -> int:
        """Update multiple documents"""
        pass
    
    @abstractmethod
    def delete_one(self, query: Dict) -> bool:
        """Delete a single document"""
        pass
    
    @abstractmethod
    def delete_many(self, query: Dict) -> int:
        """Delete multiple documents"""
        pass
    
    @abstractmethod
    def count_documents(self, query: Dict) -> int:
        """Count documents matching query"""
        pass
    
    @abstractmethod
    def create_index(self, keys: List[tuple], unique: bool = False) -> str:
        """Create an index"""
        pass
    
    @abstractmethod
    def drop_index(self, index_name: str) -> None:
        """Drop an index"""
        pass

class FileStorageInterface(ABC):
    """Base interface for file storage operations"""
    
    @abstractmethod
    def store_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Store a file and return its ID"""
        pass
    
    @abstractmethod
    def get_file(self, file_id: str) -> tuple[bytes, str, str]:
        """Get file data, filename, and content type"""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete a file"""
        pass

class DatabaseFactory(ABC):
    """Factory interface for creating database instances"""
    
    @abstractmethod
    def create_database(self) -> DatabaseInterface:
        """Create a database instance"""
        pass
    
    @abstractmethod
    def create_file_storage(self) -> FileStorageInterface:
        """Create a file storage instance"""
        pass