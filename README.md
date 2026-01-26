# AdEasy GenAI Service

**AI-Powered Product Video Generation Platform**

AdEasy allows small businesses and marketers to generate high-quality short promotional videos from a single product image. It leverages an autonomous agentic pipeline to analyze product features, segment images, generate video content, and post-process details—all orchestrated by a Supervisor Agent that continually reflects on quality.

---

## 🌟 Key Features

- **Agentic Orchestration**: Uses a **Supervisor Agent (LangGraph)** to oversee the pipeline, evaluate results at each step, and automatically retry with adjusted parameters if quality standards aren't met.
- **Visual Understanding**: Integrates **GPT-4o Vision** to deeply analyze product images, extracting materials, textures, and optimal selling points to guide video generation.
- **Advanced Video Generation**: Utilizes **LTX-Video (State-of-the-Art)** models running locally on GPU to create consistent and realistic product motion.
- **Robust Architecture**: Built with **FastAPI**, **Celery**, and **Redis** for asynchronous task processing and scalability.
- **Modern Frontend**: A clean, responsive **React + TypeScript** interface for easy user interaction.

---

## 🏗️ Architecture

The system follows a 3-step autonomous pipeline:

1.  **Vision Parsing**: GPT-4o analyzes the input image to understand the product context (Material, Lighting, Scenery).
2.  **Step 1: Segmentation**: Isolates the product from its background using segmentation models.
3.  **Step 2: Video Generation**: Uses **LTX-Video** to animate the static product image based on the vision analysis.
4.  **Step 3: Post-processing**: (Optional) Interpolation (RIFE) and Upscaling (Real-CUGAN) for final polish.

*Throughout this process, a **Supervisor Agent** monitors quality and coordinates retries if necessary.*

---

## 🚀 Quick Start

### Prerequisites
- **Docker** & **Docker Compose** installed.
- **NVIDIA GPU** (Recommended: L4 or A10G with 24GB+ VRAM) with proper drivers and **NVIDIA Container Toolkit** installed.
- **OpenAI API Key** (for the Supervisor Agent & Vision).

### 1. Installation

```bash
git clone https://github.com/your-repo/adeasy-genai-service.git
cd adeasy-genai-service
```

### 2. Environment Setup

Create the `.env` file in the `backend/` directory:

```bash
cp backend/.env.example backend/.env
```

**Edit `backend/.env`** and add your API key:
```ini
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Run with Docker

Start the entire stack (Frontend, Backend, Worker, Redis):

```bash
docker-compose up --build
```

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

*Note: On the first run, the system will download necessary AI models (LTX-Video, etc.) which may take some time depending on your network speed.*

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Task Queue**: Celery + Redis
- **AI/ML**: PyTorch, Diffusers, LangChain, LangGraph
- **Models**: LTX-Video (Video), GPT-4o (Logic/Vision)

### Frontend
- **Framework**: React (Vite)
- **Language**: TypeScript
- **Styling**: TailwindCSS (or similar)

### Infrastructure
- **Containerization**: Docker
- **Deployment Targets**: Google Cloud Platform (L4 GPU recommended), AWS, or On-Premise GPU servers.

---

## 📂 Project Structure

```text
AdEasy-GenAI-Service/
├── backend/            # Python Application
│   ├── app/            # REST API & Worker wiring
│   ├── pipeline/       # Core Agentic Logic (Supervisor, Steps)
│   ├── common/         # Shared utilities
│   ├── tests/          # Pytest suite
│   └── .venv/          # Local dev environment
│
├── frontend/           # React Application
│   ├── src/            # Components & Pages
│   └── public/         # Static assets
│
├── data/               # Local data storage (inputs/outputs)
├── docs/               # Additional documentation
└── docker-compose.yml  # Service definition
```

## � License

This project is licensed under the MIT License.
