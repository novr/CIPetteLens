# CIPetteLens 🔬

A minimal, viable CI/CD dashboard that visualizes metrics by wrapping the powerful `CIAnalyzer` engine.

## Features

-   📊 Collects and analyzes GitHub Actions workflow data using CIAnalyzer.
-   💾 Stores pre-calculated metrics from CIAnalyzer's report into a local SQLite database.
-   🚀 Provides a lightweight web interface to visualize key metrics: Duration, Success Rate, Throughput, and MTTR.
-   ⚙️ Simple, configuration-based setup for target repositories.

## Requirements

-   Python 3.11+
-   [uv](https://github.com/astral-sh/uv) - A fast Python package installer and resolver.

## Quick Start

### Local Development (Recommended)

```bash
# Install uv (if you don't have it)
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# Clone this repository
git clone [https://github.com/your-username/CIPetteLens](https://github.com/your-username/CIPetteLens)
cd CIPetteLens

# Setup project
mise run setup

# Configure environment
# Edit .env and set GITHUB_TOKEN and TARGET_REPOSITORIES

# Start development server
mise run dev
```

### 3. Run Data Collection

```bash
# Collect CI/CD metrics
mise run collect
```

### 4. Access Web Dashboard

```bash
# Dashboard will be available at
open http://localhost:5001
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

# Development
mise run dev          # Run development server
mise run web          # Start web server
mise run collect      # Collect data using CIAnalyzer
mise run health       # Check application health

# Testing
mise run test         # Run all tests
mise run test-coverage # Run tests with coverage
mise run test-security # Run security tests

# Code Quality
mise run lint         # Run linting
mise run lint-fix     # Fix linting issues
mise run format       # Format code
mise run format-check # Check code formatting
mise run type-check   # Run type checking

# Security
mise run security-scan # Run security scan
mise run audit        # Audit dependencies

# Database
mise run db-init      # Initialize database
mise run db-reset     # Reset database

# Workflow
mise run pre-commit   # Run pre-commit checks
mise run ci           # Run CI pipeline
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
│   ├── lens.py             # CIAnalyzer integration
│   ├── logger.py           # Logging configuration
│   └── security.py         # Security utilities
├── db/                     # Database files
│   └── data.sqlite         # SQLite database file
├── templates/              # HTML templates
│   └── dashboard.html
├── static/                 # CSS stylesheets
│   └── style.css
├── tests/                  # Test suite
│   ├── test_lens.py
│   └── test_security.py
├── .github/                # GitHub Actions CI/CD
│   └── workflows/
│       └── ci.yml
├── env.example             # Environment variable template
├── .mise.toml              # Task runner configuration
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