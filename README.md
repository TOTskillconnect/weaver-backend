# Y Combinator Jobs Scraper API

A Flask-based REST API that scrapes job listings from Y Combinator's job board.

## Features

- Scrapes job listings from Y Combinator's job board
- RESTful API endpoints
- Docker containerization
- Automated deployment via Render
- CORS support
- Health monitoring
- Comprehensive error handling and logging

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the API.

### Submit URL for Scraping
```
POST /submit
Content-Type: application/json

{
    "url": "https://www.ycombinator.com/jobs",
    "format": "json"  // optional, defaults to "json"
}
```

## Local Development

### Prerequisites
- Python 3.11+
- Docker
- Docker Compose

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd weaver-backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Run with Docker:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:5000`

### Running Tests
```bash
pip install -r requirements-test.txt
pytest
```

## Deployment

The application is configured for automatic deployment on Render.com using the `render.yaml` configuration.

## Environment Variables

- `FLASK_ENV`: Set to 'production' for production deployment
- `SELENIUM_HEADLESS`: Set to 'true' for headless browser operation
- `PYTHONUNBUFFERED`: Set to 'true' for unbuffered Python output
- `CHROME_BIN`: Path to Chrome binary
- `CHROMEDRIVER_PATH`: Path to ChromeDriver

## License

MIT License 