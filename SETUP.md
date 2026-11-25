# Geotechnical Survey AI — Setup & Owner Launch Guide

**Geotechnical Survey AI** boots in a 100% clean-slate state (`0` projects, `0` indexed Vault reports, `0` gallery assets, `0` research threads, and blank default workspace identity). Every workflow relies strictly on live database persistence, deterministic spreadsheet/document parsing, native **Typst** A4 typesetting, **Matplotlib** scientific plotting, and live **OpenRouter + Tavily** API calls—with zero mock responses, zero fake timers, and zero canned fallbacks.

---

## 1. Prerequisites & System Dependencies

Ensure the following tools are installed on your machine before starting:

- **Node.js `v20+`** and **`npm`**:
  ```bash
  node -v   # v20.x or newer
  ```
- **Python `3.11+`**:
  ```bash
  python3 --version   # 3.11+
  ```
- **No external LaTeX or Homebrew Cairo/Pango installation required:**
  `apps/api/requirements.txt` bundles the native Rust-backed **`typst`** Python compiler (`typst>=0.12.0`), **`matplotlib>=3.9.0`**, **`pymupdf`**, **`pypdf`**, **`pandas`**, and **`python-docx`** directly inside `.venv`.
- **Optional (Containerized Launch):** **Docker Desktop** with Docker Compose (`docker compose up --build`).

---

## 2. Required API Keys (`.env`)

### A. OpenRouter API Key (`OPENROUTER_API_KEY`) — Required
Powers the 5-stage multi-agent pipeline, Author Style Fingerprint extraction, Research synthesis, and `1536`-dimensional Vault vector embeddings.
1. Sign in at [https://openrouter.ai/keys](https://openrouter.ai/keys).
2. Create an API key (`sk-or-v1-...`) and ensure your account has active credits.

### B. Tavily Search API Key (`TAVILY_API_KEY`) — Required
Powers live external web citations (ISO 19901-8, BS 1377, EN 1997, ASTM F1962, API 5L, regional basin geology) and external technical image discovery (`include_images=True`).
1. Sign in at [https://tavily.com](https://tavily.com).
2. Copy your `tvly-...` API key from the dashboard.

### C. Database & Storage (Zero-Cloud Local Mode or Supabase Cloud)
- **Local SQLite + Local Bucket Mode (Default):** Leave `SUPABASE_URL=` and `SUPABASE_SERVICE_ROLE_KEY=` empty. Data persists in `apps/api/geotech_studio.db` and `apps/api/storage/` (`branding-assets`, `equipment-gallery`, `project-inputs`, `compiled-exports`).
- **Supabase Cloud Mode (Optional):** Enable `pgvector` in Supabase, create the 4 storage buckets above, and set `DATABASE_URL=postgresql+asyncpg://...`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`.

---

## 3. Environment Configuration

Copy `.env.example` to `.env` in the repository root and `apps/web/.env.local`:

```bash
cp .env.example .env
cp .env.example apps/web/.env.local
```

Configure `.env` in the repository root:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_ENV=development

ENABLE_PASSCODE_GATE=false
APP_PASSCODE_HASH=
SESSION_SECRET_KEY=replace-with-random-32-char-secret
ALLOWED_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

DATABASE_URL=sqlite+aiosqlite:///./geotech_studio.db
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENROUTER_DRAFTING_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
TAVILY_API_KEY=tvly-your-tavily-key
```

---

## 4. Launching the Studio Locally

### Terminal 1 — FastAPI Backend (`http://localhost:8000`)

```bash
cd "apps/api"

# 1. Create and activate virtual environment (first time only)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies (Typst, Matplotlib, PyMuPDF, FastAPI, etc.)
pip install --upgrade pip
pip install -r requirements.txt

# 3. Start FastAPI server (auto-initializes SQLite schema & local storage buckets)
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Verify health at [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health).

### Terminal 2 — Next.js Frontend (`http://localhost:3000`)

```bash
cd "apps/web"

# 1. Install Node packages (first time only)
npm install

# 2. Start Next.js Studio
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Step-by-Step Live Owner Verification Workflow

Sample reference `.docx` engineering reports are provided in `sample_reports/` for immediate testing.

### Step 1 — Configure Workspace Branding (`/settings`)
1. Open [http://localhost:3000/settings](http://localhost:3000/settings).
2. Enter your **Default contractor / consultancy**, **Author name**, **Designation**, and **Email**.
3. Upload your **Contractor logo** and **Author signature** (`.png`/`.jpg`) and click **Save workspace defaults**.

### Step 2 — Build Institutional Memory (`/vault`)
1. Open [http://localhost:3000/vault](http://localhost:3000/vault).
2. Drag and drop one or more historical `.docx` or `.pdf` reports (e.g., from `sample_reports/`).
3. Inspect the indexed report card:
   - **Text chunks:** Section-typed boilerplate with real `1536`-dim embeddings.
   - **Extracted figures:** Embedded vessels, rigs, maps, logos, and lab photos automatically added to **Visual gallery**.
   - **PDF Layout Blueprint & Style fingerprint:** Cloned cover/header hierarchy, extracted equations, preferred units, and banned AI clichés.

### Step 3 — Run Grounded Hybrid Research (`/research`)
1. Open [http://localhost:3000/research](http://localhost:3000/research).
2. Ask a technical question (e.g., *"What are ISO 19901-8 and BS 1377 requirements for offshore PCPT and unconsolidated undrained triaxial testing in Niger Delta clays?"*).
3. Watch live SSE reasoning steps execute Vault semantic retrieval + Tavily web search, returning an unboxed answer with clickable `[1]`, `[2]` source pills and **Send to Project**.

### Step 4 — Generate & Refine a Full Publication-Grade Report (`/projects/new` → Studio)
1. Click **New Report** ([http://localhost:3000/projects/new](http://localhost:3000/projects/new)).
2. Enter a report title, scope/engineering prompt, and drop any `.xlsx`/`.csv` borehole/coordinate sheets or field `.docx`/`.pdf` notes, then click **Create & Open in Studio**.
3. Inside **Document Studio**:
   - **Stage 1 Intake Gate:** Confirm or answer any inline clarification prompts if critical project metadata was missing.
   - **Stages 2–5 Multi-Agent Execution:** Run the full pipeline and watch live SSE reasoning telemetry across Autonomous Research → Iterative Section-by-Section Drafting (`0.0`–`10.0`) + Tri-Source Visuals (Vault + Cached Web Images + 5 Matplotlib Scientific Plots) → Independent Numeric QA Cross-Check → Anti-AI Senior Humanizer.
   - **Side-by-Side Editing (`Editor + Live PDF`):** Switch to **Editor + Live PDF** in the top-right Studio bar to edit blocks/tables on the left while reviewing the live paginated Typst A4 PDF (with clickable TOC, List of Figures, and List of Tables) on the right.
   - **Highlight-to-Edit, Section Expansion & External Web Images:** Highlight any sentence to rewrite/humanize inline, click **Expand / Refine with AI** or **+ Scientific Chart** on any section, or click **Search External Web** on any figure slot to browse and cache live technical maps/equipment photos.
   - **External PDF Merge & Dual Export:** Open **Attachments** to append external lab/CPT `.pdf` logs, then click **Export PDF** and **Export Word** to download your final `.pdf` and `.docx` deliverables.

---

## 6. Automated Test & Build Commands

```bash
# Backend unit & integration test suite
cd "apps/api" && .venv/bin/pytest -v

# Frontend TypeScript & production build check
cd "apps/web" && npx tsc --noEmit && npm run build
```
