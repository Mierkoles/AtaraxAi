# AtaraxAi

A modern Python web application built with FastAPI, SQLAlchemy, and designed for deployment on Azure Web Apps.

## Features

- **FastAPI Framework**: High-performance, easy to use, fast to code
- **SQLAlchemy ORM**: Database abstraction with support for SQLite and Azure SQL
- **Repository Pattern**: Clean separation of data access logic
- **Pydantic Schemas**: Data validation and serialization
- **Azure Ready**: Configured for Azure Web Apps deployment
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Clean Architecture**: Organized codebase following best practices

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: SQLAlchemy (SQLite for development, Azure SQL for production)
- **Validation**: Pydantic
- **Testing**: pytest, httpx
- **Code Quality**: Black, isort, flake8, mypy
- **Deployment**: Azure Web Apps
- **CI/CD**: GitHub Actions

## Project Structure

```
AtaraxAi/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base_class.py
│   │   └── database.py
│   ├── models/
│   │   └── user.py
│   ├── repositories/
│   │   ├── base.py
│   │   └── user.py
│   └── schemas/
│       └── user.py
├── tests/
├── .github/
│   └── workflows/
├── main.py
├── requirements.txt
└── README.md
```

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/mierkoles/AtaraxAi.git
   cd AtaraxAi
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp env.example .env
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```env
# Database Configuration
DATABASE_URL=sqlite:///./atarax.db

# Application Settings
APP_NAME=AtaraxAi
APP_VERSION=1.0.0
DEBUG=true
SECRET_KEY=your-secret-key-here

# Azure Configuration (for production)
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
```

### Database Migration

The application automatically creates tables on startup. For production deployments with schema changes, consider using Alembic:

```bash
# Initialize Alembic (one time)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add user table"

# Apply migration
alembic upgrade head
```

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## Azure Deployment

### Prerequisites

1. Azure Web App instance
2. Azure SQL Database (optional, for production)
3. GitHub repository secrets configured

### GitHub Secrets

Configure the following secrets in your GitHub repository:

- `AZURE_WEBAPP_NAME`: Your Azure Web App name
- `AZURE_WEBAPP_PUBLISH_PROFILE`: Download from Azure Portal

### Deployment Process

1. Push to `main` branch triggers automatic deployment
2. GitHub Actions runs tests and linting
3. Application is deployed to Azure Web Apps
4. Database migrations run automatically

## API Endpoints

### Users

- `GET /api/v1/users/` - List all users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users/email/{email}` - Get user by email

### System

- `GET /` - Root endpoint
- `GET /health` - Health check

## Development

### Adding New Features

1. **Create Model**: Add to `app/models/`
2. **Create Schema**: Add to `app/schemas/`
3. **Create Repository**: Add to `app/repositories/`
4. **Create Endpoints**: Add to `app/api/v1/endpoints/`
5. **Update Router**: Include in `app/api/v1/api.py`
6. **Add Tests**: Create in `tests/`

### Database Changes

When working with database schema changes:

1. Update model in `app/models/`
2. Update schema in `app/schemas/`
3. Update repository methods if needed
4. Consider migration strategy for production

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Run code quality checks: `black`, `isort`, `flake8`, `mypy`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue in the GitHub repository.
