```markdown
# ARCHITECTURE.md — AI Engineering Documentation & Technical Report Studio

**Version:** 1.0.0  
**Status:** Locked-In Production Specification  
**Source of Truth Alignment:** `PRD.md` v1.0.0 & `DESIGN.md` v1.0.0 (Option A — Cupertino Studio)  

---

## 1. Architecture Overview & Core Philosophy

### 1.1 High-Level Architectural Pattern
The system follows a **Decoupled Two-Service Monorepo Architecture** comprising:
1. **Frontend Web Studio (`apps/web`):** A Next.js 14+ (App Router) application serving the Cupertino Studio UI, the Split-Screen TipTap Rich Document Editor, and the interactive PDF.js/React-PDF viewer.
2. **Backend Document & Agent Engine (`apps/api`):** A Python 3.11+ FastAPI service responsible for deterministic Excel/CSV tabular parsing (`pandas`/`openpyxl`), historical `.docx`/`.pdf` ingestion (`python-docx`/`PyMuPDF`), multi-agent orchestration (Intake, Research, Drafting, QA/Humanizer), and pixel-accurate corporate A4 `.pdf` (`WeasyPrint` + `pypdf`) and `.docx` (`python-docx`) compilation.
3. **Persistence & Storage Layer (Supabase):** Managed PostgreSQL with `pgvector` for relational state and Knowledge Vault embeddings, paired with private Supabase Storage buckets for logos, field photos, raw intake files, and compiled report exports.

### 1.2 Core Engineering Principles
- **Deterministic Numerics Over LLM Guessing:** Engineering coordinates (Easting/Northing, WGS84 Lat/Long), borehole depth intervals, and revision tables are parsed deterministically via `pandas` and injected into structured JSON AST nodes—never passed through creative LLM rewriting where numbers could be rounded or altered[cite: 1].
- **Single Document AST Source of Truth:** The TipTap/ProseMirror JSON Abstract Syntax Tree (`document_ast_json`) stored on the `Project` record is the canonical representation of the report. Both the live A4 PDF compiler (`WeasyPrint`) and the Word exporter (`python-docx`) serialize directly from this AST plus the project's front-matter metadata.
- **Verify-First State Machine:** Report generation is strictly gated by a finite state machine (`intake` -> `clarifying` -> `drafting` -> `review` -> `completed`). The Drafting Agent cannot execute until all mandatory `ClarificationItem` records are either resolved by the user or explicitly marked `omit_section = true`.
- **Zero Premature Infrastructure:** No Redis, Celery, Kafka, or microservices in MVP v1.0. FastAPI `BackgroundTasks` and Server-Sent Events (SSE) handle multi-agent streaming and document compilation cleanly for a single-user private studio.

---

## 2. Approved Tech Stack & Dependency Manifest

### 2.1 Technology Layer Breakdown

| Layer | Technology | Version Target | Architectural Rationale |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Next.js (App Router) + TypeScript | `14.2.x` / `5.x` | Fast routing, clean layout nesting for the Two-Tier Cupertino Nav, and strict compile-time type safety. |
| **Styling & Tokens** | Tailwind CSS + CSS Custom Properties | `3.4.x` | Enforces exact `DESIGN.md` Cupertino color tokens (`#F5F5F7`, `#0066CC`, `#1D1D1F`), radii (`8px`, `11px`, `18px`, `9999px`), and typography scales. |
| **UI Primitives** | Radix UI Primitives (`shadcn/ui` headless base) | Latest stable | Accessible unstyled primitives for modals, slide-over drawers, and popovers styled strictly to `DESIGN.md`. |
| **Rich Document Editor** | TipTap (`@tiptap/react`, ProseMirror) | `2.x` | Supports custom block nodes (`SmartImagePlaceholder`, `EngineeringTable`), multi-row/colspan tables, and floating selection toolbars. |
| **Live PDF Viewer** | `react-pdf` (`pdfjs-dist`) | `9.x` | Renders compiled A4 pages on the right-hand `#F5F5F7` stage with crisp text layers, zoom controls, and page navigation. |
| **Frontend State & Fetching** | TanStack Query v5 + Zustand | `5.x` / `4.x` | TanStack Query handles server cache, polling, and mutations; Zustand manages local Split-Screen Studio pane ratios, zoom level, and active drawer state. |
| **Backend Runtime & API** | Python + FastAPI + Uvicorn | `3.11+` / `0.115+` | Native access to Python's unmatched scientific/tabular (`pandas`) and document generation (`WeasyPrint`, `python-docx`, `pypdf`) ecosystem. |
| **Database & Vector Store** | Supabase PostgreSQL + `pgvector` | Postgres `15+` | Unified relational storage and `1536`-dimension cosine similarity search without managing a separate Pinecone/Qdrant cluster. |
| **Backend DB Toolkit** | SQLAlchemy 2.0 (Async) + `asyncpg` + Alembic | `2.0.x` | Type-safe async database operations, connection pooling, and version-controlled schema migrations. |
| **File & Blob Storage** | Supabase Storage (`supabase-py`) | `2.x` | Private bucket storage with signed URLs for logos, field photos, raw spreadsheets, and compiled `.pdf`/`.docx` deliverables. |
| **AI & Search Providers** | OpenRouter API (`openai` SDK) + Tavily API | Latest | Unified OpenAI-compatible client routing to `anthropic/claude-3.5-sonnet` and `google/gemini-2.5-flash`, plus citation-backed web search. |
| **Hosting & Deployment** | Docker Compose (Local Mac) / Vercel (`web`) + Railway (`api`) | Production | Runs locally via a single command on macOS or deploys to Vercel + Railway (with Nixpacks/Dockerfile for `WeasyPrint` system libraries). |

