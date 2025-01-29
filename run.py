import os
from dotenv import load_dotenv
from api import create_app

# Load environment variables from .env file
load_dotenv()

# Get environment
env = os.environ.get('FLASK_ENV', 'development')

# Create app instance
app = create_app()

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=env == 'development'
    )