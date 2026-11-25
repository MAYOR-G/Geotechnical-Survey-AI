# PRD.md — AI Engineering Documentation & Technical Report Studio

**Version:** 1.0.0  
**Status:** Draft for Final Sign-Off  
**Target Release:** MVP v1.0  

---

## 1. Project Overview & Executive Summary

### 1.1 Problem Statement
Offshore and oil & gas geotechnical/survey engineers spend hours manually compiling repetitive, high-stakes field reports (such as Geotechnical Survey Field Reports, Geohazard Surveys, and Engineering Proposals). Each report requires:
1. Merging strict corporate front-matter (multi-party client/contractor logos, revision control matrices, authorization/signature tables, and auto-generated Tables of Contents, Figures, and Tables).
2. Reusing 80–90% standardized technical boilerplate (abbreviations, drilling procedures, PCPT methods, offshore lab specs, vessel/rig specifications) while customizing project-specific details.
3. Transforming raw field data (15-column target vs. actual coordinate sheets, chronological sequence of events logs, borehole soil depth profiles) into accurately formatted engineering tables.
4. Capturing and captioning vessel, rig, and lab photos alongside appending external lab attachments (borehole logs, PCPT plots, triaxial test sheets).

Standard AI tools fail at this workflow because they hallucinate critical coordinates or depths, overwrite standard engineering phrasing with generic "AI slop," cannot maintain complex multi-column engineering table structures, and lack a side-by-side rich editing and PDF pagination preview environment.

### 1.2 Value Proposition
A private, single-user AI documentation studio tailored specifically for technical and offshore engineering writers. It combines:
- **A Persistent Knowledge & Style Vault:** Learns the engineer's exact writing voice, terminology, and reusable technical boilerplate from past completed reports.
- **A "Verify-First" Multi-Agent Pipeline:** Scans raw uploaded spreadsheets, daily logs, and prompts, then halts to ask targeted clarifying questions before drafting—preventing fabricated data.
- **Anti-AI Humanization & Cross-Check QA:** Ensures every coordinate, depth, and timestamp matches raw inputs while polishing prose to read like an experienced human field engineer.
- **Split-Screen Canvas & Multi-Format Export:** Pairs a Notion/Google Docs-style block editor (supporting manual edits and highlight-to-prompt AI rewrites) with a live paginated PDF preview, Smart Image Placeholders, external PDF attachment merging, and exports to both `.pdf` and `.docx`.

### 1.3 Target Users & Personas
- **Primary Persona — Lead Geotechnical / Offshore Documentation Engineer:**
  - **Role:** Prepares field reports, survey summaries, and technical proposals for oil & gas operators (e.g., First E&P, Chevron, Shell) on behalf of survey contractors (e.g., GEMS, Enviros).
  - **Core Goals:** Cut report assembly time by 70%+, maintain strict technical accuracy across coordinates and depth logs, preserve personal/company writing style, and deliver client-ready PDF and Word documents without formatting headaches.

### 1.4 Approved Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 14+ (App Router, TypeScript, Tailwind CSS, shadcn/ui) | Core web interface, project workspace, split-screen studio |
| **Rich Document Editor** | TipTap (ProseMirror-based) | Notion/Google Docs-style block editing, complex tables, inline highlight-to-prompt AI toolbar |
| **Live PDF Preview & Export** | WeasyPrint (via Backend) + PDF.js / React-PDF (Frontend Viewer) | Deterministic A4 pagination, multi-logo running headers/footers, TOC generation, PDF merging |
| **Word (.docx) Export** | `python-docx` (Backend) | Editable MS Word generation preserving corporate tables, headers, and styles |
| **Backend & Orchestration** | Python FastAPI | Multi-agent state machine, Excel/CSV parsing (`pandas`/`openpyxl`), document ingestion (`PyMuPDF`/`python-docx`), PDF merging (`pypdf`) |
| **Database & Vector Store** | Supabase (PostgreSQL + `pgvector`) | Relational metadata, project state, document JSON AST, and semantic embeddings for the Knowledge Vault |
| **File Storage** | Supabase Storage | Logos, reusable equipment gallery, field photos, raw CSV/Excel uploads, external PDF attachments |
| **AI Model Routing** | OpenRouter API | **Claude 3.5 Sonnet** (Style-Cloner Drafting & Anti-AI Humanizer); **Gemini 2.5 Flash / DeepSeek V3** (Intake Scanning, Tabular Extraction, QA Verification) |
| **External Web Search** | Tavily Search API | Citation-backed regional/technical research (OML blocks, maritime standards, vessel specs) |
| **Authentication** | Single-User Passcode / Supabase Single-Admin Auth | Lightweight private workspace protection (toggleable via environment config) |