### 2.2 Approved Core Libraries vs. Banned Dependencies

| Category | Approved Package(s) | Banned / Do-Not-Install Packages |
| :--- | :--- | :--- |
| **Icons** | `lucide-react` (strict `1.5px` stroke width) | `@mui/icons-material`, `react-icons`, `fontawesome` |
| **Forms & Validation** | `react-hook-form` + `zod` (Frontend) / `Pydantic v2` (Backend) | `formik`, `yup`, `joi`, `marshmallow` |
| **HTTP & Streaming** | Native `fetch` + `@microsoft/fetch-event-source` (SSE) + `httpx` (Python) | `axios`, `superagent`, `requests` (blocking in async routes) |
| **Dates & Timestamps** | `date-fns` (Frontend) / `datetime` + `zoneinfo` (Python) | `moment`, `dayjs`, `luxon` |
| **Document Parsing** | `python-docx`, `PyMuPDF` (`fitz`), `pandas`, `openpyxl` | `pdfminer.six`, `pypdf2` (deprecated—use `pypdf` >= 4.0) |
| **PDF & Word Export** | `WeasyPrint` + `Jinja2` + `pypdf` (PDF) / `python-docx` (Word) | `jspdf`, `html2canvas` (blurry rasterized text), `reportlab` |
| **AI Orchestration** | Native Python Async State Machine + `openai` SDK + `instructor` | `langchain`, `llamaindex`, `crewai` (banned to prevent opaque prompt bloat) |

---

## 3. Frontend & Backend System Architecture

### 3.1 Frontend Architecture (`apps/web`)
- **Rendering Strategy:** Hybrid Next.js App Router. Top-level shell and initial project metadata use Server Components where practical; interactive workspaces (`/projects/[id]/studio`, `/projects/new`, `/vault`, `/research`) use Client Components backed by TanStack Query.
- **Client vs. Server Boundaries:**
  - **Server Components:** Root layout, font loading (`SF Pro` / `Inter` / `JetBrains Mono`), passcode session check middleware, and static page frames.
  - **Client Components (`"use client"`):** TipTap Editor instance, PDF.js canvas stage, multi-file drag-and-drop zones, SSE agent progress listeners, and slide-over drawers.
- **State Management Split:**
  - **Server State (TanStack Query):** Projects list, Vault documents, Gallery assets, Clarification checklists, and Research threads.
  - **Editor State (TipTap Transaction State + Debounced Auto-Save):** Local ProseMirror document state synced to `PATCH /api/v1/projects/{id}/document` after a `3000ms` debounce idle window.
  - **Studio UI State (Zustand `useStudioStore`):** Left/Right pane split percentage (`default: 50/50`), PDF preview zoom level (`default: 100%`), active slide-over drawer (`none` | `research` | `qa_log` | `outline`), and active `SmartImagePlaceholder` modal target.
- **Design Token Enforcement:** `tailwind.config.ts` and `globals.css` map exclusively to the semantic tokens defined in `DESIGN.md` (`canvas`, `canvas-parchment`, `surface-black`, `surface-tile-1`, `ink`, `primary`, `primary-focus`, `hairline`, and the single `shadow-artifact` utility `3px 5px 30px 0 rgba(0,0,0,0.22)`).

### 3.2 Backend Architecture (`apps/api`)
- **Layered Service Pattern:**
  1. **API Routers (`app/api/v1/endpoints/`):** Fast HTTP route handlers that validate incoming `Pydantic v2` schemas, verify session authentication, and delegate to Services. Zero business or SQL logic inside routers.
  2. **Domain Services (`app/services/`):** Encapsulate business rules (`VaultService`, `IntakeParserService`, `ProjectService`, `ExportCompilerService`, `ResearchService`).
  3. **Agent Pipeline (`app/agents/`):** Deterministic Python async classes implementing the 4 specialized agents (`IntakeClarifierAgent`, `ResearchAgent`, `StyleDraftingAgent`, `QaHumanizerAgent`) with structured Pydantic output schemas.
  4. **Data Access Repositories (`app/repositories/`):** Async SQLAlchemy 2.0 queries and `pgvector` similarity operations.
