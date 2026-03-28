# FinBot — Advanced RAG Application
FinBot is a production-grade RAG application developed for FinSolve Technologies (fictional). It enables employees to query internal knowledge bases via natural language, featuring strict Role-Based Access Control (RBAC) integrated directly into the vector retrieval layer

## High-level system architecture
<img width="766" height="620" alt="image" src="https://github.com/user-attachments/assets/534d2b35-e5b8-46cd-adbe-6e0d4e8e2a33" />

## Setup Instructions

### Prerequisites
- Python 3.12
- Node.js 22
- Docker

### Backend Setup
```bash
cd C:\Infinity\dev\finbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Start Qdrant
```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Run Ingestion
```bash
python backend/ingestion/ingest.py
```

### Start Backend
```bash
uvicorn backend.api.main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

## Demo Credentials
| Username | Password | Role |
|---|---|---|
| alice | alice123 | employee |
| bob | bob123 | finance |
| charlie | charlie123 | engineering |
| diana | diana123 | marketing |
| eve | eve123 | c_level |

## Architecture
- **Docling** — hierarchical document parsing
- **Qdrant** — vector database with RBAC metadata filtering
- **semantic-router** — intent-based query routing
- **Claude (Anthropic)** — LLM response generation
- **FastAPI** — REST API backend
- **Next.js** — frontend UI

## RAGAs Ablation Results
| Metric | Score |
|---|---|
| Faithfulness | 0.1451 |
| Answer Relevancy | 0.6259 |
| Context Precision | 0.9487 |
| Context Recall | 1.0000 |
| Answer Correctness | 0.3587 |

## Tool Substitutions & Justifications
- **Claude instead of OpenAI** — Strong instruction following,
  excellent for grounded RAG responses
- **FastEmbedEncoder instead of HuggingFaceEncoder** — Better
  compatibility with semantic-router 0.1.2
- **Query expansion** — Added to improve retrieval accuracy
  for queries that don't match document wording exactly
