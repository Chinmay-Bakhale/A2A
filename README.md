# Leave Policy Assistant Agent 🤖

An AI-powered Leave Policy Assistant built with Google ADK (Agent Development Kit) that helps employees check leave balances, understand leave policies, and determine eligibility for leave requests.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running Locally](#running-locally)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security Features](#security-features)
- [Design Decisions](#design-decisions)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### Core Features
- **Leave Balance Checking**: Query current leave balances for any employee
- **Eligibility Calculation**: Determine if an employee can take leave based on:
  - Available balance
  - Minimum notice period requirements
  - Maximum consecutive days limits
  - Blackout period restrictions
- **Policy Information**: Retrieve detailed leave policy rules by country and leave type
- **Multi-turn Conversations**: Contextual conversations with session management
- **Multi-country Support**: US, India, and UK leave policies

### Security Features
- **PII Detection & Masking**: Automatically detects and masks sensitive information (emails, SSN, phone numbers)
- **Content Filtering**: Blocks malicious or inappropriate content
- **Before/After Model Callbacks**: Security validation at request and response stages
- **Audit Logging**: Complete audit trail of all interactions

### Resilience Features
- **Circuit Breaker Pattern**: Prevents cascading failures in Snowflake connections
- **Graceful Error Handling**: User-friendly error messages
- **Health Checks**: Comprehensive health monitoring

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
│  ┌─────────────────────────────────────┐   │
│  │    /chat    /health    /stats       │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│  ┌──────────────▼──────────────────────┐   │
│  │   Leave Assistant Agent (ADK)       │   │
│  │  ┌────────────────────────────┐     │   │
│  │  │ Before Model Callback      │     │   │
│  │  │  - PII Detection           │     │   │
│  │  │  - Content Filtering       │     │   │
│  │  └────────────┬───────────────┘     │   │
│  │               │                     │   │
│  │  ┌────────────▼───────────────┐     │   │
│  │  │   LiteLLM (Gemini)         │     │   │
│  │  └────────────┬───────────────┘     │   │
│  │               │                     │   │
│  │  ┌────────────▼───────────────┐     │   │
│  │  │  After Model Callback      │     │   │
│  │  │   - Response Validation    │     │   │
│  │  │   - Logging                │     │   │
│  │  └────────────────────────────┘     │   │
│  └─────────────────────────────────────┘   │
│                 │                           │
│  ┌──────────────▼──────────────────────┐   │
│  │         Custom Tools                │   │
│  │  - check_leave_balance              │   │
│  │  - calculate_eligibility            │   │
│  │  - get_leave_policy_details         │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
└─────────────────┼───────────────────────────┘
                  │
       ┌──────────▼──────────┐
       │  Snowflake Client   │
       │  (Circuit Breaker)  │
       └──────────┬──────────┘
                  │
       ┌──────────▼──────────┐
       │   Mock Data / DB    │
       └─────────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Agent Framework | Google ADK | ≥1.19.0 |
| LLM Integration | LiteLLM | ≥1.80.0 |
| Data Warehouse | Snowflake Snowpark | Latest |
| API Framework | FastAPI | ≥0.109.0 |
| Cloud Platform | Google Cloud Run | - |
| Observability | OpenTelemetry + Cloud Trace | Latest |
| Python | Python | 3.12+ |
| Testing | Pytest | ≥7.4.0 |

## 📁 Project Structure

```
A2A/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── agent.py             # Core ADK agent implementation
│   ├── tools.py             # Custom agent tools
│   ├── callbacks.py         # Security callbacks
│   ├── models.py            # Pydantic models
│   ├── mock_data.py         # Sample leave policies & employee data
│   ├── snowflake_client.py  # Snowflake integration
│   └── circuit_breaker.py   # Circuit breaker implementation
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── tests/
│   ├── __init__.py
│   └── test_tools.py        # Unit tests
├── .env                     # Environment variables
├── .env.example             # Environment template
├── .gitignore
├── .dockerignore
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container definition
├── cloudbuild.yaml          # GCP CI/CD configuration
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.12 or higher
- Google Cloud account (for deployment)
- Gemini API key (for LLM)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd A2A
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# LLM Configuration
LITELLM_MODEL=gemini/gemini-pro
GOOGLE_API_KEY=your_gemini_api_key_here

# Application Settings
PORT=8080
LOG_LEVEL=INFO

# Snowflake (Optional - currently using mock data)
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# GCP (for deployment)
GCP_PROJECT_ID=your_project_id
```

**Important**: Replace `your_gemini_api_key_here` with your actual Gemini API key.

## 🏃 Running Locally

### Start the Server

```bash
# Option 1: Using Python directly
python -m uvicorn app.main:app --reload --port 8080

# Option 2: Using the main.py entry point
python app/main.py
```

The API will be available at `http://localhost:8080`

### Test the Application

**⚠️ Rate Limit Notice**: Gemini's free tier has a limit of **5 requests per minute**. The agent includes automatic retry logic with exponential backoff.

```bash
# Quick single test (recommended to avoid rate limits)
python quick_test.py

# Full test suite (includes 15s delays between requests)
python test_local.py
```

### Access API Documentation

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## 📚 API Documentation

### Endpoints

#### 1. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

#### 2. Chat with Agent
```http
POST /chat
```

Request:
```json
{
  "message": "How many PTO days do I have left?",
  "session_id": "session-123",
  "employee_id": "EMP001"
}
```

Response:
```json
{
  "response": "You have 12 PTO days remaining out of your 20-day annual allowance.",
  "session_id": "session-123",
  "timestamp": "2024-01-15T10:30:00",
  "metadata": {
    "model": "gemini/gemini-pro"
  }
}
```

#### 3. Clear Session
```http
DELETE /session/{session_id}
```

#### 4. Get Statistics
```http
GET /stats
```

### Sample Conversations

#### Example 1: Check Leave Balance
```
User: How many PTO days do I have left?
Agent: I'd be happy to help you check your PTO balance. May I have your employee ID?
User: EMP001
Agent: You have 12 PTO days remaining out of your 20-day annual allowance. You've used 8 days so far this year.
```

#### Example 2: Check Eligibility
```
User: Can I take 5 days of PTO from June 1-5?
Agent: Let me check your eligibility for that leave request. What is your employee ID?
User: EMP001
Agent: Good news! You are eligible for 5 days of PTO from June 1-5. You have sufficient balance (12 days remaining), and the request meets the 3-day minimum notice requirement. Please note that manager approval is required before confirmation.
```

#### Example 3: Policy Inquiry
```
User: What's the maximum consecutive PTO days I can take?
Agent: For US employees, the maximum consecutive PTO days is 10 days. If you need to take more than 10 consecutive days, you would need to split it into multiple requests or discuss with HR for special circumstances.
```

## 🧪 Testing

### Run All Tests

```bash
# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v

# Run with output
pytest tests/ -v -s
```

### Test Coverage

The project includes comprehensive tests for:
- Leave balance checking
- Eligibility calculations
- Policy retrieval
- Circuit breaker functionality
- Security callbacks

Target coverage: **>80%**

## 🚢 Deployment

### Deploy to Google Cloud Run

#### 1. Build and Push Container

```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Build the container
gcloud builds submit --config cloudbuild.yaml

# Or build locally
docker build -t gcr.io/YOUR_PROJECT_ID/leave-assistant .
docker push gcr.io/YOUR_PROJECT_ID/leave-assistant
```

#### 2. Deploy to Cloud Run

```bash
gcloud run deploy leave-assistant \
  --image gcr.io/YOUR_PROJECT_ID/leave-assistant:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars LOG_LEVEL=INFO \
  --max-instances 10 \
  --memory 2Gi
```

#### 3. Set Secrets

```bash
# Create secrets in Secret Manager
echo -n "your-api-key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Update Cloud Run to use secrets
gcloud run services update leave-assistant \
  --update-secrets GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

### CI/CD Pipeline

The `cloudbuild.yaml` configuration automates:
1. Building the Docker container
2. Pushing to Google Container Registry
3. Deploying to Cloud Run

Trigger on git push:
```bash
git push origin main
```

## 🔒 Security Features

### 1. PII Detection & Masking
- Email addresses
- Social Security Numbers
- Phone numbers
- Credit card numbers
- Passport numbers

### 2. Content Filtering
Blocks requests containing:
- Malicious keywords (hack, exploit, attack)
- Credential exposure attempts
- SQL injection patterns
- XSS attempts

### 3. Audit Logging
All interactions are logged with:
- Timestamp
- Session ID
- PII detection events
- Security violations
- Token usage

## 🎯 Design Decisions

### 1. Why Google ADK + LiteLLM?
- **ADK**: Provides structured agent framework with tool calling
- **LiteLLM**: Unified interface for multiple LLM providers, easy to switch models

### 2. Circuit Breaker Pattern
- Prevents cascading failures when Snowflake is down
- Automatic retry with timeout
- Fail-fast approach for better UX

### 3. Mock Data vs Real Database
- Demonstrates Snowflake integration patterns
- Easy to test without infrastructure
- Circuit breaker still functional
- Production-ready structure

### 4. Callback Architecture
- **Before Model**: Security scanning before LLM sees data
- **After Model**: Response validation and logging
- Separation of concerns

### 5. Session Management
- In-memory for simplicity (can extend to Firestore)
- Enables multi-turn conversations
- Context preservation

## 🔧 Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `LITELLM_MODEL` | LLM model to use | `gemini/gemini-pro` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PORT` | Server port | `8080` |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | Failures before opening circuit | `5` |
| `CIRCUIT_BREAKER_TIMEOUT` | Seconds before retry | `60` |

## 📊 Monitoring & Observability

### Metrics Available
- Request count and latency
- PII detection events
- Security violations
- Circuit breaker state
- Token usage

### Health Monitoring
```bash
curl http://localhost:8080/health
curl http://localhost:8080/stats
```

## 🤝 Contributing

This project was created for a technical assignment. For questions or issues, please contact the development team.

## 📝 License

Confidential - For evaluation purposes only.

## 🆘 Troubleshooting

Having issues? Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Rate limit solutions
- Common errors and fixes
- Testing tips
- Debug mode instructions

**Common Issues:**
- **Rate Limit (429)**: Wait 15s between requests or use `quick_test.py`
- **_asdict() error**: Fixed in latest version, restart server
- **Server won't start**: Check if port 8080 is available

---

**Built with ❤️ using Google ADK, LiteLLM, and FastAPI**