- **Middleware Pipeline:**
  1. `RequestIDMiddleware` (attaches UUID `X-Request-ID` to every request and log entry).
  2. `CORSMiddleware` (strictly whitelisting the Frontend origin).
  3. `PasscodeAuthMiddleware` (validates the HTTP-only session cookie or `X-Studio-Passcode` header when `ENABLE_PASSCODE_GATE=true`).
  4. `GlobalExceptionMiddleware` (catches unhandled exceptions and returns the standard JSON error envelope).

---

## 4. End-to-End Data Flow & State Lifecycle

### 4.1 Read Flow (Opening the Split-Screen Document Studio)
1. User navigates to `/projects/[id]/studio`.
2. Next.js middleware validates the session cookie (if passcode gate is enabled).
3. Client mounts the Two-Tier Cupertino Nav (`44px` Global Nav + `52px` Frosted Sub-Nav) and triggers parallel TanStack Query fetches to `GET /api/v1/projects/{id}` and `GET /api/v1/projects/{id}/qa-alerts`.
4. FastAPI `ProjectRepository` fetches the `Project` record (including `document_ast_json`, `header_logos_json`, `authorization_matrix_json`, and signed `compiled_pdf_url` from Supabase Storage).
5. Left Pane initializes the TipTap Editor with `document_ast_json` (rendering headings, 15-column monospace engineering tables, and `SmartImagePlaceholder` nodes); Right Pane renders the paginated A4 `compiled_pdf_url` on the `#F5F5F7` Parchment stage.

### 4.2 Write & Multi-Agent Generation Flow (Intake -> Clarification -> Draft -> Export)
1. **Raw Upload & Deterministic Parse:** User uploads `.xlsx`/`.csv` coordinate logs, daily notes, and field photos on `/projects/new`. Files stream to `POST /api/v1/projects/{id}/intake-files`.
2. FastAPI stores raw files in Supabase Storage (`project-inputs` bucket) and runs `IntakeParserService`:
   - Excel/CSV files are parsed via `pandas` into exact JSON table structures preserving every decimal place (`389949.9720`, `-9190.0210`, `3°54'58.741"N`)[cite: 1].
   - Text/Word notes are extracted via `python-docx` / `PyMuPDF`.
3. **Intake Verification Gate:** `IntakeClarifierAgent` (`gemini-2.5-flash`) compares parsed inputs against the selected report template schema and writes `ClarificationItem` rows to PostgreSQL. Project status transitions to `clarifying`.
4. **User Clarification Approval:** User answers questions or toggles `omit_section` in the UI and clicks **"Approve & Generate Draft"** (`POST /api/v1/projects/{id}/generate-draft`).
5. **Multi-Agent Execution Stream (SSE):**
   - **Step 1 (Vault Retrieval):** Queries `pgvector` for top-matching boilerplate chunks (`Abbreviations`, `Equipment_Specs`, `Procedures`) and loads the global `style_guide_json`[cite: 1].
   - **Step 2 (Drafting):** `StyleDraftingAgent` (`claude-3.5-sonnet`) generates narrative sections, injects deterministic `pandas` tables into their target sections, and places `SmartImagePlaceholder` nodes where equipment/field photos are required.
   - **Step 3 (QA & Anti-AI Humanizer):** `QaHumanizerAgent` cross-checks every numeric value in the prose against the `parsed_summary_json` tables (logging any `QaAlert` records if discrepancies exist) and strips banned AI clichés.
   - **Step 4 (Initial Compilation):** `ExportCompilerService` compiles the initial A4 PDF via `WeasyPrint` and stores `document_ast_json` + `compiled_pdf_url`. Project status transitions to `review`.
6. **Live Editing & Dual Export:** Whenever the user edits text, resolves a `SmartImagePlaceholder` with a gallery/uploaded photo, or attaches external lab PDFs (`Attachment 1: Borehole Logs`, `Attachment 2: PCPT Plots`), clicking `Refresh PDF` or `Export` triggers `ExportCompilerService` to re-render the HTML/CSS A4 template, merge external PDFs via `pypdf` (or build the `.docx` via `python-docx`), upload to Supabase Storage, and return a signed download URL[cite: 1].

---

## 5. Exact Project Folder & File Structure

