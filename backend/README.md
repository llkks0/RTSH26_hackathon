## Backend – Liquid Ads API & Orchestration

This directory contains the **FastAPI backend** for Liquid Ads. It manages:
- **Campaigns, target groups, and assets**
- **Image generation pipelines** (prompt creation, asset selection, image generation)
- **Evaluation and iteration** of generated creatives

It is built with **FastAPI**, **SQLModel** and **Postgres**, and uses **uv** for Python dependency management.

---

## 1. Prerequisites

- **Python**: \(>= 3.10 – the project is configured for a modern Python; use a recent 3.x\)
- **uv**: Python package/dependency manager  
  Install instructions: see the official docs `https://docs.astral.sh/uv/getting-started/installation/`
- **Docker & Docker Compose**: to run Postgres locally

---

## 2. Install Python Dependencies

From the `backend/` directory:

```bash
uv sync
```

This creates a virtual environment managed by uv and installs all dependencies defined in `pyproject.toml`.

To run commands inside the environment you can either:

- Prefix with `uv run`, e.g.:
  ```bash
  uv run src/main.py
  ```
- Or activate the environment (see uv docs) if you prefer a traditional venv workflow.

---

## 3. Start Postgres with Docker

We use a local Postgres instance defined in `docker-compose.yml`.

```bash
docker compose up -d
```

This will start a Postgres container with:
- **Database**: `project_database`
- **User**: `user`
- **Password**: `password`
- **Port**: `5432` on your host

You can stop it later with:

```bash
docker compose down
```

---

## 4. Environment Variables

Create a `.env` file in the `backend/` directory for all required secrets and configuration.

You can copy the example `.env.example` file:

```bash
cp .env.example .env
```

Then edit `.env` and fill in the values. The required variables include:

```bash
# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
# Black Forest Labs API key
BFL_API_KEY=your_bfl_api_key_here

# Database configuration (must match docker-compose.yml)
DATABASE_URL=postgresql://user:password@localhost:5432/project_database
```

---

## 5. Run the Backend Server

```bash
uv run src/main.py
```

This will start the FastAPI app (on `http://localhost:8000`).

Check `src/main.py` to confirm the entrypoint (`app`) and port.

---

## 6. Project Structure (Backend)

Some key modules:

- `src/main.py` – FastAPI app entrypoint.
- `src/functions/` – core pipeline functions:
  - `image_generator.py`, `prompt.py`, `orchestrator.py`, etc.
- `src/campaigns/`, `src/target_groups/`, `src/assets/` – CRUD and business logic for campaigns, target groups and assets.
- `src/steps/` – higher‑level orchestration steps (generate, evaluate, select, deploy, etc.).

---

## 7. Running Tests

```bash
uv run pytest
```

This will execute tests in the `tests/` directory (e.g. `test_evaluate_image_groups.py`).
