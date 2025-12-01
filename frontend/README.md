## Frontend – Liquid Ads UI

This directory contains the **React + Vite** frontend for Liquid Ads. It provides:
- **Campaign overview and detail views**
- **Target group and asset management**
- A **campaign graph visualisation** of the creative optimisation pipeline

The frontend talks to the FastAPI backend defined in `../backend`.

---

## 1. Prerequisites

- **Node.js**: Recent LTS (e.g. 20.x)
- **npm** (comes with Node) or an alternative like `pnpm`/`yarn` (examples below use npm)

---

## 2. Install Dependencies

From the `frontend/` directory:

```bash
cd frontend
npm install
```

This installs all dependencies specified in `package.json`:
- React, React DOM
- Vite
- Tailwind CSS
- Radix UI components
- TanStack Router and React Query
- React Flow (`@xyflow/react`) for the campaign graph

---

## 3. Development Server

Start the Vite dev server:

```bash
cd frontend
npm run dev
```

By default, Vite will start on a port like `5173`. The terminal output will show the exact URL, e.g.:

```text
  Local:   http://localhost:5173/
```

Open that URL in your browser. For a fully functioning experience, run the **backend** in parallel (see `../backend/README.md`).

---

## 4. Production Build & Preview

To create an optimised production build:

```bash
cd frontend
npm run build
```

The compiled assets will be output to the `dist/` directory.

To preview the production build locally:

```bash
npm run preview
```

This will start a local server that serves the `dist/` assets.

---

## 5. Project Structure (Frontend)

Key parts of the app:

- `src/main.tsx` – React entrypoint, router setup.
- `src/routes/` – route definitions:
  - `index.tsx` – dashboard / landing page.
  - `campaigns/` – listing, new campaign, and `$campaignId` views (including `flow.tsx` for the graph).
  - `assets.tsx`, `target-groups.tsx` – management views.
- `src/components/campaign-graph/` – campaign graph visualisation and supporting components.
- `src/lib/api/` – API client and hooks (`useCampaigns`, `useTargetGroups`, `useAssets`, etc.).
- `src/components/ui/` – shared UI primitives (button, dialog, inputs, etc.).

---

## 6. Connecting to the Backend

The frontend expects an API base URL configured in the API client (see `src/lib/api/client.ts`).  
If needed, adjust it to match your backend address, e.g. `http://localhost:8000`.

Typical setup for local development:

1. Start the **backend** (FastAPI) – see `../backend/README.md`.
2. Start the **frontend** dev server:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open the printed local URL in your browser and interact with campaigns, target groups, and assets.