### 5.1 Repository Directory Tree
```text
engineering-report-studio/
├── .env.example                        # Master environment variable template
├── docker-compose.yml                  # Local multi-container orchestration (web + api)
├── README.md                           # Setup, migration, and run instructions
│
├── apps/
│   ├── web/                            # Next.js 14+ Frontend (Cupertino Studio UI)
│   │   ├── package.json
│   │   ├── next.config.mjs
│   │   ├── tailwind.config.ts          # Exact DESIGN.md tokens (colors, radii, fonts, shadows)
│   │   ├── tsconfig.json
│   │   ├── public/
│   │   │   └── fonts/                  # Local fallback fonts if needed
│   │   └── src/
│   │       ├── middleware.ts           # Single-user passcode gate verification
│   │       ├── app/
│   │       │   ├── globals.css         # CSS variables & ProseMirror/TipTap table styles
│   │       │   ├── layout.tsx          # Root layout + Two-Tier Cupertino Top Nav shell
│   │       │   ├── page.tsx            # Redirects to /dashboard
│   │       │   ├── login/
│   │       │   │   └── page.tsx        # Private Passcode Gate screen
│   │       │   ├── dashboard/
│   │       │   │   └── page.tsx        # Client Projects Dashboard
│   │       │   ├── projects/
│   │       │   │   ├── new/
│   │       │   │   │   └── page.tsx    # 3-Step Setup, Raw Intake & Clarification Wizard
│   │       │   │   └── [id]/
│   │       │   │       └── studio/
│   │       │   │           └── page.tsx# 50/50 Split-Screen Editor & Live A4 PDF Preview
│   │       │   ├── vault/
│   │       │   │   └── page.tsx        # Past Reports, Style Fingerprint & Equipment Gallery
│   │       │   ├── research/
│   │       │   │   └── page.tsx        # Standalone Citation-Backed Research Workspace
│   │       │   └── settings/
│   │       │       └── page.tsx        # Universal Defaults, Logos, Signatures & Models
│   │       │
│   │       ├── components/
│   │       │   ├── layout/
│   │       │   │   ├── GlobalTopNav.tsx        # 44px #000000 bar
│   │       │   │   ├── FrostedSubNav.tsx       # 52px rgba(245,245,247,0.80) blur bar
│   │       │   │   └── FloatingStickyBar.tsx   # 64px bottom wizard approval bar
│   │       │   ├── ui/                         # Reusable Cupertino primitives
│   │       │   │   ├── Button.tsx              # Pill, Ghost Pill, Pearl Capsule, Dark Utility
│   │       │   │   ├── UtilityCard.tsx         # 18px radius, 1px #E0E0E0 hairline card
│   │       │   │   ├── OptionChip.tsx          # 9999px configurator chip
│   │       │   │   ├── SearchPillInput.tsx     # 44px pill search input
│   │       │   │   ├── Modal.tsx               # 18px radius dialog
│   │       │   │   └── SlideOverDrawer.tsx     # 440px right console drawer
│   │       │   ├── studio/                     # Split-Screen Studio components
│   │       │   │   ├── RichDocumentEditor.tsx  # TipTap editor instance & extensions
│   │       │   │   ├── AiFloatingToolbar.tsx   # #1D1D1F selection rewrite bar
│   │       │   │   ├── SmartImageNodeView.tsx  # Dashed #0066CC placeholder card
│   │       │   │   ├── EngineeringTableExt.tsx # Multi-header tabular-nums table node
│   │       │   │   ├── PaginatedPdfStage.tsx   # #F5F5F7 stage + A4 shadow + zoom controls
│   │       │   │   ├── AttachmentsModal.tsx    # External PDF upload & ordering modal
│   │       │   │   ├── SectionOutlinePopover.tsx
│   │       │   │   └── QaAlertsDrawer.tsx      # Numeric cross-check audit viewer
│   │       │   ├── intake/
│   │       │   │   ├── ClientProfileForm.tsx   # Logos, Ref codes, Revision & Sign-off matrix
│   │       │   │   ├── RawMaterialDropzone.tsx # Excel/CSV/Notes uploader
│   │       │   │   └── ClarificationList.tsx   # Verify-First Q&A resolution cards
│   │       │   ├── vault/
│   │       │   │   ├── VaultUploadCard.tsx
│   │       │   │   ├── StyleFingerprintView.tsx
│   │       │   │   └── EquipmentGalleryGrid.tsx
│   │       │   └── research/
│   │       │       ├── ResearchChatThread.tsx
│   │       │       └── CitationSourceCard.tsx
│   │       │
│   │       ├── hooks/
│   │       │   ├── useProjects.ts
│   │       │   ├── useStudioAutoSave.ts
│   │       │   ├── useAgentStream.ts           # SSE listener for multi-agent progress
│   │       │   └── useVault.ts
│   │       ├── stores/
│   │       │   └── useStudioStore.ts           # Zustand pane ratio, zoom, active modals
│   │       ├── lib/
│   │       │   ├── api-client.ts               # Typed fetch wrapper to FastAPI
│   │       │   ├── constants.ts
│   │       │   └── utils.ts
│   │       └── types/
│   │           ├── project.ts
│   │           ├── editor-ast.ts
│   │           ├── vault.ts
│   │           └── api.ts
│   │
│   └── api/                            # Python 3.11+ FastAPI Backend
│       ├── Dockerfile                  # Includes WeasyPrint system deps (pango, cairo)
│       ├── pyproject.toml              # Poetry / uv dependency lock
│       ├── alembic.ini                 # Database migration config
│       ├── alembic/
│       │   └── versions/               # SQLAlchemy schema & pgvector migrations
│       ├── app/
│       │   ├── main.py                 # FastAPI app factory, CORS, middleware
│       │   ├── core/
│       │   │   ├── config.py           # Pydantic BaseSettings startup validator
│       │   │   ├── database.py         # Async SQLAlchemy engine & session maker
│       │   │   ├── security.py         # Passcode hash & HTTP-only cookie verification
│       │   │   ├── exceptions.py       # Domain exception classes & handlers
│       │   │   └── logging.py          # Structured JSON logger with PII redaction
│       │   ├── models/                 # SQLAlchemy 2.0 ORM Models
│       │   │   ├── settings.py         # WorkspaceSettings
│       │   │   ├── vault.py            # VaultDocument, VaultChunk (Vector), GalleryAsset
│       │   │   ├── project.py          # Project, ProjectInputFile, ProjectAttachment
│       │   │   ├── clarification.py    # ClarificationItem, QaAlert
│       │   │   └── research.py         # ResearchThread
│       │   ├── schemas/                # Pydantic v2 Request/Response Schemas
│       │   │   ├── common.py           # Standard API Envelope
│       │   │   ├── project.py
│       │   │   ├── vault.py
│       │   │   ├── agent.py
│       │   │   └── research.py
│       │   ├── repositories/           # Data Access Layer (Strictly all DB queries)
│       │   │   ├── project_repo.py
│       │   │   ├── vault_repo.py       # Includes pgvector cosine distance queries
│       │   │   ├── settings_repo.py
│       │   │   └── research_repo.py
│       │   ├── services/               # Core Business & Document Processing Logic
│       │   │   ├── storage_service.py  # Supabase Storage adapter
│       │   │   ├── vault_ingestor.py   # .docx/.pdf chunking & style guide extraction
│       │   │   ├── intake_parser.py    # Deterministic pandas Excel/CSV table parser
│       │   │   ├── pdf_compiler.py     # WeasyPrint A4 renderer + pypdf attachment merger
│       │   │   └── docx_compiler.py    # python-docx corporate Word generator
│       │   ├── agents/                 # Multi-Agent System & Prompts
│       │   │   ├── llm_router.py       # OpenRouter client + fallback/retry wrapper
│       │   │   ├── prompts/            # Versioned YAML/Jinja system prompts
│       │   │   │   ├── intake_clarifier.yaml
│       │   │   │   ├── style_extractor.yaml
│       │   │   │   ├── report_drafter.yaml
│       │   │   │   ├── qa_humanizer.yaml
│       │   │   │   └── inline_editor.yaml
│       │   │   ├── intake_agent.py     # Scans raw uploads -> produces ClarificationItems
│       │   │   ├── research_agent.py   # Tavily + Vault RAG search with strict citations
│       │   │   ├── drafting_agent.py   # Combines Vault boilerplate + user data + tables
│       │   │   └── qa_humanizer_agent.py # Numeric verification + Anti-AI prose pass
│       │   ├── templates/              # Corporate Report Export Templates
│       │   │   └── reports/
│       │   │       ├── base_a4_report.html.j2  # Multi-logo running header, TOC, signature tables
│       │   │       └── report_print.css        # @page A4 rules, tabular borders, page breaks
│       │   └── api/
│       │       └── v1/
│       │           ├── router.py
│       │           └── endpoints/
│       │               ├── auth.py
│       │               ├── projects.py
│       │               ├── intake.py
│       │               ├── studio.py
│       │               ├── exports.py
│       │               ├── vault.py
│       │               ├── research.py
│       │               └── settings.py
│       └── tests/
│           ├── unit/
│           └── integration/

```

