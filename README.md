# AdEasy GenAI Service

AI-powered short video generation service for small businesses.

## 🚀 Quick Start

### 1. Run with Docker (Recommended)
Everything (Backend, Frontend, Redis) is containerized.

```bash
docker-compose up --build
```
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000/docs

## 📁 Simple Structure
The project is strictly divided into Frontend and Backend.

```text
AdEasy-GenAI-Service/
├── backend/            # Python (FastAPI + Celery + PyTorch)
│   ├── app/            # API & Worker Logic
│   ├── pipeline/       # AI Generation Steps (FastSAM, SDXL, WanI2V)
│   ├── common/         # Shared Utilities
│   └── Dockerfile
│
├── frontend/           # TypeScript (React + Vite)
│   ├── src/            # UI Components & Pages
│   └── Dockerfile
│
├── docker-compose.yml  # Service Orchestration
└── .env                # Environment Variables
```

## 🔧 Tech Stack
- **Languages**: Python 3.11, TypeScript
- **Frameworks**: FastAPI, React
- **Infrastructure**: Docker, Redis, Celery
- **AI Models**: Qwen3-VL, SDXL, Wan I2V
