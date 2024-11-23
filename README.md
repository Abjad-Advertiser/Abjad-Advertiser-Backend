# Abjad Advertisement Backend API

## Overview
The Abjad Advertisement Backend API is designed to manage advertisements, track events, and handle user management. It provides functionalities for advertisers to create and manage ads, track user interactions, and efficiently manage user accounts.

## How It's Built
The API is built using the following technologies and frameworks:

- **FastAPI**: A modern web framework for building APIs with Python 3.6+ based on standard Python type hints.
- **SQLAlchemy**: An ORM (Object Relational Mapper) that allows for database interactions using Python objects.
- **PostgreSQL**: A powerful, open-source relational database system used for storing data.
- **Docker**: Used for containerization, allowing the application to run in isolated environments.

## Running the Application

### Prerequisites
1. **Docker**: Ensure you have Docker installed on your machine.
2. **Docker Compose**: This is included with Docker Desktop installations.

### Steps to Run
1. **Clone the Repository**: 
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up Environment Variables**: Create a `.env` file in the root directory of the project. You can use the following template:
   ```
   PORT=8000
   DATABASE_URL=postgresql+asyncpg://<username>:<password>@postgres_db:5432/abjad_advertiser_db
   SECRET_KEY=<your-secret-key>
   ALGORITHM=<your-algorithm>
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   DEBUG=True
   ```

3. **Build and Run the Containers**:
   ```bash
   docker-compose up --build
   ```

4. **Access the API**: Once the containers are running, you can access the API at `http://localhost:8000`.

### Database Setup
The application uses PostgreSQL as its database. The database schema is created automatically when the application starts, thanks to SQLAlchemy's `Base.metadata.create_all()` method, which is called during the application lifecycle.

### API Endpoints
The API provides various endpoints for user management, advertisement management, and event tracking. You can explore the available routes by accessing the FastAPI documentation at `http://localhost:8000/docs`.