### 5.2 Naming Conventions & Placement Rules

* **Frontend React Components:** `PascalCase.tsx` inside `apps/web/src/components/<domain>/`.
* **Frontend Hooks & Stores:** `camelCase.ts` prefixed with `use` (`useStudioStore.ts`, `useAgentStream.ts`).
* **Backend Python Modules:** `snake_case.py` across all folders.
* **Strict Layer Isolation:** React components in `apps/web` must NEVER call OpenRouter, Tavily, or Supabase directly; all operations flow through `apps/web/src/lib/api-client.ts` to the FastAPI backend. Inside `apps/api`, SQL queries are strictly restricted to `app/repositories/`.

---

## 6. Database Interaction & Data Access Layer

* **Connection Pooling & Singleton Engine:** `app/core/database.py` initializes a single `create_async_engine` instance using `asyncpg` connected to the Supabase PostgreSQL pooler (Transaction mode on port `6543` with `statement_cache_size=0` compatibility, or Session mode on port `5432` with `pool_size=10, max_overflow=20`).
* **Session Lifecycle:** Injected via FastAPI dependency `get_db_session()` yielding an `AsyncSession`. Transactions commit explicitly inside the Service layer (`await session.commit()`) and automatically roll back on any raised exception.
* **Migration Workflow:** Managed exclusively via **Alembic** (`alembic revision --autogenerate -m "..."` and `alembic upgrade head`). The initial migration enables `CREATE EXTENSION IF NOT EXISTS vector;` and creates an HNSW index (`vector_cosine_ops`) on `vault_chunks.embedding`.
* **Repository Pattern Rule:** Services pass Pydantic or domain primitives into `app/repositories/*_repo.py`. Raw SQL is forbidden except for parameterized `pgvector` cosine distance operators (`VaultChunk.embedding.cosine_distance(query_vector)`).

