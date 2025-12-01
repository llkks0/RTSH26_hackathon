## RTSH 26 Hackathon – Liquid Ads

This repository contains our Road to START Hack 2026 hackathon project: **Liquid Ads**, a self‑optimising creative ads engine that generates, evaluates, and iteratively improves image ads using the **Black Forest Labs Flux 2** model.

The project is split into:
- **`backend/`**: FastAPI service orchestrating campaigns, assets, image generation and evaluation.
- **`frontend/`**: React + Vite UI for browsing campaigns, target groups, assets, and the creative optimisation flow.

### Backend – Quick Start

See the detailed instructions in `backend/README.md`. In short:

1. **Install uv** (Python package/dependency manager).
2. **Install backend deps**:
   ```bash
   cd backend
   uv sync
   ```
3. **Start Postgres via Docker Compose**:
   ```bash
   docker compose up -d
   ```
4. **Create `.env` with your API keys and config** (see `backend/README.md` for details).
5. **Run the backend**:
   ```bash
   uv run src/main.py
   ```

### Frontend – Quick Start

See `frontend/README.md` (or the section below if viewing the repo root).

1. **Install Node.js** (LTS) and npm.
2. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```
3. **Run the dev server**:
   ```bash
   npm run dev
   ```
4. Open the printed local URL in your browser (`http://localhost:5173`) while the backend is running.

### High‑Level Architecture

- **Campaigns & Target Groups**: Define who we are targeting and what we want to optimise.
- **Assets & Image Generation**: Manage base assets, prompts and generated images for each target group.
- **Evaluation & Iteration**: Evaluate performance, select top images, and generate improved creatives.
- **Frontend UI**: Visualises the campaign graph and supports asset selection and iteration workflows.

For more details, see:
- `backend/README.md` for API and pipeline details.
- `frontend/README.md` source for the campaign graph UI and data fetching.

