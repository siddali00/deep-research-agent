# Deep Research AI Agent

Autonomous research agent for intelligence gathering, risk assessment, and due diligence investigations. Built with LangGraph for orchestration, multi-model AI (OpenAI + Gemini), Tavily search, and Neo4j for identity graph generation.

## Architecture

```
FastAPI API
  └── ResearchService
        └── LangGraph StateGraph
              ├── Planner    → generates search queries (OpenAI GPT-4.1)
              ├── Searcher   → executes web searches (Tavily)
              ├── Extractor  → extracts structured facts (Gemini 2.5)
              ├── Analyzer   → identifies risks & patterns (OpenAI GPT-4.1)
              ├── Validator  → confidence scoring & sufficiency check (Gemini 2.5)
              │     ├── [needs more] → back to Planner
              │     └── [sufficient] → Reporter
              └── Reporter   → final report + Neo4j graph (OpenAI GPT-4.1)
```

The agent runs iterative research loops. Each iteration: plan queries, search the web, extract facts, analyze for risks, validate confidence, and decide whether to continue or report.

## Project Structure

```
src/
├── config/          # Pydantic Settings, model constants
├── models/          # AI model providers (OpenAI, Gemini) + router
├── graphs/          # LangGraph state, nodes, edges, compiled graph
│   ├── nodes/       # planner, searcher, extractor, analyzer, validator, reporter
│   └── edges/       # conditional routing logic
├── tools/           # Tavily search, web scraper
├── db/              # Neo4j client, schemas (nodes/relationships), Cypher queries
├── api/             # FastAPI app, routers, controllers, Pydantic schemas
├── services/        # Research orchestration, scoring, report formatting
└── utils/           # Logging, rate limiter, prompt templates

evaluation/          # Test personas, evaluator, metrics (precision/recall/F1)
tests/               # Unit and integration tests
```

## Setup

### Prerequisites

- Python 3.11+
- Neo4j (local or cloud instance)
- API keys for: OpenAI, Google Gemini, Tavily

### Installation

```bash
# Clone and enter the project
cd elile-ai-task

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# For development
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your actual API keys
```

Required environment variables:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google Gemini API key |
| `TAVILY_API_KEY` | Tavily search API key |
| `NEO4J_URI` | Neo4j connection URI (default: `bolt://localhost:7687`) |
| `NEO4J_USER` | Neo4j username (default: `neo4j`) |
| `NEO4J_PASSWORD` | Neo4j password |
| `LANGSMITH_API_KEY` | LangSmith API key (optional, for tracing) |
| `LANGSMITH_ENDPOINT` | Optional; set to `https://eu.api.smith.langchain.com` for EU |

## Usage

### API Server

```bash
uvicorn src.api.app:app --reload --port 8000
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/research/` | Start a new research investigation |
| `GET` | `/api/research/{job_id}/status` | Check research progress |
| `GET` | `/api/research/{job_id}/result` | Get structured results |
| `GET` | `/api/reports/{job_id}` | Get full markdown report |
| `GET` | `/api/reports/{job_id}/summary` | Get report summary |
| `GET` | `/api/reports/{job_id}/risks` | Get risk flags |
| `GET` | `/api/graph/{research_id}` | Get identity graph data |
| `GET` | `/health` | Health check |

### Example

```bash
# Start a research investigation
curl -X POST http://localhost:8000/api/research/ \
  -H "Content-Type: application/json" \
  -d '{"target_name": "Timothy Overturf", "target_context": "CEO of Sisu Capital"}'

# Response: {"job_id": "abc-123", "status": "started", ...}

# Poll for status
curl http://localhost:8000/api/research/abc-123/status

# Get the final report
curl http://localhost:8000/api/reports/abc-123
```

### Run Evaluation

```bash
python -m evaluation.evaluator
```

This runs the agent against 3 test personas and outputs precision, recall, and F1 scores to `reports/evaluation_results.json`.

## Testing

```bash
# Unit tests (no API keys required)
pytest tests/unit/ -v

# Integration tests (requires API keys in .env)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=src --cov-report=term-missing
```

## Key Design Decisions

### Multi-Model Strategy

OpenAI GPT-4.1 handles tasks requiring strong reasoning (planning, risk analysis, report writing). Gemini 2.5 handles high-volume data processing (fact extraction, validation) with its large context window. The `ModelRouter` makes swapping or adding models trivial.

### Consecutive Search Strategy

The Planner generates queries in progressive waves — broad identity first, then professional history, financial connections, legal/regulatory, and deep network analysis. Each wave incorporates entities discovered in previous iterations.

### Confidence Scoring

Facts are scored on a 0.0–1.0 scale based on source credibility tier (SEC filings = 0.95, Reddit = 0.35), corroboration count, and cross-reference consistency.

### Identity Graph

Neo4j stores the relationship network with node types (Person, Organization, Event, Location, Document) and relationship types (WORKS_AT, INVESTED_IN, ASSOCIATED_WITH, etc.). Each entity carries source metadata and confidence scores.

## LangSmith Tracing

Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and optionally `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com` (for EU) in `.env` to enable full tracing of every LangGraph node execution in LangSmith. Each search query, LLM call, and state transition is tracked.

## Production Considerations

- **Scalability**: The async FastAPI + ThreadPoolExecutor pattern handles concurrent research jobs. For production scale, swap to Celery or a task queue.
- **Rate limiting**: Token-bucket rate limiter prevents API throttling. Configurable per-service.
- **Error handling**: Each node catches exceptions independently, so partial results are preserved even if one step fails.
- **Neo4j**: Use Neo4j Aura (cloud) for production. The client is a singleton with connection pooling.
