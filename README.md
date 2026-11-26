# LLMOps Ticket Triage API

An AI-powered customer support ticket classification API built with FastAPI and Large Language Models (LLMs).

The application analyzes customer support tickets and generates structured classifications, priority levels, summaries, and suggested customer replies.

## Features

- **Ticket Classification:** Categorizes tickets into Technical, Billing, Account, Subscription, Delivery, Refund, General, and Other.
- **Priority Detection:** Assigns Low, Medium, High, or Critical priority.
- **LLM Integration:** Uses Gemini as the primary provider and Groq as the fallback provider through LiteLLM.
- **Provider Fallback:** Automatically switches to Groq when Gemini fails.
- **Quota Cooldown:** Skips Gemini for the remainder of the running process after detecting daily quota exhaustion.
- **Prompt Management:** Maintains classification instructions in YAML.
- **Response Validation:** Uses Pydantic to validate structured LLM responses.
- **Error Handling:** Implements retries, exponential backoff, and provider-level error handling.
- **Safety Checks:** Blocks selected unsupported claims in generated customer replies.
- **Automated Testing:** Includes pytest-based unit and API tests.
- **LLMOps Monitoring:** Tracks request counts, provider usage, failures, token consumption, and latency using Prometheus metrics.
- **Docker Support:** Includes Dockerfile and Docker Compose configuration.

## Tech Stack

- Python 3.12
- FastAPI
- LiteLLM
- Gemini API
- Groq API
- Pydantic
- PyYAML
- Prometheus Client
- Pytest
- Docker

## Architecture

```text
Customer
   |
   v
FastAPI Application
   |
   v
Ticket Processing
   |
   v
Prompt Manager (YAML)
   |
   v
LLM Client (LiteLLM)
   |
   +------> Gemini (Primary)
   |
   +------> Groq (Fallback)
   |
   v
Response Validation (Pydantic)
   |
   v
Safety Checks
   |
   v
Structured JSON Response
```

Prometheus metrics are exposed through the `/metrics` endpoint.

## Project Structure

```text
llm-ops-ticket-triage/
│
├── app/
│   ├── main.py
│   ├── triage.py
│   ├── llm_client.py
│   ├── prompt_manager.py
│   ├── schema.py
│   ├── logger.py
│   └── metrics.py
│
├── prompts/
│   └── triage.yaml
│
├── tests/
│
├── evals/
│
├── datasets/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Setup and Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd llm-ops-ticket-triage
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Add your own API credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model_name

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_groq_model_name
```

Never commit your actual `.env` file or API keys.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application information |
| GET | `/healthz` | Health check |
| POST | `/triage` | Classify a support ticket |
| GET | `/metrics` | Prometheus metrics |

### Interactive API Documentation

Open:

`http://127.0.0.1:8000/docs`

### Example Request

**POST /triage**

```json
{
  "ticket": "I was charged twice for my monthly subscription. Both transactions appear in my bank statement."
}
```

### Example Response

```json
{
  "category": "Billing",
  "priority": "High",
  "product": "Unknown",
  "summary": "The customer reports being charged twice for their monthly subscription.",
  "draft_reply": "Thank you for contacting us. We apologize for the inconvenience..."
}
```

## Automated Testing

Run the complete test suite:

```bash
python -m pytest -v
```

The project currently has 31 automated tests passing.

## Monitoring

Prometheus metrics are available at:

`http://127.0.0.1:8000/metrics`

Metrics include:

- Total LLM requests
- Provider-specific successful requests
- Provider failures
- Prompt token consumption
- Completion token consumption
- Total token consumption
- LLM request latency

## Docker

Build and start the application:

```bash
docker compose up --build -d
```

The Docker Compose configuration maps the application to:

`http://localhost:8001`

Stop the container:

```bash
docker compose down
```

## Limitations

- Classification quality depends on the selected LLM and prompt.
- The provider cooldown is process-local and resets when the application restarts.
- Draft replies are suggestions and should be reviewed before being sent to customers.
- The current safety checks use phrase matching and are not a comprehensive semantic hallucination detector.
- Evaluation results on synthetic datasets should not be interpreted as guaranteed real-world performance.

## Future Improvements

- Production deployment.
- More comprehensive evaluation datasets.
- Advanced response safety validation.
- Persistent provider cooldown management.
- Expanded monitoring and observability.

## Author

Mayank Raj

GitHub: [0mayank-raj](https://github.com/0mayank-raj)