---

## 2. Core User Journeys & User Stories

### Journey 1: Seeding the Knowledge & Style Vault
1. User navigates to `/vault` and uploads 5–10+ historical `.docx` or `.pdf` reports and reusable equipment photos (e.g., *Dolphin Geo Survey* vessel, *TH-30M* drill rig).
2. Backend parses the documents into structural sections, extracts writing style rules (sentence length, passive/active voice, technical terminology, formatting conventions), indexes boilerplate chunks in `pgvector`, and saves equipment specs/photos.
3. User reviews the extracted "Style Profile & Boilerplate Library" and marks it active.

### Journey 2: Creating a New Client Project & Running Intake Verification
1. User clicks **"New Project"** on `/dashboard` and selects or creates a **Client/Project Profile** (e.g., Client: *First E&P*, Contractor: *GEMS / Enviros*, Doc Ref: `GEMS-FEPDCL-ANY-ECEN-FLD-GI24-01`, Author/Reviewer/Approver names, and logos).
2. User uploads raw project materials into the Project Intake drawer: Excel/CSV files (coordinates, borehole depth logs), rough daily activity notes, field photos, and an initial instruction prompt.
3. The **Intake & Clarification Agent** analyzes the uploads against the selected report structure and displays a **Clarification Checklist** (e.g., *"Anyala Central CSP coordinates are present, but no test logs were found—was this location skipped?"*, *"Please confirm the replacement Drilling Supervisor's name on 05/07/2024"*).
4. User answers the questions or marks items as "Not Applicable / Omit" and clicks **"Approve & Generate Draft"**.

### Journey 3: Multi-Agent Drafting, Split-Screen Review & Export
1. The **Research Agent** (if toggled), **Style-Cloner Drafting Agent**, and **QA & Anti-AI Humanizer Agent** execute sequentially, streaming section progress to the UI.
2. User lands on the **Split-Screen Studio** (`/projects/[id]/studio`):
   - **Left Pane:** Rich editor with formatted headings, 15-column coordinate tables, sequence logs, and **Smart Image Placeholders** where photos are needed.
   - **Right Pane:** Live paginated A4 PDF preview showing exact cover page logos, revision tables, and page breaks.
3. User clicks a Smart Image Placeholder to select a rig photo from the gallery or upload a new field photo with a caption.
4. User highlights a paragraph in the editor, clicks **"Ask AI"**, and types *"Make this note about weather standby more concise"*. The inline agent updates the text in place.
5. User opens the **Attachments & Appendices** tab, uploads 3 external PDFs (*Attachment 1: Borehole Logs*, *Attachment 2: PCPT Plots*, *Attachment 3: Lab Summary*), and orders them.
6. User clicks **"Export Package"** and downloads either the merged master `.pdf` or the editable `.docx`.

### User Stories & Acceptance Criteria

