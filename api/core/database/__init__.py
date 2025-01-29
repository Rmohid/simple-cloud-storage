from .interface import (
    DatabaseInterface,
    CollectionInterface,
    FileStorageInterface,
    DatabaseFactory
)

from .factory import (
    DatabaseProvider,
    get_database as get_db,  # Alias for backward compatibility
    get_database,
    get_file_storage,
    init_database
)

__all__ = [
    'DatabaseInterface',
    'CollectionInterface',
    'FileStorageInterface',
    'DatabaseFactory',
    'DatabaseProvider',
    'get_db',
    'get_database',
    'get_file_storage',
    'init_database'
]