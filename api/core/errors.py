class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found"""
    pass

from flask import jsonify
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import NotFound

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        return jsonify({'error': str(error)}), 400
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors"""
        return jsonify({'error': str(error)}), 401
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_not_found_error(error):
        """Handle not found errors"""
        return jsonify({'error': str(error)}), 404
        
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(error):
        """Handle JWT errors"""
        return jsonify({'error': str(error)}), 401
        
    @app.errorhandler(404)
    def handle_404_error(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Resource not found'}), 404