| ID | User Story | Acceptance Criteria |
| :--- | :--- | :--- |
| **US-01** | As an engineer, I want to upload past reports into a Knowledge Vault so that the AI writes in my exact technical voice and reuses my standard equipment/procedure sections. | - Accepts `.docx` and `.pdf` files up to 50MB each.<br>- Extracts and displays a readable "Style Fingerprint" (tone, terminology, boilerplate sections).<br>- Stores embeddings in `pgvector` tagged by section type (e.g., `intro`, `equipment_specs`, `sampling_procedures`). |
| **US-02** | As an engineer, I want the AI to ask me clarifying questions when my raw notes or Excel files are incomplete so that it never hallucinates coordinates, dates, or depths. | - Pipeline halts after Intake Analysis if ambiguity or missing required fields are detected.<br>- Presents structured questions with text inputs or "Omit/Skip" toggles.<br>- Zero unverified numbers or named entities appear in the generated draft. |
| **US-03** | As an engineer, I want raw CSV/Excel coordinate and sequence logs converted into formatted report tables automatically so that I don't have to copy-paste cell by cell. | - Parses multi-header tables (e.g., Minna/Nigeria West Belt Easting/Northing + WGS84 Lat/Long + Water Depths).<br>- Preserves exact decimal precision from source spreadsheets without rounding.<br>- Renders editable tables in the rich editor and clean bordered tables in PDF/Word exports. |
| **US-04** | As an engineer, I want a multi-agent QA and Humanizer pass on every draft so that the report reads like a field professional wrote it and contains no AI clichés. | - QA Agent flags any discrepancy between source Excel/notes and drafted text.<br>- Humanizer Agent strips banned AI phrases (e.g., *"delve into"*, *"testament to"*, *"crucial role"*) and enforces crisp, passive/objective engineering prose. |
| **US-05** | As an engineer, I want to highlight any text or table section in the editor and prompt the AI to revise it while seeing a live PDF preview alongside my edits. | - Highlighting text reveals a floating AI action bar (*Rewrite, Expand, Condense, Match Style, Custom Prompt*).<br>- Diff view allows accepting or rejecting the inline change.<br>- Right-pane PDF preview updates upon save or manual refresh. |
| **US-06** | As an engineer, I want the system to insert Smart Image Placeholders when a photo or map is needed and let me attach external lab PDFs to the end of the report. | - AI inserts contextual placeholders (e.g., `[IMAGE NEEDED: Survey Vessel on Site]`).<br>- Clicking a placeholder opens the Equipment Gallery / File Uploader.<br>- Uploaded external PDFs are appended sequentially after the main report body during final PDF export. |
| **US-07** | As an engineer, I want to use a standalone Research Agent with web citations or invoke it inside my project so that I can verify regional OML block data or maritime standards. | - Standalone `/research` chat and collapsible studio sidebar.<br>- Every factual claim includes a clickable source URL and snippet via Tavily.<br>- One-click "Insert into Project Notes" button. |

---

## 3. Features & Functional Requirements

### Module A: Knowledge & Style Vault (`/vault`)
- **FR-A1 (`P0`):** Support bulk upload of historical reports (`.docx`, `.pdf`).
- **FR-A2 (`P0`):** Automatically chunk documents by heading hierarchy and classify chunks into: `Front_Matter`, `Abbreviations`, `Executive_Summary`, `Introduction`, `Scope_of_Work`, `Equipment_Specs`, `Procedures`, `Sequence_of_Events`, `Field_Results`, and `Appendices`.
- **FR-A3 (`P0`):** Generate a global **Author Style Guide JSON** capturing preferred nomenclature (e.g., `"mBSF"`, `"PCPT"`, `"COMPANY"`, `"Contractor"`), date/time formatting (`DD/MM/YYYY`, `24-hour Hrs`), and sentence structure rules.
- **FR-A4 (`P0`):** Maintain a **Reusable Asset & Equipment Gallery** storing standard photos (vessels, drill rigs, winches, lab gear) with default captions and tags for automatic or one-click insertion.