---

## 7. Authentication, Authorization & Session Architecture

* **Private Single-User Passcode Mechanics:**
* Configured via `ENABLE_PASSCODE_GATE` (`true` | `false`) and `APP_PASSCODE_HASH` (bcrypt/SHA-256 hash of the owner's passcode).
* When `ENABLE_PASSCODE_GATE=false` (default for local MacBook development), `/login` is bypassed and all routes are immediately accessible to the local user.
* When `ENABLE_PASSCODE_GATE=true` (recommended when deployed to Vercel/Railway), submitting the passcode at `POST /api/v1/auth/unlock` issues a signed `HS256` JWT stored in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie (`studio_session`, 30-day expiry).


* **Enforcement Layers:**
1. **Next.js Edge Middleware (`src/middleware.ts`):** Intercepts navigation to `/dashboard`, `/projects/*`, `/vault`, `/research`, and `/settings`, redirecting unauthenticated browsers to `/login`.
2. **FastAPI Dependency (`verify_studio_session`):** Applied at the top-level `api_v1_router` to verify the session token on every API request.



---

## 8. API Architecture & Communication Contracts

### 8.1 Route Naming & REST + SSE Conventions

All backend routes are prefixed with `/api/v1`:

* `GET / POST /api/v1/projects` — List or create project folders.
* `GET / PATCH / DELETE /api/v1/projects/{project_id}` — Fetch or update project metadata, logos, and `document_ast_json`.
* `POST /api/v1/projects/{project_id}/intake-files` — Multipart upload for Excel/CSV, notes, and field photos; triggers deterministic parsing + `IntakeClarifierAgent`.
* `PATCH /api/v1/projects/{project_id}/clarifications` — Batch submit user answers or `omit_section` flags.
* `POST /api/v1/projects/{project_id}/generate-draft` — SSE stream (`text/event-stream`) emitting live step updates from the 4-agent pipeline.
* `POST /api/v1/projects/{project_id}/inline-edit` — Executes targeted AI rewrite on highlighted editor text/table selection.
* `POST /api/v1/projects/{project_id}/compile-preview` — Recompiles the live A4 PDF via `WeasyPrint` + merges external PDF attachments (`pypdf`).
* `POST /api/v1/projects/{project_id}/export` — Generates and returns signed download URLs for `.pdf` or `.docx`.
* `GET / POST / DELETE /api/v1/vault/documents` & `/api/v1/vault/gallery` — Manage Knowledge Vault reports, style fingerprint, and reusable equipment gallery.
* `POST /api/v1/research/query` — Standalone or project-scoped citation-backed research query.

### 8.2 Standard Response Envelope

Every non-streaming JSON endpoint returns a deterministic envelope validated by `schemas/common.py`:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_9f8c7b6a",
    "timestamp": "2026-11-16T13:54:00Z"
  },
  "error": null
}

```

On error (`success: false`), `"data"` is `null` and `"error"` contains `{"code": "CLARIFICATION_REQUIRED", "message": "Human-readable explanation", "details": [...]}`.

---

## 9. External Services & Third-Party Integrations

All external services are wrapped behind adapter classes in `app/services/` or `app/agents/` with explicit timeouts and retries:

1. **Supabase Storage Adapter (`StorageService`):**
* Organizes files into 4 logical buckets: `branding-assets` (client/contractor logos, signatures), `equipment-gallery` (reusable rig/vessel photos), `project-inputs` (raw CSV/Excel, field notes, external PDF attachments), and `compiled-exports` (generated `.pdf` and `.docx` files).
* Enforces `15s` upload/download timeouts and generates 1-hour signed URLs for the frontend PDF previewer.


2. **Tavily Search Adapter (`ResearchAgent`):**
* Wrapped with `httpx.AsyncClient(timeout=20.0)` and `tenacity` exponential backoff (`max_attempts=2`).
* Enforces `search_depth="advanced"` and strips any result lacking a valid `url` and `content` snippet.


3. **WeasyPrint & PyPDF Compiler (`PdfCompilerService`):**
* Renders `base_a4_report.html.j2` + `report_print.css` into an in-memory PDF byte buffer, then uses `pypdf.PdfWriter` to append any uploaded `ProjectAttachment` PDFs (`Attachment 1: Borehole Logs`, `Attachment 2: PCPT Plots`, `Attachment 3: Offshore Lab Summary`) in exact `display_order`.





---

## 10. AI / LLM Architecture

### 10.1 Model Routing & Role Assignment (`app/agents/llm_router.py`)

All LLM calls route through OpenRouter's unified endpoint (`https://openrouter.ai/api/v1`) with `HTTP-Referer` and zero-data-retention provider preferences enabled:

