# CIPetteLens 🔬

A minimal, viable CI/CD dashboard that visualizes metrics by wrapping the powerful `CIAnalyzer` engine.

## Features

-   📊 Wraps `CIAnalyzer` to collect and analyze GitHub Actions workflow data via Docker.
-   💾 Stores pre-calculated metrics from `CIAnalyzer`'s report into a local SQLite database.
-   🚀 Provides a lightweight web interface to visualize key metrics: Duration, Success Rate, Throughput, and MTTR.
-   ⚙️ Simple, configuration-based setup for target repositories.

## Requirements

-   Python 3.11+
-   [uv](https://github.com/astral-sh/uv) - A fast Python package installer and resolver.
-   **Docker** - To run the `CIAnalyzer` engine.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone this repository
git clone [https://github.com/your-username/CIPetteLens](https://github.com/your-username/CIPetteLens)
cd CIPetteLens

# Configure environment
cp env.example .env
# Edit .env and set GITHUB_TOKEN and TARGET_REPOSITORIES

# Build and run with Docker
mise run build
mise run run

# Or use Docker Compose
docker-compose up -d
```

### Option 2: Local Development

```bash
# Install uv (if you don't have it)
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# Make sure Docker is installed and running
docker --version

# Clone this repository
git clone [https://github.com/your-username/CIPetteLens](https://github.com/your-username/CIPetteLens)
cd CIPetteLens

# Install dependencies using uv
uv sync

# Configure environment
cp env.example .env
# Edit .env and set GITHUB_TOKEN and TARGET_REPOSITORIES
```

### 3. Run Data Collection

```bash
# Using Docker
mise run collect

# Or locally
uv run collect
```

### 4. Start Web Dashboard

```bash
# Using Docker (already running if you used mise run run)
open http://localhost:5000

# Or locally
uv run web
open http://localhost:5000
```

## Development

### Quick Setup

```bash
# Complete project setup
mise run setup

# Install development dependencies
mise run install-dev
```

### Available Tasks

```bash
# Show all available tasks
mise tasks

# Run tests
mise run test

# Run security tests
mise run test-security

# Run tests with coverage
mise run test-coverage

# Lint and format
mise run lint
mise run format

# Run pre-commit checks
mise run pre-commit

# Run CI pipeline
mise run ci
```

### Development Workflow

```bash
# Start development environment
mise run dev

# In another terminal, run tests
mise run test

# Check application health
mise run health
```

## Project Structure

```
CIPetteLens/
├── cipettelens/            # Main package
│   ├── __init__.py
│   ├── app.py              # Flask web dashboard
│   ├── config.py           # Configuration loader
│   ├── database.py         # SQLite operations
│   └── lens.py             # Wrapper script for CIAnalyzer (via Docker)
├── db/                     # For database files
│   └── data.sqlite         # SQLite database file
├── templates/              # HTML templates
│   └── dashboard.html
├── static/                 # CSS stylesheets
│   └── style.css
├── tests/                  # Test suite
│   └── test_lens.py
├── env.example             # Environment variable template
├── pyproject.toml          # Project metadata & dependencies
└── README.md
```

## Environment Variables

Create a `.env` file with the following:

```bash
# --- Required ---
# GitHub token for CIAnalyzer to access the API
GITHUB_TOKEN=ghp_your_token_here

# Comma-separated list of repositories to analyze
TARGET_REPOSITORIES=owner/repo1,owner/repo2

# --- Optional ---
# Configuration for the Flask web server
FLASK_DEBUG=True
FLASK_PORT=5000
```

## Architecture

**Tech Stack:**
-   Python 3.11+
-   Flask (web framework)
-   SQLite (data storage)
-   **Docker**
-   `CIAnalyzer` (analysis engine, run via Docker)
-   pytest (testing)
-   ruff (linting & formatting)
-   uv (package management)

**Data Flow:**
1.  A scheduler (`cron`) or manual command triggers `lens.py`.
2.  `lens.py` executes a `docker run kesin11/cianalyzer ...` command as a subprocess.
3.  The `CIAnalyzer` container calls the GitHub Actions API, performs its analysis, and outputs a JSON report.
4.  `lens.py` captures and parses this JSON report.
5.  The extracted, pre-calculated metrics are saved to the SQLite database.
6.  `app.py` serves a web dashboard that reads the latest metrics from the SQLite database.

## License

MIT