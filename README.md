# Abjad Advertisement Backend API

## Overview
The Abjad Advertisement Backend API is designed to manage advertisements, track events, and handle user management. It provides functionalities for advertisers to create and manage ads, track user interactions, and efficiently manage user accounts.

## How It's Built
The API is built using the following technologies and frameworks:

- **FastAPI**: A modern web framework for building APIs with Python 3.6+ based on standard Python type hints.
- **SQLAlchemy**: An ORM (Object Relational Mapper) that allows for database interactions using Python objects.
- **PostgreSQL**: A powerful, open-source relational database system used for storing data.
- **Docker**: Used for containerization, allowing the application to run in isolated environments.
- **Husky**: Git hooks management for consistent code quality.
- **Various Linters**: Ruff, Black, isort, Flake8, and Pylint for code quality.

## Prerequisites

### 1. Python Setup
- Install Python 3.12.5 or later:
  - **Windows**: Download from [Python.org](https://www.python.org/downloads/)
  - **macOS**: `brew install python@3.12`
  - **Linux**: `sudo apt-get install python3.12`

### 2. Docker Setup
- Install Docker and Docker Compose:
  - **Windows/macOS**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
  - **Linux**:
    ```bash
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

    # Install Docker Compose
    sudo apt-get install docker-compose
    ```

### 3. Node.js Setup (for Husky)
- Install Node.js 18 or later:
  - **All Platforms**: Download from [Node.js website](https://nodejs.org/)
  - **Using nvm**:
    ```bash
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    nvm install 18
    nvm use 18
    ```

## Project Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Abjad-Advertiser/Abjad-Advertiser-Backend.git
cd Abjad-Advertiser-Backend
```


### 2. Set Up Python Virtual Environment
```bash
# Windows
python -m venv .venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source venv/bin/activate
```

#### Install Python dependencies
```bash
# Windows
pip install -r requirements.txt

# macOS/Linux
pip3 install -r requirements.txt
```

### 3. Set Up Node.js Dependencies
```bash
npm install
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
PORT=8000
DATABASE_URL=postgresql+asyncpg://<username>:<password>@postgres_db:5432/abjad_advertiser_db
SECRET_KEY=<your-secret-key>
ALGORITHM=<your-algorithm>
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=True
```

### 5. Set Up Git Hooks
Husky will automatically set up git hooks after npm install. These hooks will:
- Run Python linters (Black, isort, Flake8, Pylint) before commits
- Validate commit messages
- Run tests before pushing

## Running the Application

### Using Docker (Highly Recommended)

#### Build and start containers

```bash
docker compose up --build
```

#### Stop containers

```bash
docker compose down
```

#### Start PostgreSQL container only
```bash
docker compose up -d postgres_db
```


### Run the FastAPI application
```bash
# Windows
python main.py

# macOS/Linux
python3 main.py
```

## Development Tools

### Code Formatting
The project uses several tools for code quality:

- **Black**: For Python code formatting.
- **isort**: For sorting imports.
- **Ruff**: For Python linting.
- **Pylint**: For Python linting.
- **Flake8**: For Python linting.

### Running Tests & Writing tests
To run existing tests:
```bash
pytest
```

It's highly recommended to write tests for new features in test files in the `tests` directory.


## API Documentation
Once the application is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## Database Management
The project uses SQLAlchemy to interact with the database. The database schema is defined in the `models` directory.

To create the database and tables, run:
```bash
# ! Not tested, but should work
alembic init alembic
alembic migrate
alembic upgrade head
```

### Restart containers
```bash
docker compose down
docker compose up --build
```


## Troubleshooting

### Common Issues
1. **Port Conflicts**: If port 8000 is in use, modify the `PORT` in `.env`
2. **Database Connection**: Ensure PostgreSQL container is running before starting the application
3. **Permission Issues**: 
   - Windows: Run PowerShell as Administrator
   - Linux/macOS: Use `sudo` for Docker commands if needed

### Logs
- Application logs: `logs/adserver.log`
- Docker logs: `docker-compose logs`

## Contributing
1. Ensure all tests pass: `pytest`
2. Format code: `black . && isort .`
3. Run linters: `flake8 . && pylint app/`
4. Follow conventional commits specification
5. Submit a pull request in new branch if needed