| Agent / Task | Primary Model | Fallback Model | Temperature | Output Format |
| --- | --- | --- | --- | --- |
| **Intake & Clarification Agent** | `google/gemini-2.5-flash` | `deepseek/deepseek-chat` | `0.1` | Strict JSON Schema (`ClarificationChecklist`) |
| **Vault Style Extractor** | `anthropic/claude-3.5-sonnet` | `openai/gpt-4o` | `0.2` | Strict JSON Schema (`AuthorStyleGuide`) |
| **Style-Cloner Drafting Agent** | `anthropic/claude-3.5-sonnet` | `openai/gpt-4o` | `0.3` | Structured TipTap Section AST + Image Placeholders |
| **QA & Anti-AI Humanizer Agent** | `anthropic/claude-3.5-sonnet` | `google/gemini-2.5-pro` | `0.2` | Revised Section AST + `QaAlert` list |
| **Inline Highlight-to-Edit** | `anthropic/claude-3.5-sonnet` | `google/gemini-2.5-flash` | `0.3` | Markdown/HTML fragment |
| **Vault Vector Embeddings** | `openai/text-embedding-3-small` | — | `0.0` | `float[1536]` |

### 10.2 RAG & Style-Cloner Retrieval Pipeline

1. When drafting a specific section (e.g., `4. FIELD ACTIVITIES - GEOTECHNICAL INVESTIGATION`), the Drafting Agent queries `vault_repo.search_similar_chunks(section_type="Procedures", query_embedding=..., top_k=3)`.


2. The retrieved historical chunks (e.g., standard descriptions of the *TH-30M Drill Rig*, *Seabed Frame*, and *AP Van Den Berg Wison PCPT* procedure) are injected into the system prompt alongside the global `style_guide_json`.


3. **Deterministic Table Bypass:** Coordinate tables (`Minna/Nigeria West Belt` and `WGS84`), equipment spec tables, and borehole soil profiles parsed by `pandas` from the user's uploaded spreadsheets are inserted directly into the section AST as `EngineeringTable` nodes—the LLM writes the surrounding narrative and summary tables while never re-typing raw coordinate arrays.



### 10.3 Anti-AI Humanizer & Numeric Cross-Check Guardrails

* `qa_humanizer.yaml` maintains an explicit **Banned AI Phrase List** (editable in `/vault` Tab 2: *"delve"*, *"testament"*, *"tapestry"*, *"crucial role"*, *"moreover"*, *"it is important to note"*, *"in conclusion"*) and enforces the user's authentic offshore engineering cadence (e.g., `"1 no. downhole CPTu borehole"`, `"0.0m - 120.0 mBSF"`, `"Standby on weather between 08:14Hrs to 12:00Hrs"`).


* A regex + AST numeric extractor compares all numbers, depths, and dates generated in the prose against the `ProjectInputFile.parsed_summary_json` dictionary. Any unverified number creates a `QaAlert` highlighted in amber (`#FFF9EB`) in the Studio.

---

## 11. Environment Configuration & Secrets Management

### 11.1 `.env.example` Blueprint

```ini
# ==========================================
# PUBLIC / CLIENT-SAFE VARIABLES (apps/web)
# ==========================================
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_ENV=development

# ==========================================
# SERVER-ONLY SECRETS (apps/api & Next.js server)
# ==========================================
# Security & Workspace Access
ENABLE_PASSCODE_GATE=false
APP_PASSCODE_HASH=
SESSION_SECRET_KEY=replace-with-64-char-hex-secret
ALLOWED_CORS_ORIGINS=http://localhost:3000

# Supabase Database & Storage
DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[password]@[aws-0-eu-central-1.pooler.supabase.com:6543/postgres](https://aws-0-eu-central-1.pooler.supabase.com:6543/postgres)
DIRECT_DATABASE_URL=postgresql://postgres.[project-ref]:[password]@[aws-0-eu-central-1.pooler.supabase.com:5432/postgres](https://aws-0-eu-central-1.pooler.supabase.com:5432/postgres)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# AI & Search Providers
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_DRAFTING_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
TAVILY_API_KEY=tvly-...

```

### 11.2 Startup Validation Rule

`apps/api/app/core/config.py` uses `pydantic-settings` (`BaseSettings`) instantiated at module import time. If any required key (`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENROUTER_API_KEY`) is missing or malformed, FastAPI refuses to boot and prints a clear diagnostic listing the missing variable.

---

## 12. Error Handling, Logging & Observability

