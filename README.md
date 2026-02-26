# Deep Research AI Agent

Autonomous research agent for intelligence gathering, risk assessment, and due diligence investigations. Built with LangGraph for orchestration, multi-model AI (OpenAI GPT-4.1 + Gemini Flash) routed through OpenRouter, Tavily search, and Neo4j for identity graph generation.

## Architecture

```
FastAPI API
  └── ResearchService
        └── LangGraph StateGraph
              ├── Planner      → generates search queries         (OpenAI GPT-4.1)
              ├── Searcher     → executes web searches            (Tavily, concurrent)
              ├── Extractor    → extracts structured facts        (OpenAI GPT-4.1)
              ├── Analyzer  ─┐ → identifies risks & patterns      (OpenAI GPT-4.1)
              ├── Scorer    ─┤ → confidence scoring (parallel)    (OpenAI GPT-4.1)
              ├── Validator  ─┘ → sufficiency check (fan-in)      (OpenAI GPT-4.1)
              │     ├── [needs more] → back to Planner
              │     └── [sufficient] → Reporter
              └── Reporter     → final report + Neo4j graph       (Gemini Flash)
```

All models are routed through **OpenRouter** (`https://openrouter.ai/api/v1`). OpenAI GPT-4.1 handles planning, extraction, analysis, scoring, and validation. Gemini 3 Flash Preview handles report generation. Each provider has an automatic cross-provider fallback.

The agent runs iterative research loops. Each iteration: plan queries → search the web → extract facts → analyze risks + score confidence (in parallel) → check sufficiency → continue or report.

## Project Structure

```
src/
├── config/          # Pydantic Settings, model routing constants
├── models/          # AI model providers (OpenAI, Gemini via OpenRouter) + router
├── graphs/          # LangGraph state, nodes, edges, compiled graph
│   ├── nodes/       # planner, searcher, extractor, analyzer, scorer, validator, reporter
│   └── edges/       # conditional routing logic
├── tools/           # Tavily search wrapper
├── db/              # Neo4j client, Cypher queries, identity graph builder
├── api/             # FastAPI app, routers, controllers, Pydantic schemas
├── services/        # Research orchestration, scoring
└── utils/           # Logging, LLM retry/fallback, robust JSON parsing, prompt templates

evaluation/          # Test personas, evaluator, metrics (precision/recall/F1)
tests/               # Unit and integration tests
```

## Setup

### Prerequisites

- Python 3.11+
- Neo4j (Aura cloud or local instance)
- API keys for: OpenRouter, Tavily
- (Optional) LangSmith for tracing

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
```

### Configuration

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your actual API keys
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key (routes both OpenAI and Gemini) |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | OpenAI model for most tasks (default: `openai/gpt-4.1`) |
| `GEMINI_MODEL` | Gemini model for reporting (default: `google/gemini-3-flash-preview`) |
| `TAVILY_API_KEY` | Tavily search API key |
| `NEO4J_URI` | Neo4j connection URI |
| `NEO4J_USERNAME` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `NEO4J_DATABASE` | Neo4j database name |
| `LANGSMITH_API_KEY` | (Optional) LangSmith API key for tracing |
| `MAX_RESEARCH_ITERATIONS` | Number of research loops (default: 5) |
| `CONFIDENCE_THRESHOLD` | Minimum confidence for sufficiency (default: 0.7) |

## Usage

### API Server

```bash
uvicorn src.api.app:app --reload --port 8000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/research/` | Start a new research investigation |
| `GET` | `/api/research/{job_id}/status` | Check research progress |
| `GET` | `/api/research/{job_id}/result` | Get structured results (facts, risks, connections) |
| `GET` | `/api/reports/{job_id}` | Get full markdown report |
| `GET` | `/api/reports/{job_id}/summary` | Get report summary |
| `GET` | `/api/reports/{job_id}/risks` | Get risk flags |
| `GET` | `/api/graph/{research_id}` | Get identity graph data from Neo4j |
| `GET` | `/health` | Health check |

### Example

```bash
# Start a research investigation
curl -X POST http://localhost:8000/api/research/ \
  -H "Content-Type: application/json" \
  -d '{"target_name": "Timothy Overturf", "target_context": "CEO of Sisu Capital"}'

# Poll for status
curl http://localhost:8000/api/research/{job_id}/status

# Get the full report
curl http://localhost:8000/api/reports/{job_id}

# Get risk flags
curl http://localhost:8000/api/reports/{job_id}/risks

# Get structured results (facts, risks, connections, confidence stats)
curl http://localhost:8000/api/research/{job_id}/result
```

### Report Output

Reports are saved to `reports/` as markdown files and include:

- **Metadata header** — prepared by Elile Research Agent, timestamps, iteration/fact/risk counts, confidence stats
- **LLM-generated sections** — executive summary, subject profile, key findings (by category with confidence scores), risk assessment table, connection map, source assessment, recommendations, and sources consulted
- **Code-generated appendices** — complete tables of all extracted facts, risk flags, connections, and search queries (never omitted or summarized)

### Neo4j Identity Graph

After each run, the agent builds an identity graph in Neo4j with:

- **Person** nodes (target subject + discovered associates)
- **Organization** nodes (companies, firms)
- **Document** nodes (source articles with URLs and confidence)
- **Labeled relationships** (e.g., CEO_FOUNDER, FATHER_ASSOCIATE) with descriptions and confidence scores

View it in the Neo4j Aura console with:

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
```

## Evaluation

```bash
python -m evaluation.evaluator
```

Runs the agent against 3 test personas (varying difficulty) and outputs precision, recall, and F1 scores to `reports/evaluation_results.json`.

## Testing

```bash
# Unit tests (no API keys required)
pytest tests/unit/ -v

# Integration tests (requires API keys in .env)
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=src --cov-report=term-missing
```
