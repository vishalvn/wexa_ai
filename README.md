# DataPulse — Real-Time Analytics & Reporting Platform

A production-grade SaaS analytics platform built with FastAPI + Next.js 14.

---

## Architecture Overview

```
dataplatform/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/               # Route handlers (Routers)
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── events.py
│   │   │   │   ├── dashboards.py
│   │   │   │   ├── widgets.py
│   │   │   │   ├── alerts.py
│   │   │   │   └── reports.py
│   │   ├── core/              # Config, security, dependencies
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/            # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── event.py
│   │   │   ├── dashboard.py
│   │   │   └── alert.py
│   │   ├── schemas/           # Pydantic v2 request/response models
│   │   │   ├── auth.py
│   │   │   ├── event.py
│   │   │   ├── dashboard.py
│   │   │   └── alert.py
│   │   ├── services/          # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── event_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── alert_service.py
│   │   ├── repositories/      # Database query layer
│   │   │   ├── base.py
│   │   │   ├── user_repo.py
│   │   │   ├── event_repo.py
│   │   │   └── dashboard_repo.py
│   │   ├── tasks/             # Celery background tasks
│   │   │   ├── celery_app.py
│   │   │   ├── event_tasks.py
│   │   │   └── alert_tasks.py
│   │   ├── websocket/         # Real-time WebSocket handlers
│   │   │   └── manager.py
│   │   └── main.py            # FastAPI app entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── (auth)/            # Auth pages (login, signup)
│   │   ├── (dashboard)/       # Protected dashboard pages
│   │   │   ├── dashboards/
│   │   │   ├── alerts/
│   │   │   └── settings/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── charts/
│   │   ├── dashboard/
│   │   └── ui/
│   ├── lib/
│   │   ├── api.ts             # Axios API client
│   │   ├── auth.ts
│   │   └── store.ts           # Zustand state
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Layer Explanation (for beginners)

The backend follows Clean Architecture with 4 strict layers:

1. **Routers (api/)** — Handle HTTP requests only. No logic here.
2. **Services (services/)** — All business logic lives here.
3. **Repositories (repositories/)** — All database queries live here.
4. **Models (models/)** — SQLAlchemy table definitions.

This means: Router calls Service → Service calls Repository → Repository talks to DB.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend API | FastAPI (Python 3.11) | Async-native, auto OpenAPI docs |
| Database | PostgreSQL + SQLAlchemy 2.0 async | Reliable, async queries |
| Migrations | Alembic | Version-controlled schema changes |
| Task Queue | Celery + Redis | Async background processing |
| Caching | Redis | Fast query result caching |
| Real-Time | WebSockets (FastAPI/Starlette) | Live dashboard updates |
| Frontend | Next.js 14 App Router + TypeScript | Modern React with SSR |
| UI | Tailwind CSS + Shadcn/UI | Fast, accessible components |
| Charts | Recharts | React-native charting |
| State | Zustand | Lightweight state management |
| Auth | JWT (access + refresh) + bcrypt | Industry standard |

---

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/analytics
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-256-bit-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=your-app-password
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Quick Start (Docker)
```bash
git clone https://github.com/vishalvn/Wexa-AI-assignment
cd Wexa-AI-assignment
cp backend/.env.example backend/.env   
docker-compose up --build
```

App will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
alembic upgrade head        
uvicorn app.main:app --reload --port 8000
```

**Celery Worker (separate terminal):**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Documentation

FastAPI auto-generates interactive docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Running Tests
```bash
cd backend
pytest tests/ -v --asyncio-mode=auto
```
