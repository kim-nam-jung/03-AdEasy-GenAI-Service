# Project Structure

## 1. Backend (`/backend`)
Handles all API requests and heavy AI processing.

- **`app/`**: Application core.
  - `api/`: REST endpoints (e.g., `/tasks`).
  - `core/`: Config (`config.py`) and Celery settings.
  - `worker.py`: Celery task entry point.
- **`pipeline/`**: The Core AI Logic.
  - Sequentially executes Step 0 (Preprocessing) through Step 9 (Validation).
- **`common/`**: Helpers used by both App and Pipeline (Logging, Paths, Redis).

## 2. Frontend (`/frontend`)
User interface for managing tasks and viewing results.

- Built with **React** + **TypeScript** + **Vite**.
- **`src/api/`**: Typed API clients.
- **`src/components/`**: Reusable UI blocks.

## 3. Data Flow
1. **User** uploads images via Frontend.
2. **Frontend** calls `POST /api/v1/tasks`.
3. **Backend** queues a Celery Task in Redis.
4. **Worker** picks up the task and runs `pipeline/orchestrator.py`.
5. **Pipeline** generates video and updates status in Redis.
6. **Frontend** polls status and displays the final video.
