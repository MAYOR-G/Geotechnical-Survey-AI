# Geotechnical Survey AI — Engineering Documentation & Technical Report Studio

An AI-powered offshore and oil & gas geotechnical engineering documentation studio combining a persistent Knowledge & Style Vault, a "Verify-First" 4-agent pipeline (`Intake & Clarification` -> `Research` -> `Style-Cloner Drafting` -> `QA & Anti-AI Humanizer`), a Split-Screen Rich Document Editor + Live Paginated A4 PDF Preview, deterministic `pandas` coordinate table parsing, and dual export to Master `.pdf` (with merged external lab PDF attachments) and editable `.docx`.

## Architecture

- **`apps/web`** — Next.js 14+ App Router, TypeScript, Tailwind CSS (Cupertino Studio design system), TipTap Rich Editor, Zustand, TanStack Query, and self-contained `@/components/prestigeui/*` conversational & reasoning components.
- **`apps/api`** — Python 3.11 FastAPI, SQLAlchemy 2.0 Async, Pydantic v2, `pandas`/`openpyxl` deterministic table parser, `python-docx` Word compiler, `WeasyPrint` / `PyMuPDF` + `pypdf` A4 PDF compiler & attachment merger, and SSE multi-agent streaming.

## Local Development Quickstart

### 1. Start the Backend (`apps/api`)
```bash
cd "apps/api"
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend (`apps/web`)
```bash
cd "apps/web"
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to configure your identity in `/settings`, index real historical reports in `/vault`, query live cited sources in `/research`, and generate reports in Document Studio. See [SETUP.md](./SETUP.md) for complete setup instructions and live verification steps.

## Key Modules & Routes

- `/dashboard` — Client Project Folders grid & workspace summary metrics.
- `/projects/new` — 3-step Project Setup, Raw Intake File Uploader (`.xlsx`/`.csv`/notes) & Verify-First Clarification Q&A Checklist.
- `/projects/[id]/studio` — Split-Screen Studio: Agent Chat with live `ReasoningSteps` & `CitedAnswer` on the left, toggleable **Edit Document** (TipTap + Highlight-to-Prompt AI + Smart Image Placeholders) and **Live A4 PDF Style Preview** on the right, plus external PDF attachment merging and `.pdf`/`.docx` export.
- `/vault` — Knowledge & Style Vault (Past Reports, Author Style Fingerprint & Banned AI Clichés, Equipment & Field Gallery).
- `/research` — Standalone citation-backed Research Assistant.
- `/settings` — Contractor/Author defaults, logos, digital signature, and OpenRouter/Tavily API configuration.
