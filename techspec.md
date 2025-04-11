

Backend Technical Specification Document for “Cursor”
1. Overview
Project Name: Cursor

Objective:
Develop a Python-based backend service to receive a starting source URL (from the UI), perform robust web scraping on Y Combinator job pages to extract founder details (including LinkedIn URLs), and return the data as a CSV file for prospecting purposes.

Scope:
The backend will:

Accept a source URL via API.
Initiate a controlled crawling session to discover role pages.
Extract critical founder information (name, title, LinkedIn URL) using dynamic content handling.
Process data asynchronously if needed, and generate a downloadable CSV file.
Provide endpoints for job submission, status tracking, and result download.

2. Goals & Objectives
Scalability:
Implement asynchronous task processing to support long-running scraping jobs and parallelize page extraction when necessary.

Robustness:
Apply best practices for interacting with dynamically generated web pages (using headless browsers) and implement proper error handling and retries.

Maintainability:
Use a modular code structure to separate scraping logic, API endpoints, and asynchronous task management.

Security & Compliance:
Validate inputs, handle personal data responsibly, and adhere to web scraping legal guidelines and ethical considerations.

3. Functional Requirements
URL Submission Endpoint:

Accept a POST request with the source URL from the frontend.

Validate and sanitize the input URL.

Scraping Task Execution:

Use a headless browser (Selenium/Playwright) to load pages and extract dynamic content.

Navigate from the search page to individual role pages.

Locate and extract founder information (name, title, and LinkedIn URL).

Data Aggregation & CSV Generation:

Process and store extracted data in memory.

Generate and deliver a CSV file containing:

Role Page URL

Founder Name

Founder Title

LinkedIn URL

Status & Download Endpoints (Optional for Asynchronous Tasks):

Provide a GET endpoint to poll the job status.

Offer a GET endpoint for downloading the CSV upon task completion.

Logging & Error Handling:

Log progress, errors, and exceptions throughout the scraping process.

Implement retries for transient errors (such as network timeouts and dynamic loading issues).

4. Non-Functional Requirements
Performance:
Execute efficiently with headless mode to reduce overhead; implement concurrency where possible.

Reliability:
Include robust error handling and retry mechanisms.

Modularity:
Decouple components (API logic, scraping module, task queue) to facilitate maintainability and potential future scaling.

Deployment Readiness:
Containerize the backend using Docker to ensure consistency across environments and ease deployment on platforms like Render, Railway, or Heroku.

5. Technical Architecture
System Components:
API Gateway:

Exposes RESTful endpoints (/submit, /status/<job_id>, /download/<job_id>) using Flask or FastAPI.

Scraping Module:

Contains Selenium-based logic for crawling and data extraction.

Uses explicit waits for dynamic content and handles potential edge cases such as missing elements.

Task Manager (Optional - Asynchronous Processing):

Uses Celery with Redis (or RabbitMQ) as the message broker.

Offloads long-running scraping tasks to background workers.

Data Formatter:

Aggregates scraped data and generates the final CSV output.

Logging & Monitoring:

Uses Python’s logging framework.

Optionally integrates with monitoring tools for live tracking of job progress and error notifications.

Architecture Diagram (Conceptual):

                     +-----------------------+
                     |     Frontend (UI)     |
                     |   (Vercel Hosted)     |
                     +-----------+-----------+
                                 |
                                 | REST API Call (Submit URL)
                                 v
                     +-----------------------+
                     |     API Gateway       |
                     | (Flask / FastAPI App) |
                     +-----------+-----------+
                                 |
                         (Optional Celery Task)
                                 |
                                 v
                     +-----------------------+
                     |  Scraping & Task      |
                     |      Manager          |
                     | (Selenium / Celery)   |
                     +-----------+-----------+
                                 |
                                 v
                     +-----------------------+
                     | CSV Generation Module |
                     +-----------+-----------+
                                 |
                                 v
                     +-----------------------+
                     |   API Gateway         |
                     |   (Download CSV)      |
                     +-----------------------+
6. Technology Stack
Programming Language:
Python 3.9+.

Web Framework:
Flask or FastAPI for building RESTful APIs.

Web Scraping:
Selenium (with headless Chrome/Firefox) or Playwright for dynamic content loading.

Asynchronous Task Processing:
Celery (with Redis or RabbitMQ) for managing long-running tasks (optional based on load).