### Module B: Client Profiles & Project Workspace (`/projects`)
- **FR-B1 (`P0`):** Create/edit **Universal Defaults** (User's primary contractor company logo, author name, email, designation, signature image).
- **FR-B2 (`P0`):** Create/edit **Project Folders** with per-project metadata:
  - Client Name & Logo, Partner Logos (up to 3 header logos).
  - Document Title, Subtitle, Client Ref Code, Contractor Ref Code, Revision History rows (`Rev`, `Date`, `Reason`, `Prepared`, `Checked`, `Approved`).
  - Distribution List & Sign-off Matrix (`Prepared By`, `Reviewed By`, `Approved By` with names, designations, emails, and optional signature images).
- **FR-B3 (`P1`):** Support **Document Type Templates**:
  1. *Geotechnical / Offshore Survey Field Report* (default master template).
  2. *Technical / Engineering Proposal*.
  3. *Custom / Blank Structured Report* (user-defined or AI-proposed section outline).

### Module C: Multi-Agent Engine & "Verify-First" Pipeline
- **FR-C1 (`P0` - Intake & Clarification Agent):**
  - Ingests raw project uploads (`.xlsx`, `.csv`, `.txt`, `.docx`, `.pdf`, `.png`/`.jpg`) plus user prompt.
  - Compares available data against required sections of the chosen template.
  - Outputs a structured JSON list of **Clarification Questions** for missing, conflicting, or ambiguous items before any drafting begins.
- **FR-C2 (`P0` - Research Agent):**
  - Queries internal `pgvector` Vault first, then external Tavily API (when web search is enabled).
  - Returns verified facts with inline citations and source URLs. Never fabricates citations.
- **FR-C3 (`P0` - Style-Cloner Drafting Agent):**
  - Drafts report sections using retrieved Vault boilerplate + verified user inputs + Author Style Guide JSON.
  - Converts uploaded CSV/Excel sheets into structured Markdown/TipTap tables without altering numeric values.
  - Inserts **Smart Image Placeholders** (`data-type="image-placeholder"`) with descriptive prompts wherever visual evidence (maps, equipment, field activity photos) is contextually required.
- **FR-C4 (`P0` - QA & Anti-AI Humanizer Agent):**
  - **Numeric & Entity Verification:** Cross-checks every coordinate, depth value, vessel name, and date in the draft against the raw intake data. Flags mismatches.
  - **Humanization Pass:** Rewrites robotic transitions, removes LLM-typical filler words, and enforces authentic offshore/engineering report register.

### Module D: Split-Screen Editor, Smart Visuals & Exporter (`/projects/[id]/studio`)
- **FR-D1 (`P0` - Rich Block Editor):**
  - Built on TipTap supporting H1–H4 headings, nested numbered lists (`3.1`, `3.1.1`), complex tables (merged cells, column colspans, row additions/deletions), figure captions, and page-break markers.
- **FR-D2 (`P0` - Inline Highlight-to-Prompt AI):**
  - Selecting any text range or table opens a floating AI menu allowing custom revision instructions or preset actions (*Humanize*, *Make Technical*, *Fix Grammar*, *Summarize*).
  - Shows inline preview before applying changes.
- **FR-D3 (`P0` - Smart Image Placeholder Resolution):**
  - Clicking a placeholder in the editor opens a modal with two tabs: **Select from Equipment/Vault Gallery** or **Upload New Field Photo**.
  - Automatically numbers figures (`Figure 1`, `Figure 2`) and updates the **List of Figures** in the front matter.
- **FR-D4 (`P0` - Live Paginated PDF Preview & Attachment Merger):**
  - Right pane renders the compiled A4 PDF with exact corporate cover layout, running multi-logo headers, page numbers, auto-calculated Table of Contents, List of Figures, and List of Tables.
  - **External Attachment Manager:** Allows uploading external PDFs (e.g., Borehole Logs, PCPT Plots, Lab Sheets) and merges them cleanly at the end of the generated PDF or into designated Appendix slots.
- **FR-D5 (`P0` - Dual Export):**
  - One-click export to **Master PDF (`.pdf`)** (including merged external PDF attachments).
  - One-click export to **Editable Word (`.docx`)** (preserving corporate tables, headers, logos, and heading styles).

---

## 4. Pages, Screens & Navigation Flow

### Navigation Architecture
A persistent left sidebar (collapsible on Studio view) with 4 primary destinations:
1. **Projects (`/dashboard`)**
2. **Knowledge & Style Vault (`/vault`)**
3. **Research Assistant (`/research`)**
4. **Defaults & Branding (`/settings`)**

### Screen Inventory

| Route | Screen Name | Core Components & Actions |
| :--- | :--- | :--- |
| `/` | Root Redirect | Redirects directly to `/dashboard` (or `/login` if single-user passcode is enabled). |
| `/login` | Private Access Gate | Simple single-input passcode screen for private workspace protection. |
| `/dashboard` | Projects Dashboard | Grid/list of Client Project Folders, search/filter bar, status badges (`Intake`, `Clarification Needed`, `Draft Ready`, `Exported`), **"New Project"** CTA button. |
| `/projects/new` | New Project & Intake Wizard | **Step 1:** Project Metadata, Logos & Sign-off Matrix.<br>**Step 2:** Raw File Uploader (Excel/CSV, notes, photos) + Initial Prompt.<br>**Step 3:** AI Clarification Q&A Checklist before generation. |
| `/projects/[id]/studio` | Split-Screen Document Studio | **Top Bar:** Project title, Agent Status indicator, Section Outline drawer toggle, Attachments modal button, Export (`.pdf` / `.docx`) dropdown.<br>**Left Pane (50%):** TipTap Rich Editor + Floating AI Toolbar + Smart Image Placeholder cards.<br>**Right Pane (50%):** Paginated PDF Preview with zoom, page jump, and "Refresh Preview" button.<br>**Slide-Over Drawer:** Embedded Research Agent & QA Verification Log. |
| `/vault` | Knowledge & Style Vault | **Tab 1: Past Reports:** Upload dropzone, indexed report list, chunk viewer.<br>**Tab 2: Style Profile:** Extracted writing rules & editable banned-words list.<br>**Tab 3: Equipment & Visual Gallery:** Reusable photos with default captions/tags. |
| `/research` | Standalone Research Workspace | Chat interface with toggleable sources (*Internal Vault Only*, *Live Web via Tavily*, *Both*), citation cards, and "Copy / Save to Project" actions. |
| `/settings` | Universal Defaults & API Config | Default Contractor Logo, Author Profile (Name, Email, Designation, Signature upload), OpenRouter model selection overrides. |

---

## 5. Roles, Authentication & Permissions

For MVP v1.0, this is a **Private Single-User Workspace** tailored for a single documentation engineer.

| Role | Authentication Mechanism | Access Control Matrix |
| :--- | :--- | :--- |
| **Owner / Primary Engineer** | Default open local/private access, with an optional environment-configured Passcode Gate (`APP_PASSCODE`) stored via HTTP-only session cookie. | **Full CRUD Access:** Can view, create, update, and delete all Projects, Knowledge Vault documents, Style Profiles, Equipment Photos, Research Threads, and Exports. |
| **Unauthenticated Visitor** (when Passcode Gate is enabled) | None | Redirected to `/login`. Zero access to routes or API endpoints. |

---

## 6. Data Requirements & Core Entities

### 6.1 `WorkspaceSettings` (Singleton)
- **Attributes:** `id`, `default_contractor_name`, `default_contractor_logo_url`, `author_name`, `author_email`, `author_designation`, `author_signature_url`, `style_guide_json` (extracted rules, preferred terms, banned AI words), `updated_at`.

### 6.2 `VaultDocument` & `VaultChunk`
- **`VaultDocument` Attributes:** `id`, `filename`, `file_url`, `file_type` (`docx` | `pdf`), `document_category` (`field_report` | `proposal` | `reference`), `ingestion_status`, `created_at`.
- **`VaultChunk` Attributes:** `id`, `vault_document_id` (FK), `section_type` (enum matching report anatomy), `heading_title`, `content_text`, `tables_json`, `embedding` (`vector(1536)`).

### 6.3 `GalleryAsset`
- **Attributes:** `id`, `title`, `default_caption`, `category` (`vessel` | `drill_rig` | `lab_equipment` | `map` | `field_photo`), `file_url`, `tags` (array), `created_at`.

### 6.4 `Project`
- **Attributes:** `id`, `title`, `document_type`, `status` (`intake` | `clarifying` | `drafting` | `review` | `completed`), `client_name`, `contractor_name`, `client_ref_code`, `contractor_ref_code`, `revision_number`, `header_logos_json` (array of up to 3 logo URLs), `revision_history_json`, `authorization_matrix_json` (Prepared, Checked, Approved rows + signatures), `document_ast_json` (TipTap/ProseMirror JSON state), `compiled_pdf_url`, `compiled_docx_url`, `created_at`, `updated_at`.

### 6.5 `ProjectInputFile` & `ProjectAttachment`
- **`ProjectInputFile` (Raw Intake Materials):** `id`, `project_id` (FK), `filename`, `file_url`, `file_type` (`xlsx` | `csv` | `docx` | `pdf` | `txt` | `image`), `parsed_summary_json` (extracted tables/text).
- **`ProjectAttachment` (External PDFs to Merge):** `id`, `project_id` (FK), `attachment_number` (e.g., `Attachment 1`), `title` (e.g., `Borehole Logs`), `file_url`, `display_order`.

### 6.6 `ClarificationItem`
- **Attributes:** `id`, `project_id` (FK), `category` (`missing_data` | `conflict` | `image_needed` | `scope_confirmation`), `question_text`, `context_reference` (which file/section triggered it), `user_response`, `is_resolved` (boolean), `omit_section` (boolean).

### 6.7 `ResearchThread` & `ResearchMessage`
- **Attributes:** `id`, `project_id` (nullable FK for standalone vs. project-bound), `title`, `messages_json` (role, content, citations array with `title`, `url`, `snippet`), `created_at`.

---

## 7. External Integrations & APIs

| Service / API | Integration Purpose | Data In (Request) | Data Out (Response) |
| :--- | :--- | :--- | :--- |
| **OpenRouter API (`anthropic/claude-3.5-sonnet`)** | Primary Style-Cloner Drafting Agent, Inline Editor Rewrites, and Anti-AI Humanizer Agent | System prompt + Author Style Guide JSON + Retrieved Vault Boilerplate + Verified Project Data | Structured TipTap-compatible Markdown/JSON sections with human engineering tone |
| **OpenRouter API (`google/gemini-2.5-flash` or `deepseek/deepseek-chat`)** | High-speed Intake Scanning, Clarification Question Generation, CSV-to-Table Mapping, and Numeric QA Cross-Checking | Parsed raw text/tables from uploaded files + Template Schema | JSON list of missing variables/questions; QA discrepancy report |
| **OpenAI / OpenRouter Embeddings (`text-embedding-3-small`)** | Vectorizing Knowledge Vault chunks and queries | Text chunks (500–1,000 tokens) from historical reports | 1536-dimensional float vector stored in Supabase `pgvector` |
| **Tavily Search API** | External Web Research Agent for regional data, OML blocks, vessel specs, and maritime standards | Search query string + `search_depth="advanced"` + `include_raw_content=True` | Ranked web results with verified URLs, titles, and factual snippets |
| **Supabase (Database & Storage)** | Persistence for projects, vectors, images, raw files, and exported documents | SQL queries, vector similarity RPC calls, multipart file uploads | Relational records, top-K matching boilerplate chunks, signed/public asset URLs |

---

## 8. UI/UX States (Loading, Empty & Error States)

### 8.1 Loading States
- **Vault Ingestion:** Progress bar per uploaded report showing `Extracting Text & Tables -> Analyzing Style -> Generating Embeddings -> Complete`.
- **Intake Analysis:** Skeleton cards in the Clarification step with animated status text: *"Scanning Excel coordinate sheets and checking against Field Report schema..."*
- **Multi-Agent Drafting Pipeline:** A 4-step live stepper modal/banner:
  1. `Retrieving Boilerplate & Research`
  2. `Drafting Technical Sections & Tables`
  3. `Running Numeric QA Cross-Check`
  4. `Applying Anti-AI Humanizer Polish`
- **PDF Preview Compilation:** Subtle shimmer overlay on the right-hand preview pane while WeasyPrint compiles updated HTML/CSS + merges PDF attachments in the background.

### 8.2 Empty States
- **Empty Knowledge Vault (`/vault`):** Clear onboarding card: *"Your Style Vault is empty. Upload 3–10 past field reports or proposals so the AI can learn your exact writing style, table structures, and standard equipment boilerplate."* + **"Upload Past Reports"** primary button.
- **Empty Projects Dashboard (`/dashboard`):** *"No documentation projects yet. Start a new client report folder by uploading raw field notes, coordinate sheets, or prompts."* + **"Create First Project"** CTA.
- **Empty Attachments List:** *"No external attachments added. Upload Borehole Logs, PCPT Plots, or Lab Summary PDFs here to automatically merge them into the final report package."*

### 8.3 Error & Fallback States
- **Unparseable Excel/CSV or Corrupted File:** Non-blocking toast and inline badge next to the file: *"Could not parse 'coords_raw.xlsx'. Please ensure the file is not password-protected or upload a standard CSV/XLSX."*
- **QA Numeric Mismatch Warning:** If the QA Agent detects that a number in the generated text differs from the source Excel sheet, it highlights the cell/sentence in amber in the Studio with a tooltip: *"QA Alert: Source sheet shows 49.4m, draft shows 49.0m. Click to fix."*
- **LLM / OpenRouter Timeout or Rate Limit:** Automatic retry with exponential backoff (up to 2 retries) and fallback model routing; if still failing, preserves all current editor state in local storage + Supabase and shows a `"Retry Step"` button.

---

## 9. Non-Functional Requirements

- **Performance & Responsiveness:**
  - Inline AI highlight-to-edit responses must begin streaming or return within **< 4 seconds**.
  - Full 30-page PDF preview recompilation (including table layout and PDF attachment merging) must complete in **< 5 seconds**.
  - **Desktop-First Optimization:** Optimized for `1280px+` widescreen monitors (split-screen editor + preview). On tablet/smaller screens (`< 1024px`), the Studio automatically switches to a tabbed view (`Editor` tab | `PDF Preview` tab).
- **Zero-Hallucination & Data Integrity:**
  - Coordinate tables and depth logs must bypass creative LLM rewriting—parsed deterministically via `pandas` and injected directly into the document AST or verified cell-by-cell.
  - Auto-save in the Split-Screen Editor every **3 seconds** after typing stops (debounced) to prevent any lost work.
- **Document Formatting Fidelity:**
  - Exported PDFs must strictly enforce A4 dimensions (`210mm x 297mm`), corporate multi-logo header tables on running pages, proper page break handling (preventing orphaned headings), and accurate Table of Contents page numbering.
- **Security & Privacy:**
  - All uploaded client reports, coordinates, and proprietary oil & gas survey files are stored in private Supabase buckets and never used to train public models (enforced via OpenRouter zero-data-retention provider routing where supported).

---

## 10. MVP Scope, Out-of-Scope & Success Criteria

### 10.1 Strictly In-Scope (MVP v1.0)
- Knowledge & Style Vault with `.docx`/`.pdf` ingestion, style extraction, and reusable Equipment/Photo Gallery.
- Client/Project Folder setup with multi-logo headers, revision tables, and signature/authorization matrices.
- Multi-format raw intake (`.xlsx`, `.csv`, `.docx`, `.pdf`, `.txt`, images, prompts) + **Mandatory Clarification Q&A step** before drafting.
- 4-Agent Pipeline (Intake Clarifier, Tavily + Vault Research Agent, Style-Cloner Writer, QA & Anti-AI Humanizer).
- Standalone `/research` chat utility + embedded Studio research drawer.
- Split-Screen Studio: TipTap Rich Editor (with inline highlight-to-prompt AI and Smart Image Placeholders) + Live A4 Paginated PDF Preview.
- External PDF Attachment uploader & merger (for Borehole logs, PCPT plots, Lab results).
- Export to both **PDF (`.pdf`)** and **MS Word (`.docx`)**.

### 10.2 Strictly Out-of-Scope (Non-Goals for v1.0)
- Multi-tenant SaaS billing, Stripe subscriptions, or complex RBAC team permissions.
- Real-time multi-user simultaneous cursor collaboration (e.g., Yjs/WebSockets for multiple editors at once).
- Native geotechnical plotting software (the app merges existing PCPT/Borehole log PDFs/images rather than rendering raw sensor cone-resistance curves from `.ags` or `.las` binary hardware files).
- Native mobile phone app (iOS/Android).

### 10.3 Definition of Done & Success Metrics
1. **End-to-End Replication Test:** Given raw coordinate tables, rough daily sequence notes, and field photos for a campaign like the *Anyala East & Central Geotechnical Survey*, the user can generate, review, populate images, attach lab PDFs, and export a complete, client-ready PDF and `.docx` report that matches the structure, tables, and professional human tone of the reference document.
2. **Zero Unverified Data:** The Intake Agent successfully pauses and asks clarifying questions whenever required template fields (e.g., water depth, vessel name, or test coordinates) are missing from the raw upload.
3. **Export Cleanliness:** Exported `.pdf` and `.docx` files open cleanly in Adobe Acrobat and Microsoft Word with all multi-logo headers, 15-column coordinate tables, figure captions, and appended external PDFs intact.

---

## 11. Assumptions & Open Decisions Requiring Approval

### Key Assumptions Made
1. **Master Template Baseline:** We are using the uploaded *Geotechnical Survey Field Report (FIRST E&P / GEMS / Enviros)* as the primary baseline template for v1.0, while keeping the section outline flexible so additional document types (like Proposals or other reports you drop in later) can be added as templates without changing the core engine.
2. **Deterministic Table Parsing:** Large numerical tables (like the 15-column *Test Position Coordinates*) will be parsed directly from Excel/CSV via Python (`pandas`) so that not a single digit is altered or rounded by an LLM.
3. **PDF & Word Rendering Pipeline:** Both PDF (via WeasyPrint + `pypdf` for merging external attachments) and Word (`.docx` via `python-docx`) will be generated by the Python FastAPI backend to ensure 100% consistent corporate headers, borders, and pagination.

### Open Decisions for Your Sign-Off
1. **Deployment Target:** Do you want to run this locally on your MacBook first (via Docker / local Next.js + FastAPI), or deploy it directly to the cloud (e.g., **Vercel** for Frontend + **Railway** for the Python FastAPI backend + **Supabase** cloud)?
2. **Additional Sample Documents:** Do you want to drop in any other sample reports/proposals right now so we can include their section structures in `design.md`, or should we proceed to `design.md` using this Geotechnical Field Report structure plus a flexible "Custom/Proposal Outline" mode?