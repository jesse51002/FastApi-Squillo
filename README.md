# FastAPI-Squillo

A FastAPI-based recipe import and AI recipe engine service that extracts cooking techniques and imports recipes from various sources.

## Prerequisites

- Python 3.12 or higher
- Poetry (Python dependency management)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FastApi-Squillo
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Install pre-commit hooks**
   ```bash
   poetry run pre-commit install
   ```

5. **Configure environment variables**

   Create a `.env` file in the project root with the following API keys:
   ```env
   MISTRAL_API_KEY=your-mistral-api-key-here
   CLAUDE_API_KEY=your-claude-api-key-here
   GEMINI_API_KEY=your-gemini-api-key-here
   ENSEMBLE_DATA_API_KEY=your-ensemble-data-api-key-here
   ```

## Running the Server

Run the server with auto-reload enabled:

```bash
make run
```

The server will start at `http://localhost:8000`

### API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check

Verify the server is running:

```bash
curl http://localhost:8000/health
```

## Development

### Code Quality

**Pre-commit hooks** (automatically runs on git commit):
- Formats code with `make format`
- Lints code with `make lint`

Install pre-commit hooks:
```bash
poetry run pre-commit install
```

**Lint code:**
```bash
make lint
```

**Format code:**
```bash
make format
```

**Clean cache files:**
```bash
make clean
```

## Technologies

- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation using Python type hints
- **Poetry** - Dependency management
- **Google Gemini** - AI/LLM integration
- **httpx** - Async HTTP client
- **recipe-scrapers** - Web recipe extraction

## Coding Standards

This project follows strict coding standards documented in [claude.md](claude.md).