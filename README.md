# 🏦 Banking CRM Agent
### Agentic AI for Relationship Manager Outreach

> An intelligent CRM layer that helps Relationship Managers identify high-potential loan
> candidates and generate personalized WhatsApp outreach — powered by **LangGraph**,
> **Groq llama-3.1-8b-instant**, and a **6-factor deterministic scoring engine**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Demo Video](#demo-video)
- [Architecture](#architecture)
- [Execution Flow](#execution-flow)
- [Tool Design](#tool-design)
- [Scoring Engine](#scoring-engine)
- [Agent Design](#agent-design)
- [Key Design Decisions](#key-design-decisions)
- [Trade-offs & Limitations](#trade-offs--limitations)
- [Setup & Run](#setup--run)
- [Demo Scenarios](#demo-scenarios)
- [Future Enhancements](#future-enhancements)
- [Project Structure](#project-structure)

---

## Overview

### The Problem

Relationship Managers at banks manage hundreds of customers. Identifying who to contact,
why they are a good candidate, and crafting a personalized message — manually — takes
hours per campaign.

### The Solution

A conversational agentic AI system where an RM types a natural language query and receives:

- A **ranked list** of high-potential customers scored by conversion likelihood
- **Per-customer reasoning** explaining exactly why they qualify
- **Three personalized WhatsApp message variants** (formal, casual, urgent) per customer — ready to send

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph StateGraph |
| LLM | Groq `llama-3.1-8b-instant` |
| Backend API | FastAPI + WebSocket streaming |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | React 18 + Vite + Tailwind CSS |
| Containerization | Docker + docker-compose |

---

## 🎬 Demo Video

> Full walkthrough of the system — architecture, live demo of all 3 scenarios, and design trade-offs.

| | |
|---|---|
| **Duration** | 8 minutes |
| **Platform** | Google Drive |
| **Link** | [▶ Watch Demo Video](https://drive.google.com/file/d/1dNOpBoLD2xhnCtq7cgqOvGz8GuQKyEy-/view?usp=sharing) |

### What the demo covers:
- System architecture walkthrough (LangGraph, scoring engine, tools)
- Scenario 1: Full pipeline — find leads + generate WhatsApp messages
- Scenario 2: Filtered query + follow-up context handling
- Scenario 3: Single customer deep dive + comparison reasoning
- Design decisions and trade-offs

---

## Architecture

Open `architecture_diagram.html` (at the project root) for a fully interactive visual diagram.

### System Layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│  👤  Relationship Manager — types natural language query                 │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │  WebSocket  ws://localhost:8000/ws/chat
┌──────────────────────────▼───────────────────────────────────────────────┐
│  FRONTEND  React 18 + Vite + Tailwind                                    │
│  ┌─────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐│
│  │  Chat UI         │  │  Scored Leads Panel  │  │  WhatsApp Messages   ││
│  │  Streaming resp. │  │  Real-time, animated │  │  3 tone variants     ││
│  └─────────────────┘  └──────────────────────┘  └──────────────────────┘│
└──────────────────────────┬───────────────────────────────────────────────┘
                           │  FastAPI  port 8000
┌──────────────────────────▼───────────────────────────────────────────────┐
│  BACKEND  FastAPI + LangGraph StateGraph                                 │
│                                                                           │
│  understand_intent → retrieve_customers → score_customers                │
│       → filter_candidates → generate_messages → synthesize_response      │
│                                                                           │
│  AgentState (TypedDict) flows immutably through all 6 nodes              │
└──────────────┬──────────────────────────────┬────────────────────────────┘
               │ SQL queries                  │ Groq API calls
┌──────────────▼──────────┐    ┌──────────────▼────────────────────────────┐
│  SQLite Database         │    │  Groq  llama-3.1-8b-instant               │
│  50 customers            │    │  Intent parsing · Message generation      │
│  ~800 transactions       │    │  Response synthesis                       │
│  Loan enquiries          │    │                                           │
│  SQLAlchemy ORM          │    │                                           │
└─────────────────────────┘    └───────────────────────────────────────────┘
```

**API Endpoints**

| Method | Path | Description |
|--------|------|-------------|
| `WS` | `/ws/chat` | WebSocket — real-time agent streaming |
| `GET` | `/api/customers` | Scored customer list with filters |
| `GET` | `/api/customers/{id}` | Full customer profile + scoring |
| `POST` | `/api/messages/generate` | On-demand message generation |
| `GET` | `/health` | System health check |
| `GET` | `/docs` | Swagger UI |

---

## Execution Flow

Walkthrough for: *"Find high-value customers for personal loan and generate messages"*

```
[0 ms]     RM types query in Chat UI
[~10 ms]   WebSocket opens to ws://localhost:8000/ws/chat

[~800 ms]  [understand_intent] — Groq LLM call
           → intent: "find_leads", filters: {}, top_n: 8
           → Streaming: {type:"thinking", step:"understand_intent"}

[~850 ms]  [retrieve_customers] — SQLAlchemy query
           → Tool: get_customers_by_criteria(filters={})
           → Returns 50 customers + transactions + enquiries
           → Streaming: {type:"thinking", step:"retrieve_customers"}

[~900 ms]  [score_customers] — pure Python, no LLM
           → Tool: score_and_recommend_customers(customers=50)
           → 6-factor weighted scoring → ranked list with reasoning

[~910 ms]  [filter_candidates] — select top N above threshold
           → Top 8 customers above 40.0 score threshold
           → Product recommendations attached per customer
           → Streaming: {type:"customers_ready", data:[...]}
              ↳ Frontend right panel populates HERE — before messages

[~3000 ms] [generate_messages] — 1 batched Groq call
           → Tool: generate_whatsapp_messages(customers=8, variants=3)
           → Returns JSON with formal/casual/urgent per customer
           → Streaming: {type:"partial_result", messages:[...]}

[~5000 ms] [synthesize_response] — Groq LLM call
           → 2-sentence executive summary + markdown table
           → Streaming: {type:"text", content:"..."} (chunked)

[~5100 ms] WebSocket closes — RM sees full response
```

---

## Tool Design

| Tool | Purpose | Input | Output | Called By |
|------|---------|-------|--------|-----------|
| `get_customers_by_criteria()` | Fetch customers from DB with dynamic filters | city, occupation, min/max credit, min/max income, days_since_enquiry | List of customer dicts + transactions + enquiries | `retrieve_customers` node |
| `score_and_recommend_customers()` | Score all customers on 6 factors, attach products | Customer list, transactions map, enquiries map | Scored customers sorted by conversion_score | `score_customers` node |
| `generate_whatsapp_messages()` | Generate 3 tone variants via single Groq call | Customer dict, product dict | `[{tone, content}]` × 3 | `generate_messages` node |
| `get_customer_by_name()` | Fetch a single customer by partial name | Name string | Full profile + transactions + enquiries | `retrieve_customers` (single-customer intents) |
| `score_customer()` | Score one customer | Customer dict, transactions, enquiries | Scored dict with breakdown + reasoning | `retrieve_customers` (regenerate_message shortcut) |
| `recommend_product()` | Match customer to best loan product | Scored customer dict | Product dict or None | `score_customers` node |

### Batched Message Generation

Rather than making 1 LLM call per customer per tone (= 24 calls for 8 customers × 3 tones),
`generate_whatsapp_messages` uses a **single batched call** returning a JSON object with all
three variants at once. This reduces latency and API cost by ~24×.

---

## Scoring Engine

The scoring engine is **fully deterministic and explainable** — no LLM involved. Each customer
is scored 0–100 across 6 weighted factors. An RM or compliance officer can audit every number.

### Factors and Weights

| Factor | Weight | Formula | Signal |
|--------|--------|---------|--------|
| Income Stability | **25%** | `salary_credits_last_3mo / 3` (salaried) | Consistent employment |
| Credit Score | **20%** | `(credit_score − 300) / 550` | Creditworthiness |
| DTI Ratio | **20%** | `1 − (total_emi / monthly_income)` | Repayment capacity |
| Account Balance | **15%** | `min(balance / (3 × income), 1)` | Financial buffer |
| Transaction Regularity | **10%** | `min(tx_count_90d / 30, 1)` | Account activity |
| Loan Enquiry Recency | **10%** | `1.0` if <30d · `0.5` if <90d · `0` else | Purchase intent |

### Score Normalization

```python
# Raw weighted sum spans [0.35, 1.0] for realistic customer profiles.
# Normalize to [0, 100] so all four tiers are reachable:
#   < 40 = weak  |  40–60 = medium  |  60–75 = strong  |  > 75 = prime
_BASE, _SPAN = 0.35, 0.65
conversion_score = max(0.0, min(100.0, (raw_score - _BASE) / _SPAN * 100))
```

### Conversion Probability

```python
noise = random.uniform(-4, 4)   # Simulates real-world prediction uncertainty
conversion_probability = max(0.0, min(100.0, conversion_score * 0.85 + noise))
```

### Product Matching Rules

| Condition | Product |
|-----------|---------|
| Salaried + Income ≥ ₹50k + Credit ≥ 720 | Salaried Premium (10.5–12%) |
| Salaried + Income ≥ ₹25k + Credit ≥ 650 | Salaried Standard (13–16%) |
| Self-Employed + Income ≥ ₹75k + Credit ≥ 680 | Self-Employed Loan (14–18%) |
| Existing loan + Credit ≥ 700 | Top-Up Loan (11–13%) |

---

## Agent Design

### LangGraph StateGraph

```
understand_intent
       ↓
retrieve_customers
       ↓  [conditional routing]
       ├─ greeting / 0 customers → synthesize_response (skip)
       ├─ regenerate_message     → generate_messages  (skip scoring)
       └─ default                → score_customers
                                        ↓
                               filter_candidates
                                        ↓  [conditional routing]
                                        ├─ explain / compare / aggregate → synthesize_response
                                        └─ default                       → generate_messages
                                                                                ↓
                                                                    synthesize_response
                                                                            ↓
                                                                          END
```

### Conditional Routing

**After `retrieve_customers`:**
- `greeting` or zero results → skip to `synthesize_response` immediately
- `regenerate_message` intent with a named customer already scored → skip to `generate_messages`
- Default → `score_customers`

**After `filter_candidates`:**
- `explain_customer`, `compare_customers`, `aggregate_summary` → skip to `synthesize_response` (no messages needed)
- Zero recommended customers → `synthesize_response` with helpful "no results" message
- Default → `generate_messages`

### AgentState Schema

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]  # conversation history
    rm_query: str                        # original query
    intent: str                          # find_leads | filtered_search | deep_dive |
                                         # regenerate_message | explain_customer |
                                         # compare_customers | aggregate_summary | greeting
    filters: Dict[str, Any]              # city, income, credit, occupation, days_since_enquiry
    raw_customers: List[Dict]            # from DB
    transactions_by_customer: Dict       # customer_id → [transaction dicts]
    enquiries_by_customer: Dict          # customer_id → [enquiry dicts]
    scored_customers: List[Dict]         # after 6-factor scoring
    recommended_customers: List[Dict]    # top N filtered
    generated_messages: List[Dict]       # WhatsApp variants
    target_customer_name: Optional[str]  # for single-customer queries
    target_customer_name_2: Optional[str]# second customer for compare_customers
    requested_tone: Optional[str]        # formal | casual | urgent
    reasoning: str                       # final RM-facing response text
    thinking_steps: List[Dict]           # streamed to frontend as nodes complete
    current_step: str
    error: Optional[str]
    top_n: int
```

### Intent Parser — Two-Layer Design

The `understand_intent` node uses **regex pre-checks before the LLM** for high-confidence patterns:

1. **Regex layer** (~0 ms): greetings, compare queries, aggregate summaries, single-customer message regeneration, bulk generate patterns — all intercepted deterministically.
2. **LLM layer** (~700 ms): only reached for ambiguous queries requiring language understanding (filter extraction, implicit intent).

This prevents the LLM from being a latency bottleneck for predictable patterns and avoids
common misclassifications (e.g., bulk "find and generate" → `regenerate_message`).

---

## Key Design Decisions

### 1. LangGraph StateGraph over a simple LLM chain

**Decision:** Use LangGraph `StateGraph` instead of a sequential chain.  
**Rationale:** Each node is independently testable and debuggable. State is explicit and
inspectable at every step. Routing logic is code, not emergent LLM behavior. Adding a new
capability means adding a new node — not refactoring a monolithic chain. Critical for
production banking systems that need auditable reasoning chains.

### 2. Deterministic scoring over ML

**Decision:** Rule-based weighted scoring engine, zero LLM dependency.  
**Rationale:** Explainable and auditable — an RM or compliance officer can understand exactly
why a customer scored 84.9. No training data required. Weights are configurable. The tool
interface is identical to what an ML model would expose — swappable when data becomes available.

### 3. Batched message generation (1 call vs. 24)

**Decision:** Single LLM call for all customers and all tone variants.  
**Rationale:** Generating messages for 8 customers × 3 tones sequentially = 24 API round trips.
Batching reduces this to 1 call with structured JSON output. At production scale this
difference is significant for both latency (~3s vs. ~30s) and cost.

### 4. Two-layer intent parsing (regex + LLM)

**Decision:** Deterministic pre-checks intercept high-confidence patterns before the LLM.  
**Rationale:** Greetings, compare queries, and aggregate summary requests are handled by regex
in <1ms — no LLM call, no latency. Only genuinely ambiguous queries invoke the LLM. This
prevents the intent parser from becoming a latency bottleneck and eliminates a class of
LLM misclassifications (e.g., hallucinating customer names on bulk queries).

### 5. WebSocket streaming over REST polling

**Decision:** WebSocket with server-sent events for agent progress.  
**Rationale:** The pipeline takes 5–10 seconds end-to-end. Polling would show a blank screen.
Streaming surfaces each node's progress in real time — crucially, customers appear in the right
panel as soon as scoring completes (~910ms), long before message generation finishes (~3000ms).
Better UX, identical backend complexity.

### 6. SQLAlchemy ORM with production-shaped schema

**Decision:** All DB access through SQLAlchemy models, no raw SQL.  
**Rationale:** SQLite for the demo — PostgreSQL for production. Switching is a single
`DATABASE_URL` environment variable change. The schema (customers, transactions, loan_enquiries)
is production-shaped with proper FK relationships and indexable fields.

---

## Trade-offs & Limitations

### 1. SQLite is not production-ready

SQLite cannot handle concurrent writes from multiple RMs. A bank running this for 50 RMs
simultaneously would need PostgreSQL. The ORM layer makes this a configuration change,
not a code change.

### 2. Scoring weights are hand-tuned

The 6 weights were set based on domain logic, not trained on historical conversion data.
A bank with conversion history could train an XGBoost or logistic regression model and drop
it into the same tool interface — the `score_and_recommend_customers` signature is unchanged.

### 3. No authentication or multi-tenancy

The system has no login, no RM identity, no role-based access. Session isolation exists
per `session_id` but anyone with the URL can access all customer data. Production would
require OAuth2 + row-level security scoping each RM to their assigned portfolio.

### 4. LLM hallucination risk in messages

Despite compliance validation and forbidden-terms checking, the LLM could generate subtly
inaccurate statements about loan terms. Production would require a compliance review step
before messages reach customers (a rule-engine or fine-tuned classifier node).

### 5. In-memory session state

Session follow-up state (`_session_cache` in `chat.py`) is in-process memory. It resets on
server restart and doesn't work across multiple backend instances. Production would use
Redis as the session store, enabling multi-instance horizontal scaling.

---

## Setup & Run

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key — free at [console.groq.com](https://console.groq.com)

### Quick Start (Docker)

```bash
git clone <repo-url>
cd banking-crm-agent

# Configure
cp .env.example backend/.env
# Edit backend/.env — set GROQ_API_KEY=gsk_...

# Start everything
docker-compose up --build

# Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Windows — one command

```bat
start.bat
```

Checks for `GROQ_API_KEY`, launches backend and frontend in separate windows,
waits for backend readiness, then opens the browser.

### Mac/Linux — one command

```bash
chmod +x start.sh && ./start.sh
```

### Manual Setup

**Backend:**

```bash
# From the banking-crm-agent/ directory
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Configure
cp ../.env.example .env
# Edit .env — set GROQ_API_KEY=gsk_...

# Run (must be run from project root so 'from backend.xxx' imports resolve)
cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### Verify Installation

```bash
curl http://localhost:8000/health
# {"status":"ok","model":"llama-3.1-8b-instant","app":"Banking CRM Agent"}
```

### Run Tests

```bash
# From banking-crm-agent/ directory (with venv activated)
python -m pytest tests/ -v

# Expected: 49+ tests passing
# test_scoring.py        — 29 tests — scoring engine unit tests (no LLM)
# test_intent_parser.py  — 30 tests — intent parser unit tests (no LLM)
# test_api.py            — REST API smoke tests
```

---

## Demo Scenarios

### Scenario 1 — Full Pipeline

**Query:** `"Find high-value customers likely to convert for a personal loan this month and generate personalized WhatsApp messages"`

**What the agent does:**
- Intent parsed as `find_leads`, `generate_messages: true`
- All 50 customers retrieved and scored
- Top 8 above threshold returned with score reasoning
- 24 WhatsApp variants generated (8 customers × 3 tones) via 1 LLM call
- Executive summary synthesized

**Expected output:** 8 ranked customers with animated score bars in the right panel,
WhatsApp messages tab populated, LLM-written reasoning per candidate.

---

### Scenario 2 — Filtered Search + Follow-up

**Query:** `"Show salaried customers in Mumbai with credit score above 720"`

**Filters extracted:** `city=Mumbai`, `occupation=SALARIED`, `min_credit_score=720`

**Follow-up:** `"Generate urgent messages for all of them"`

The agent detects this as a follow-up query, re-uses the cached customers from the
prior result, and jumps directly to `generate_messages` with `tone=urgent` — no DB
re-query, no re-scoring.

---

### Scenario 3 — Deep Dive + Comparison

**Query:** `"Why is Arjun Reddy a good candidate for a personal loan?"`

- Single-customer intent detected (`explain_customer`)
- Arjun's full profile fetched including 12 months of transaction history
- LLM generates per-factor reasoning (credit score, salary credits, DTI, recent enquiry)

**Follow-up:** `"Compare Arjun Reddy and Tarun Walia — who should I approach first?"`

- Both profiles fetched in parallel
- Scored side-by-side
- LLM recommends the stronger candidate with margin and reasoning

---

## Future Enhancements

### 1. ML-based conversion scoring

Replace the weighted rules engine with a model trained on historical loan conversion outcomes
(XGBoost / logistic regression). Tool interface is unchanged — drop-in replacement. Features to
add: CIBIL score trend (3-month delta), transaction velocity, seasonal patterns.

### 2. WhatsApp Business API integration

Message objects are already structured with `customer_id`, `tone`, `content`, and `product`.
A thin integration layer connects to WhatsApp Business API for direct RM-initiated sends,
with delivery receipts fed back into the CRM.

### 3. Multi-RM authentication + portfolio scoping

Session isolation already exists per `session_id`. Adding OAuth2 authentication and
SQLAlchemy row-level filtering scopes each RM to their assigned customer portfolio.
No graph changes required.

### 4. Real-time transaction ingestion

Replace the seeded SQLite data with a Kafka consumer reading live transaction events.
Score updates trigger automatically when a customer's profile changes (new salary credit,
new enquiry, large debit). The scoring tool is stateless and re-entrant.

### 5. Compliance review node

Add a node between `generate_messages` and `synthesize_response` that sends messages to
a compliance rule-engine (or fine-tuned classifier) before they reach the RM. Flag and
regenerate non-compliant messages. Critical for production deployment in regulated banking.

---

## Project Structure

```
banking-crm-agent/
├── backend/
│   ├── main.py                    # FastAPI app, lifespan, route registration
│   ├── config.py                  # Pydantic settings — env vars
│   ├── app_state.py               # Runtime mutable LLM config
│   ├── llm_factory.py             # Provider-agnostic LLM factory (Groq/Gemini/Anthropic)
│   ├── agents/
│   │   ├── orchestrator.py        # LangGraph StateGraph + conditional routing
│   │   ├── state.py               # AgentState TypedDict
│   │   └── nodes/
│   │       ├── query_understanding.py   # Node 1: intent + filter extraction
│   │       ├── customer_retrieval.py    # Node 2: DB queries
│   │       ├── scoring.py               # Node 3: run scoring engine
│   │       ├── product_recommender.py   # Node 4: filter top N + products
│   │       ├── message_generator.py     # Node 5: WhatsApp message generation
│   │       └── response_synthesizer.py  # Node 6: final RM-facing response
│   ├── tools/
│   │   ├── db_tools.py            # SQLAlchemy query tools
│   │   ├── scoring_tools.py       # 6-factor scoring engine + product matcher
│   │   └── message_tools.py       # Groq LLM message generation + validation
│   ├── api/
│   │   ├── chat.py                # WebSocket endpoint + session cache
│   │   ├── customers.py           # REST customer endpoints
│   │   └── messages.py            # REST message endpoints
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── seed.py                # 50 customers + realistic transaction history
│   │   └── connection.py          # DB engine + session factory
│   ├── schemas/                   # Pydantic v2 request/response schemas
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Root component, layout
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx  # Chat panel + streaming renderer
│   │   │   ├── CustomerTable.jsx  # Scored leads right panel
│   │   │   ├── CustomerCard.jsx   # Per-customer card with score bar
│   │   │   ├── MessagePreview.jsx # WhatsApp-styled message tabs
│   │   │   ├── AgentThinking.jsx  # Live thinking steps display
│   │   │   └── ScoreCard.jsx      # Score breakdown visualization
│   │   ├── hooks/
│   │   │   └── useAgentStream.js  # WebSocket hook — streaming state manager
│   │   └── lib/
│   │       └── api.js             # REST API helpers
│   ├── index.html
│   ├── vite.config.js             # Vite + proxy to :8000
│   └── package.json
├── tests/
│   ├── test_scoring.py            # 29 scoring engine unit tests
│   ├── test_intent_parser.py      # 30 intent parser unit tests
│   └── test_api.py                # REST API smoke tests
├── architecture_diagram.html      # Interactive system architecture diagram
├── docker-compose.yml
├── .env.example                   # Template — copy to backend/.env
├── .gitignore
├── start.bat                      # Windows one-command startup
├── start.sh                       # Mac/Linux one-command startup
└── README.md
```

---

*Built for the BUSINESSNEXT AI Full Stack Developer take-home assignment.*  
*Stack: LangGraph · Groq llama-3.1-8b-instant · FastAPI · React 18 · SQLAlchemy · SQLite*
