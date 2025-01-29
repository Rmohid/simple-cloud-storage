from flask import Flask
from flask_jwt_extended import JWTManager
from datetime import datetime, UTC

from api.core.database import init_database
from api.core.errors import register_error_handlers

def create_app(test_config=None):
    """Create and configure the app"""
    app = Flask(__name__)
    
    # Load default configuration
    app.config.from_mapping(
        MONGO_URI='mongodb://localhost:27017/',
        MONGO_DB_NAME='cloud_storage',
        SECRET_KEY='dev',
        JWT_SECRET_KEY='dev'
    )
    
    # Override with test config if passed
    if test_config is not None:
        app.config.update(test_config)
    
    # Initialize extensions
    jwt = JWTManager(app)
    
    # Configure simple JWT settings
    app.config.update(
        JWT_ALGORITHM='HS256',  # Simple symmetric algorithm
        JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 hour
        JWT_REFRESH_TOKEN_EXPIRES=86400,  # 24 hours
        JWT_ERROR_MESSAGE_KEY='msg'
    )
    
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        """Add basic claims to token"""
        return {
            'sub': str(identity),  # User ID
            'iat': datetime.now(UTC).timestamp()  # Issued at time
        }
    
    # Initialize database
    init_database(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Only register blueprints if not testing or explicitly requested
    if not app.config.get('TESTING') or test_config and test_config.get('REGISTER_BLUEPRINTS', True):
        # Register blueprints
        from api.auth import bp as auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        from api.indexes import bp as indexes_bp
        app.register_blueprint(indexes_bp, url_prefix='/api/indexes')
    
    return app