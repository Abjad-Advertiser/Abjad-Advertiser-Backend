<div align="center">

# 🎯 Abjad Advertisement Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

---

<p align="center">
  <b>🚀 A Modern Advertisement Management Platform</b><br>
  Built with FastAPI, PostgreSQL, and ❤️
</p>

[Features](#-key-features) •
[Installation](#-quick-start) •
[Documentation](#-api-documentation) •
[Contributing](#-contributing) •
[Support](#-need-help)

</div>

## 🌟 Overview
<div align="center">
<i>Welcome to the Abjad Advertisement Backend API! This powerful platform helps businesses reach their audience effectively through smart advertisement management. Whether you're looking to create engaging ads, track user interactions, or manage accounts seamlessly, we've got you covered!</i>
</div>

## ✨ Key Features
<div align="center">

| Feature | Description |
|---------|-------------|
| 📊 **Ad Management** | Create, update, and track advertisement campaigns |
| 👥 **User Management** | Secure user authentication and authorization |
| 📈 **Analytics** | Comprehensive tracking and reporting |
| 💳 **Billing** | Integrated payment and subscription handling |
| 🔒 **Security** | Enterprise-grade security measures |

</div>

## 🛠️ Tech Stack
<div align="center">

| Technology | Purpose |
|------------|---------|
| 🚀 **FastAPI** | Lightning-fast API development |
| 🎲 **SQLAlchemy** | Database ORM |
| 🐘 **PostgreSQL** | Database |
| 🐳 **Docker** | Containerization |
| 🐶 **Husky** | Git hooks |
| ✨ **Code Quality** | Black, isort, Ruff, Pylint |

</div>

## 📋 Prerequisites

<details>
<summary>🐍 Python Setup</summary>

```bash
# 💻 Windows
Download from python.org

# 🍎 macOS
brew install python@3.12

# 🐧 Linux
sudo apt-get install python3.12
```
</details>

<details>
<summary>🐳 Docker Setup</summary>

```bash
# 💻 Windows/macOS
Install Docker Desktop

# 🐧 Linux
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose
```
</details>

<details>
<summary>📦 Node.js and npm Setup (Required for Development)</summary>

> **Why Node.js?** We use Node.js and npm for development tools:
> - **Husky**: Git hooks that run before commits to ensure code quality
> - **lint-staged**: Runs linters on staged files
> - **commitlint**: Enforces conventional commit messages
>
> These tools help maintain code quality and consistent commit messages across the project.

```bash
# Install Node.js (v18 or later)
# 💻 Windows: Download from nodejs.org
# 🍎 macOS: brew install node@18
# 🐧 Linux: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version

# Install project dependencies
npm install  # This will automatically set up Husky
```
</details>

## 🚀 Quick Start

<div align="center">

```bash
┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Clone  │ ──► │   Setup  │ ──► │   Install    │ ──► │   Run    │
│  Repo   │     │    Env   │     │Dependencies  │     │   App    │
└─────────┘     └──────────┘     └──────────────┘     └──────────┘
```

</div>

### 1. 📥 Clone & Navigate
```bash
git clone https://github.com/Abjad-Advertiser/Abjad-Advertiser-Backend.git
cd Abjad-Advertiser-Backend
```

### 2. 🔧 Setup Development Environment

1. **Create and Activate Virtual Environment**
```bash
# 💻 Windows
python -m venv .venv
.venv\Scripts\activate

# 🍎 macOS/🐧 Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. **Install Python Dependencies**
```bash
# Make sure your pip is up to date
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

3. **Install Development Tools**
```bash
# Install Node.js dependencies (Husky, lint-staged, commitlint)
npm install

# Husky will be automatically set up to:
# - Run Python linters (black, isort, ruff) before commits
# - Check commit message format
# - Run tests before pushing
```

4. **Verify Installation**
```bash
# Check if Python tools are installed
python -c "import fastapi; print(fastapi.__version__)"
python -c "import sqlalchemy; print(sqlalchemy.__version__)"

# Check if Husky is set up
ls -la .git/hooks/  # Should show pre-commit hook
```

5. **Configure Environment**
```bash
# Create and configure your .env file
PORT=8000
DATABASE_URL=postgresql+asyncpg://<username>:<password>@postgres_db:5432/abjad_advertiser_db
SECRET_KEY=<your-secret-key>
ALGORITHM=<your-algorithm>
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=True
```

## 🏃‍♂️ Running the App

<div align="center">

| Method | Command | Description |
|--------|---------|-------------|
| 🐳 Docker | `docker compose up --build` | Run everything in containers |
| 🛑 Stop | `docker compose down` | Stop all containers |
| 🎲 DB Only | `docker compose up -d postgres_db` | Run database only |
| 🔧 Manual | `python main.py` | Run FastAPI directly |

</div>

## 📚 API Documentation
<div align="center">

| Documentation | URL | Description |
|--------------|-----|-------------|
| 🎮 Swagger UI | `http://localhost:8000/docs` | Interactive API testing |
| 📖 ReDoc | `http://localhost:8000/redoc` | Alternative documentation |

</div>

## 🧪 Testing
<div align="center">

[![Tests](https://img.shields.io/badge/tests-unit-green.svg?style=for-the-badge)](https://docs.pytest.org/en/stable/)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellowgreen.svg?style=for-the-badge)](https://coverage.readthedocs.io/)

```bash
pytest  # Run all tests
pytest --cov=app tests/  # Run with coverage
```

</div>

## 🗃️ Database Management
```bash
alembic init alembic
alembic migrate
alembic upgrade head
```

## 🔧 Troubleshooting

<details>
<summary>🔌 Port Issues</summary>

- Change `PORT` in `.env` if 8000 is in use
- Check if another service is using the port
</details>

<details>
<summary>🎲 Database Connection</summary>

- Ensure PostgreSQL container is running
- Verify connection string in `.env`
- Check database logs: `docker-compose logs postgres_db`
</details>

<details>
<summary>🔑 Permission Problems</summary>

- Windows: Run PowerShell as Admin
- Linux/macOS: Use `sudo` when needed
</details>

<details>
<summary>📝 Commit Linting</summary>

```bash
# Install globally
npm install -g @commitlint/{cli,config-conventional}

# Add to PATH
npm root -g  # Add this path to your environment variables
```
</details>

## 🤝 Contributing
<div align="center">

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](http://makeapullrequest.com)
[![Contributors](https://img.shields.io/github/contributors/Abjad-Advertiser/Abjad-Advertiser-Backend?style=for-the-badge)](https://github.com/Abjad-Advertiser/Abjad-Advertiser-Backend/graphs/contributors)

We love contributions! Please check our contributing guidelines and feel free to submit PRs.
</div>

## 🆘 Need Help?
<div align="center">

| Channel | Purpose |
|---------|----------|
| 📝 Issues | Bug reports & feature requests |
| 📧 Email | Technical support |
| 📚 Wiki | Documentation & guides |

</div>

## 📜 License
<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

This project is licensed under the MIT License - see the LICENSE file for details.

---

<p align="center">
  <sub>Made with ❤️ by the Abjad Team</sub>
</p>

</div>
