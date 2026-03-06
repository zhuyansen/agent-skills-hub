# Agent Skills Hub

An aggregation and dynamic scoring platform for open-source Agent Skills. Crawls GitHub for Agent tools (Claude MCP servers, Codex skills, YouMind plugins, etc.), scores them with a weighted algorithm, and displays results in a searchable web interface.

## Architecture

```
backend/   → Python FastAPI + SQLAlchemy + SQLite
frontend/  → React + TypeScript + Vite + TailwindCSS
```

## Features

- GitHub data scraping with rate limit handling
- Dynamic scoring algorithm (0-100) with time decay penalty
- Hourly automated sync via APScheduler
- RESTful API with pagination, filtering, sorting
- Card/Table view toggle, category filters, search
- Responsive design

## Quick Start

### Backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App at http://localhost:5173

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/skills` | Paginated skill list (sort, search, filter) |
| GET | `/api/skills/category/{name}` | Filter by category |
| GET | `/api/skills/{id}` | Single skill detail |
| POST | `/api/sync` | Trigger background GitHub sync |
| GET | `/api/stats` | Summary statistics |
| GET | `/api/categories` | Category list with counts |

## Environment Variables

See `backend/.env.example`:

```
GITHUB_TOKEN=ghp_xxxxx          # Required: GitHub Personal Access Token
DATABASE_URL=sqlite:///./skills_hub.db
SYNC_INTERVAL_HOURS=1
CORS_ORIGINS=http://localhost:5173
```

## Scoring Algorithm

See [docs/scoring-algorithm.md](docs/scoring-algorithm.md) for the full design document.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic, SQLAlchemy, httpx, APScheduler
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS v4
- **Database**: SQLite