Data Processing:
Python CSV library or pandas for generating CSV output.

Containerization & Deployment:
Docker for containerization; potential deployment on Heroku, Render, or Railway.

Logging:
Python's built-in logging module.

Version Control:
Git for source code management.

7. Project Structure
If using a separate backend repository, an example file structure:

bash
Copy
/backend
├── app.py                 # Main Flask/FastAPI application
├── requirements.txt       # List of Python dependencies
├── config.py              # Configuration settings (e.g., environment variables, URLs)
├── scraper                # Module containing scraping logic
│   ├── __init__.py
│   └── scraper.py         # Contains functions/classes for page interaction and data extraction
├── tasks                  # (Optional) Module for Celery asynchronous tasks
│   ├── __init__.py
│   └── tasks.py           # Celery task definitions
├── utils                  # Utility functions (logging, helper functions)
│   └── helpers.py
├── tests                  # Unit tests and integration tests
│   └── test_scraper.py
└── Dockerfile             # Dockerfile for containerization
8. API Design
Endpoints:
POST /submit

Description:
Receives the source URL and initiates the scraping process.

Request Payload:
{
  "url": "https://www.ycombinator.com/jobs"
}
Response:

For synchronous processing: return the CSV file directly.

For asynchronous processing: return a JSON object with a job_id for further status tracking.

GET /status/<job_id> (Optional)

Description:
Returns the current status of the scraping job.

Response:

json
Copy
{
  "job_id": "12345",
  "status": "in-progress", 
  "progress": "50%" 
}
GET /download/<job_id> (Optional for Asynchronous Tasks)

Description:
Provides a downloadable CSV file once the scraping job is complete.

9. Scraping Module Best Practices
Use Headless Browsers:
Configure Selenium to run in headless mode to save resources.

Explicit Waits:
Use Selenium’s WebDriverWait combined with expected conditions (e.g., presence_of_element_located, element_to_be_clickable) for dynamic content loading.

Error Handling & Retries:
Catch exceptions (e.g., NoSuchElementException, TimeoutException) and implement retries or fallback strategies if elements are not found.

User-Agent Rotation & Throttling:
Consider rotating user-agents and applying delays (e.g., time.sleep()) between requests to mimic human-like interactions and avoid detection.

Modular Code:
Separate the scraping logic into functions/classes to facilitate testing and future modifications.

10. Asynchronous Task Management
Celery Integration (Optional):
If tasks are expected to run long or in parallel:

Setup:
Create Celery tasks to offload the scraping process.

Broker:
Use Redis or RabbitMQ as the message broker.

Task Flow:

The /submit endpoint triggers a Celery task.

The task performs the scraping and saves the CSV file (e.g., in temporary storage or a database).

Update task status for polling via /status/<job_id>.

Final CSV file is delivered via /download/<job_id>.

11. Logging, Monitoring, and Security
Logging:

Use Python’s logging framework to log key events (task start/stop, errors, retries).

Optionally integrate with centralized logging solutions (e.g., ELK stack).

Monitoring:

Monitor task performance and resource usage.

Use health-check endpoints to ensure the backend is responsive.

Security:

Validate and sanitize all user inputs.

Enforce CORS policies if frontend and backend are hosted on different domains.

Consider rate limiting for public endpoints to avoid abuse.

Data Privacy & Compliance:

Follow legal guidelines for web scraping and secure handling of scraped data (avoid storing more data than necessary).

12. Testing Strategy
Unit Tests:

Test individual modules (e.g., scraping logic, CSV generation).

Integration Tests:

Test end-to-end flows from URL submission to CSV generation.

Mocking External Dependencies:

Use mocks for Selenium/WebDriver interactions during testing to reduce reliance on live pages.

Continuous Integration:

Setup CI pipelines (using GitHub Actions, CircleCI, etc.) to run tests on every commit.

13. Deployment Strategy
Dockerization:

Create a Dockerfile for containerizing the backend.

Use Docker Compose if needed to run the backend service along with Redis (and other dependencies) during local development.

Cloud Deployment:

Preferred Options:
Platforms like Heroku, Render, or Railway support Python applications with containerized deployments.

Integration with CI/CD Pipelines:
Automate the deployment process with pipelines that trigger on successful builds.

Scalability & Load Handling:

For asynchronous tasks, scale Celery workers independently based on job queue size.

Monitor resource utilization and employ auto-scaling if supported by the host platform.