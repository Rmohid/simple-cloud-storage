# Simple Cloud Storage

[![Test](https://github.com/Rmohid/simple-cloud-storage/actions/workflows/test.yml/badge.svg)](https://github.com/Rmohid/simple-cloud-storage/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/Rmohid/simple-cloud-storage/branch/main/graph/badge.svg)](https://codecov.io/gh/Rmohid/simple-cloud-storage)

A cloud-based service that provides an API to store and organize different types of data including text, images, sounds, and documents under customizable indexes.

## Status

- **CI/CD**: GitHub Actions automatically runs tests and linting on every push and pull request
- **Test Coverage**: Code coverage reports are automatically generated and uploaded to Codecov

## Features

- User authentication with JWT
- Create and manage indexes to organize data
- Store different types of content:
  - Text notes
  - Files (images, documents, etc.)
  - Support for file type detection
- Search functionality within indexes
- RESTful API design

## Prerequisites

### System Dependencies

- Python 3.12+
- MongoDB 6.0+
- libmagic (for file type detection)
- Docker and Docker Compose (optional, for containerized setup)

#### macOS

```bash
# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community

# Install libmagic
brew install libmagic
```

#### Linux (Ubuntu/Debian)

```bash
# Install MongoDB
sudo apt-get install -y mongodb

# Install libmagic
sudo apt-get install -y libmagic1
```

### Python Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Configuration options:
- `MONGO_URI`: MongoDB connection URI
- `MONGO_DB_NAME`: Database name
- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key

## Docker Setup

Run the application using Docker:

```bash
# Build and start services
docker-compose up --build

# Stop services
docker-compose down
```

For running tests in Docker:

```bash
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Development

### Local Development

Start the development server:

```bash
python run.py
```

### Testing

Set up the test environment:

```bash
# Copy test environment configuration
cp .env.example .env.test

# Update test configuration values in .env.test:
# - MONGO_DB_NAME should end with "_test"
# - Use different SECRET_KEY and JWT_SECRET_KEY from development
```

Run tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_entries.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=api tests/
```

Test files are organized by feature:
- `test_auth.py`: Authentication tests
- `test_indexes.py`: Index management tests
- `test_entries.py`: Entry storage and retrieval tests
- `test_database.py`: Database operations tests

## API Documentation

### Authentication

- `POST /auth/register`: Register new user
- `POST /auth/login`: Login and get JWT tokens
- `POST /auth/refresh`: Refresh access token
- `GET /auth/me`: Get current user info

### Indexes

- `POST /indexes/`: Create new index
- `GET /indexes/`: List all indexes
- `GET /indexes/<id>`: Get specific index
- `PUT /indexes/<id>`: Update index
- `DELETE /indexes/<id>`: Delete index

### Entries

- `POST /entries/`: Create new entry (text or file)
- `GET /entries/?index_id=<id>`: List entries in index
- `GET /entries/<id>`: Get specific entry
- `DELETE /entries/<id>`: Delete entry
- `GET /entries/search?index_id=<id>&q=<query>`: Search entries

## Project Structure

```
cloud-storage-service/
├── api/
│   ├── auth/           # Authentication routes
│   ├── indexes/        # Index management
│   ├── entries/        # Entry storage and retrieval
│   └── core/           # Core functionality
├── tests/              # Test suite
└── run.py             # Application entry point
```

## License

MIT License