* **Domain Exception Hierarchy (`app/core/exceptions.py`):**
* `AppError` (Base class with `code`, `status_code`, `message`, `details`).
* `FileParseError (422)` — Raised when an uploaded `.xlsx`, `.csv`, `.docx`, or `.pdf` is corrupted or password-protected.
* `ClarificationGateError (409)` — Raised if draft generation is requested while unresolved `ClarificationItem` rows exist.
* `ExternalProviderError (502)` — Raised when OpenRouter, Tavily, or Supabase Storage fails after retries.
* `CompilationError (500)` — Raised if `WeasyPrint` or `python-docx` fails during document rendering.


* **Structured Logging & Redaction:**
* Uses Python `structlog` outputting JSON in production and colored console logs in development.
* Every log line includes `request_id`, `project_id`, `agent_name`, `duration_ms`, and `model_used`.
* **Strict Redaction:** Never log raw API keys, session cookies, or full proprietary report bodies at `INFO` level.


* **Frontend Error Boundaries:** Next.js `error.tsx` boundaries wrap the Studio canvas so a rendering error inside a custom TipTap node or PDF viewer displays a clean Cupertino recovery card (`Retry Render` / `Restore Last Auto-Save`) without crashing the navigation shell.

---

## 13. Security Boundaries & Hardening Rules

1. **Strict Upload Validation:**
* Validate both file extension and magic-byte MIME signature (`python-magic` / header inspection) before parsing.
* Allowed intake/vault types: `.docx`, `.pdf`, `.xlsx`, `.csv`, `.txt`, `.png`, `.jpg`, `.webp`.
* Maximum file size: `50MB` per report/attachment PDF; `15MB` per image or spreadsheet.


2. **HTML & Template Sanitization:**
* Before passing TipTap HTML/AST content into `WeasyPrint` Jinja2 templates, sanitize with `nh3` / `bleach` (allowing only structural report tags: `h1-h4`, `p`, `table`, `thead`, `tbody`, `tr`, `th`, `td`, `ul`, `ol`, `li`, `strong`, `em`, `img`, `figure`, `figcaption`, `span`, `div`) and restrict image `src` attributes strictly to whitelisted Supabase Storage signed URLs or local template assets (preventing Server-Side Request Forgery / SSRF in `WeasyPrint`).


3. **CORS & Headers:**
* FastAPI `CORSMiddleware` restricts origins strictly to `ALLOWED_CORS_ORIGINS`.
* Next.js sets `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, and `Referrer-Policy: strict-origin-when-cross-origin`.



---

## 14. Testing, Deployment & Scalability Roadmap

### 14.1 Pragmatic Testing Strategy

* **Unit Tests (`pytest` in `apps/api/tests/unit/`):**
* Test `IntakeParserService` against multi-header offshore coordinate Excel sheets (`Minna/Nigeria West Belt` + `WGS84`) to verify zero rounding or column shifting.


* Test the `QaHumanizerAgent` numeric cross-checker and banned-phrase stripper.
* Test `PdfCompilerService` and `DocxCompilerService` output generation from a fixture `document_ast_json`.


* **Integration Tests (`pytest-asyncio` + `httpx.AsyncClient`):**
* Test the full state machine transition: `Create Project` -> `Upload Intake Files` -> `Resolve Clarifications` -> `Generate Draft` -> `Compile & Merge External PDFs`.


* **E2E Smoke Test (Playwright in `apps/web`):**
* Verifies opening `/projects/[id]/studio`, editing a coordinate cell and paragraph in TipTap, resolving a `SmartImagePlaceholder`, and triggering a `.pdf` and `.docx` export.



### 14.2 Deployment Pipeline

1. **Local MacBook Development:** Run `docker-compose up --build` (or `pnpm dev` in `apps/web` + `uvicorn app.main:app --reload` in `apps/api`) connected to a cloud Supabase project.
2. **Production Cloud Deployment:**
* **Database & Storage:** Supabase Cloud (`PostgreSQL 15` + `pgvector` + private Storage buckets).
* **Backend (`apps/api`):** Deployed to **Railway** via `apps/api/Dockerfile` (which pre-installs `libpango-1.0-0`, `libcairo2`, and `libgdk-pixbuf2.0-0` required by `WeasyPrint`). Executes `alembic upgrade head` automatically in the pre-deploy hook.
* **Frontend (`apps/web`):** Deployed to **Vercel** with `NEXT_PUBLIC_API_BASE_URL` pointing to the Railway FastAPI domain.



### 14.3 MVP v1.0 vs. Future Scale Boundaries

* **Built Now in MVP v1.0:** Single-user private workspace, synchronous/SSE agent pipeline, direct FastAPI `WeasyPrint` + `python-docx` compilation, Supabase `pgvector` Knowledge Vault, and multi-attachment PDF merging.
* **Deferred Until Needed (Post-MVP):** Multi-tenant team organizations, background Celery/Redis worker clusters (only needed if 20+ concurrent users compile 100-page PDFs simultaneously), and real-time multi-cursor WebSocket collaboration.

```

`ARCHITECTURE.md` is locked in and ready to save alongside `PRD.md` and `DESIGN.md`. Whenever you are ready, drop in your **Implementation Plan / Coding Agent Execution Prompt**!

```