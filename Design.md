# DESIGN.md — Cupertino Studio Design System for AI Engineering Documentation & Technical Report Studio

**Version:** 1.0.0  
**Visual Direction:** Option A — Cupertino Studio (Apple Reference — Light-Dominant Workspace, True-Black Global Nav, Frosted Parchment Sub-Nav, Single Action-Blue Accent)  
**Source of Truth Alignment:** `PRD.md` v1.0.0  

---

## 1. Visual Direction & Design Principles

### 1.1 Aesthetic Philosophy & Brand Personality
The **AI Engineering Documentation & Technical Report Studio** translates Apple's signature museum-gallery design language into a precision technical authoring environment. In this workspace, **the engineering report, coordinate tables, and live A4 PDF artifact are the hero**—the surrounding application chrome recedes into near-invisibility.

Surfaces alternate deliberately between **Pure White (`#FFFFFF`)**, **Apple Parchment (`#F5F5F7`)**, and **Near-Black Tile (`#272729`)** beneath a pinned **44px True-Black Global Nav (`#000000`)** and a **52px Frosted Glass Sub-Nav (`rgba(245, 245, 247, 0.80)`)**. Every interactive signal across the entire application is carried by a single, authoritative **Action Blue (`#0066CC`)**. Elevation is flat across all UI cards and buttons; the single drop-shadow in the system (`rgba(0, 0, 0, 0.22) 3px 5px 30px 0`) is reserved exclusively to float the live A4 PDF document sheet and photographic equipment renders above the Parchment canvas.

### 1.2 Core UX Principles
1. **Artifact Over Chrome (Zero-Clutter Split Studio):** By replacing a traditional bulky left sidebar with the slim Apple Two-Tier Top Navigation (`44px` Global Nav + `52px` Frosted Sub-Nav), 100% of the horizontal viewport width is dedicated to the 50/50 Split-Screen Rich Editor and Live A4 PDF Preview.
2. **One Accent, Unmistakable Intent:** `#0066CC` (Action Blue) is the exclusive signal for primary buttons, text links, inline AI highlight triggers, and selected option chips. Users never have to guess what is clickable.
3. **Typography & Surface Rhythm as Dividers:** Section boundaries are created through generous whitespace (`24px–80px`), surface shifts (`#FFFFFF` ↔ `#F5F5F7` ↔ `#272729`), and tight negative-tracked `SF Pro Display` headings—never heavy boxes or drop-shadows on cards.
4. **Tabular Precision for Engineering Data:** While narrative report text runs at an editorial `17px` (`1.47` line-height) for effortless reading, wide engineering tables (15-column coordinate sheets, borehole logs, sequence timestamps) lock into `12px–13px` `tabular-nums` monospace cells with crisp `1px solid #E0E0E0` hairlines and smooth horizontal scrolling.
5. **Tactile Micro-Feedback:** Every button and interactive pill responds to press/active states with `transform: scale(0.95)` over `150ms`, providing physical, hardware-grade responsiveness.

### 1.3 Anti-Patterns (Strict Rules on What to Avoid)
- **NO AI-SaaS Neon Gradients or Glowing Blobs:** Never use purple-to-blue gradients, glowing mesh backgrounds, or rainbow AI sparkles anywhere in the UI or inline editor toolbar.
- **NO Drop Shadows on Cards, Buttons, or Inputs:** Cards use a `1px solid #E0E0E0` hairline border on white or sit flat on `#F5F5F7`. Only the rendered A4 PDF page and equipment/field photography receive the `rgba(0, 0, 0, 0.22) 3px 5px 30px 0` shadow.
- **NO Secondary Brand Colors:** Do not introduce teal, violet, or orange brand accents. Semantic status colors (Success, Warning, Error) appear strictly inside validation badges, QA alerts, and toasts.
- **NO Font Weight 500:** Follow the strict Apple weight ladder (`300`, `400`, `600`, `700`). Body is `400`; strong inline and display headings are `600`.
- **NO Mixed Border Radii:** Strictly enforce the radius grammar: `0px` (full-bleed tiles/A4 paper), `8px` (compact dark utility buttons & inner card images), `11px` (pearl secondary buttons), `18px` (workspace utility cards & modals), and `9999px` (primary blue pill CTAs, filter chips, and search inputs).

---

## 2. Color System & Semantic Tokens

Variability across light workspace surfaces and dark console drawers is governed by the exact tokens below.

### 2.1 Surface & Background Tokens

| Semantic Token | Hex / RGBA Value | RGB | Usage Specification |
| :--- | :--- | :--- | :--- |
| `{colors.canvas}` | `#FFFFFF` | `rgb(255, 255, 255)` | Utility cards, TipTap editor surface, A4 PDF paper sheet, modals |
| `{colors.canvas-parchment}` | `#F5F5F7` | `rgb(245, 245, 247)` | Default application page backdrop, PDF preview stage backdrop, footer |
| `{colors.surface-frosted}` | `rgba(245, 245, 247, 0.80)` | — | Sticky 52px Sub-Nav and floating bottom action bar (`backdrop-filter: saturate(180%) blur(20px)`) |
| `{colors.surface-pearl}` | `#FAFAFC` | `rgb(250, 250, 252)` | Secondary "Pearl" capsule button fill and subtle table header row tint |
| `{colors.surface-black}` | `#000000` | `rgb(0, 0, 0)` | Persistent 44px Global Top Navigation bar background |
| `{colors.surface-tile-1}` | `#272729` | `rgb(39, 39, 41)` | Dark-mode agent pipeline drawer, dark feature banner tiles |
| `{colors.surface-tile-2}` | `#2A2A2C` | `rgb(42, 42, 44)` | Elevated card surface inside dark agent pipeline/research drawers |
| `{colors.surface-tile-3}` | `#252527` | `rgb(37, 37, 39)` | Code/log viewer well and dark bottom stack |
| `{colors.surface-chip-translucent}` | `rgba(210, 210, 215, 0.64)` | — | 44x44px circular control buttons floating over field photography or PDF zoom controls |
| `{colors.overlay-modal}` | `rgba(29, 29, 31, 0.48)` | — | Backdrop dimmer behind centered modals and slide-over drawers (`backdrop-filter: blur(8px)`) |

### 2.2 Typography Tokens

| Semantic Token | Hex Value | RGB | Usage Specification |
| :--- | :--- | :--- | :--- |
| `{colors.ink}` / `{colors.body}` | `#1D1D1F` | `rgb(29, 29, 31)` | Primary headlines, default body copy, table cell values, dark utility button fill |
| `{colors.ink-muted-80}` | `#333333` | `rgb(51, 51, 51)` | Secondary body copy, Pearl button labels, table column headers |
| `{colors.ink-muted-48}` | `#7A7A7A` | `rgb(122, 122, 122)` | Input placeholders, disabled button labels, timestamps, micro legal/ref notes |
| `{colors.body-on-dark}` | `#FFFFFF` | `rgb(255, 255, 255)` | Primary text inside the 44px Global Nav and dark agent drawers |
| `{colors.body-muted-on-dark}` | `#CCCCCC` | `rgb(204, 204, 204)` | Secondary text and log descriptions on dark surfaces (`#272729`) |

### 2.3 Brand & Interactive Accent Tokens

| Semantic Token | Hex Value | RGB | Usage Specification |
| :--- | :--- | :--- | :--- |
| `{colors.primary}` | `#0066CC` | `rgb(0, 102, 204)` | Single brand interactive color: Primary pill CTAs, inline links, active editor tools |
| `{colors.primary-focus}` | `#0071E3` | `rgb(0, 113, 227)` | 2px solid keyboard focus ring and selected configurator/template chip border |
| `{colors.primary-on-dark}` | `#2997FF` | `rgb(41, 151, 255)` | Interactive links, citation badges, and active tab indicators on `#000000` / `#272729` surfaces |
| `{colors.primary-tint}` | `rgba(0, 102, 204, 0.08)` | — | Subtle highlight background for selected text ranges during inline AI prompting |

### 2.4 Hairlines & Border Tokens

| Semantic Token | Hex / RGBA Value | Usage Specification |
| :--- | :--- | :--- |
| `{colors.hairline}` | `#E0E0E0` | 1px solid border on utility cards, inputs, and engineering data table grids |
| `{colors.divider-soft}` | `#F0F0F0` / `rgba(0, 0, 0, 0.04)` | 3px soft ring on Pearl capsule buttons and subtle row dividers |
| `{colors.hairline-frosted}` | `rgba(0, 0, 0, 0.08)` | 1px bottom border on the 52px Frosted Sub-Nav and search input |
| `{colors.hairline-on-dark}` | `#38383A` | 1px solid divider inside dark drawers (`#272729`) |

### 2.5 Semantic Status Tokens (QA Verification, Intake & Alerts Only)

| Status | Background Tint | Border Hex | Text / Icon Hex | Usage Context |
| :--- | :--- | :--- | :--- | :--- |
| **Success (Verified)** | `#F2FAF5` | `#A3E2B8` | `#106831` | QA numeric cross-check passed, Vault document indexed, Export complete |
| **Warning (QA Alert / Missing Input)** | `#FFF9EB` | `#F5D07E` | `#945800` | Intake Clarification required, QA coordinate mismatch alert, Smart Image Placeholder |
| **Danger / Error** | `#FFF2F2` | `#F5B3B3` | `#C91919` | Unparseable Excel file, failed API call, destructive delete confirmation |
| **Info (Agent Active)** | `#F0F7FF` | `#B8D9FF` | `#0066CC` | Active multi-agent drafting step, inline AI diff preview |

---

## 3. Typography System

### 3.1 Font Families
- **Display & Headlines (`{font.display}`):** `'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Inter', system-ui, sans-serif` (Used for sizes `>= 19px`; if falling back to `Inter` on non-Apple OS, enable `font-feature-settings: "ss03"`).
- **Body & UI Controls (`{font.body}`):** `'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Inter', system-ui, sans-serif` (Used for prose, buttons, captions, and navigation below `20px`).
- **Technical Monospace (`{font.mono}`):** `'SF Mono', 'JetBrains Mono', ui-monospace, monospace` (Used for Easting/Northing coordinates, WGS84 Lat/Long, depth intervals `0.0m - 120.0m mBSF`, document reference codes `8385-GRN1-AARB-00003`, and 24-hour timestamps)[cite: 1].

### 3.2 Complete Type Scale

| Token Name | Size (`px` / `rem`) | Weight | Line Height | Letter Spacing | Primary Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `{typography.hero-display}` | `56px` / `3.5rem` | `600` | `1.07` | `-0.28px` | Onboarding welcome hero, empty workspace statement |
| `{typography.display-lg}` | `40px` / `2.5rem` | `600` | `1.10` | `0px` | Page headers (`/dashboard`, `/vault`, `/research`) |
| `{typography.display-md}` | `34px` / `2.125rem` | `600` | `1.20` | `-0.374px` | Report H1 Cover Title & Major Section Headers (`1. EXECUTIVE SUMMARY`) |
| `{typography.lead}` | `28px` / `1.75rem` | `400` | `1.14` | `0.196px` | Wizard step subheaders, report cover subtitle (`Anyala East & Central Locations`) |
| `{typography.lead-airy}` | `24px` / `1.5rem` | `300` | `1.50` | `0px` | Executive summary callout text, onboarding lead copy (rare weight 300) |
| `{typography.tagline}` | `21px` / `1.3125rem` | `600` | `1.19` | `0.231px` | 52px Frosted Sub-Nav Project Title, Report H2 (`2.1 Project Description`) |
| `{typography.button-large}` | `18px` / `1.125rem` | `300` | `1.00` | `0px` | Primary Hero CTA buttons (`New Project Folder`) |
| `{typography.body-strong}` | `17px` / `1.0625rem` | `600` | `1.24` | `-0.374px` | Card titles, Report H3 (`3.1.1 Anyala East SOW`), strong inline prose |
| `{typography.body}` | `17px` / `1.0625rem` | `400` | `1.47` | `-0.374px` | Default editor report paragraphs, primary pill button labels, search input |
| `{typography.dense-link}` | `17px` / `1.0625rem` | `400` | `2.41` | `0px` | Document outline navigation links, footer utility columns |
| `{typography.caption-strong}` | `14px` / `0.875rem` | `600` | `1.29` | `-0.224px` | Form field labels, table column headers, figure/table caption prefixes |
| `{typography.caption}` / `{typography.button-utility}` | `14px` / `0.875rem` | `400` | `1.43` | `-0.224px` | Sub-nav utility links, Pearl button labels, QA alert copy, image captions |
| `{typography.table-mono}` | `12.5px` / `0.781rem` | `400` | `1.35` | `0px` | Coordinate table cells, depth logs, revision history cells (`tabular-nums`) |
| `{typography.nav-link}` / `{typography.fine-print}` | `12px` / `0.75rem` | `400` | `1.00` | `-0.12px` | 44px Global Top Nav items, metadata badges, revision footers |
| `{typography.micro-legal}` | `10px` / `0.625rem` | `400` | `1.30` | `-0.08px` | Proprietary copyright blocks, coordinate datum footnotes (`WGS84`) |

### 3.3 Readability & Numeric Formatting Rules
- **Prose Measure:** In the TipTap Rich Editor and Research Assistant, narrative paragraphs are constrained to a maximum measure of `68ch` (`~680px`) so the eye scans comfortably at `17px / 1.47`. Wide engineering tables break out of the `68ch` text column to use 100% of the pane width.
- **Strict Tabular Numerals:** All numeric columns (Easting, Northing, Distance from Target, Bearing, Water Depth, Borehole Depth Intervals) MUST enforce `font-variant-numeric: tabular-nums` so decimal points align vertically down every column.

---

## 4. Spacing, Layout Grid & Elevation System

### 4.1 Spatial Scale (8px Base Unit)
- `{spacing.xxs}`: `4px` (tight inline icon-to-text gap)
- `{spacing.xs}`: `8px` (button clusters, badge padding)
- `{spacing.sm}`: `12px` (compact form field gaps, table cell horizontal padding)
- `{spacing.md}`: `17px` (default paragraph vertical rhythm)
- `{spacing.lg}`: `24px` (standard utility card internal padding, grid gutters)
- `{spacing.xl}`: `32px` (major panel padding, modal internal padding)
- `{spacing.xxl}`: `48px` (header-to-grid vertical clearance)
- `{spacing.section}`: `80px` (full-bleed section vertical padding on `/dashboard` and `/vault` hero bands)

### 4.2 Grid & Container Specifications
- **Dashboard, Vault, Research & Settings Max-Width:** `1440px` centered container with `32px` horizontal padding (`20px` on tablet/phone).
- **Intake Wizard & Clarification Flow Max-Width:** `980px` centered editorial container for focused form completion and Q&A verification.
- **Split-Screen Document Studio (`/projects/[id]/studio`):** `100vw` full-bleed viewport width locked below the `96px` combined top navigation (`calc(100vh - 96px)`), split into a `50%` Left Editor Pane and `50%` Right Live PDF Preview Stage (with a draggable `1px` center hairline divider allowing `40/60` or `60/40` resizing).

### 4.3 Border Radius Scale

| Token | Value | Applied Components |
| :--- | :--- | :--- |
| `{rounded.none}` | `0px` | Full-bleed page bands, A4 PDF preview pages, data table inner cells |
| `{rounded.xs}` | `5px` | Inline citation tags, keyboard shortcut hints (`⌘K`) |
| `{rounded.sm}` | `8px` | Dark utility buttons, inline editor floating toolbar, inner thumbnail crops |
| `{rounded.md}` | `11px` | Pearl secondary capsule buttons (`{component.button-pearl-capsule}`) |
| `{rounded.lg}` | `18px` | Project folder cards, Vault report cards, Equipment gallery cards, Modals, Smart Image Placeholders |
| `{rounded.pill}` | `9999px` | Primary Action Blue CTAs, ghost pill CTAs, template selector chips, search input |
| `{rounded.full}` | `50%` | 44x44px circular floating zoom/carousel icon buttons |

### 4.4 Depth & Elevation System
1. **Flat Surface Alternation (`Level 0`):** Zero shadow, zero border. Sections separate by alternating `{colors.canvas}` (`#FFFFFF`) and `{colors.canvas-parchment}` (`#F5F5F7`).
2. **Crisp Hairline (`Level 1`):** `1px solid #E0E0E0` (`{colors.hairline}`) on white utility cards, table grids, and inputs. Zero drop shadow.
3. **Frosted Glass Chrome (`Level 2`):** `background: rgba(245, 245, 247, 0.80); backdrop-filter: saturate(180%) blur(20px); border-bottom: 1px solid rgba(0, 0, 0, 0.08)` on the sticky 52px Sub-Nav and sticky bottom wizard bar.
4. **Artifact Pedestal Shadow (`Level 3 — Exclusive`):** `box-shadow: 3px 5px 30px 0px rgba(0, 0, 0, 0.22)`. Applied **ONLY** to:
   - The rendered A4 PDF sheets resting on the `#F5F5F7` preview stage.
   - Product/equipment renders or field photos resting inside preview cards.

---

## 5. Reusable Component Specifications

### 5.1 Top Navigation System (Two-Tier Cupertino Architecture)
- **`global-nav` (Row 1 — 44px Height):**
  - **Surface:** `{colors.surface-black}` (`#000000`), pinned at `top: 0`, `z-index: 50`.
  - **Typography:** `{typography.nav-link}` (`12px`, weight `400`, tracking `-0.12px`), default text `#CCCCCC`, active route `#FFFFFF`.
  - **Left/Center Items:** Brand Glyph + `Projects` (`/dashboard`), `Knowledge Vault` (`/vault`), `Research Assistant` (`/research`), `Defaults & Branding` (`/settings`). Spaced `28px` apart.
  - **Right Cluster:** Quick Search trigger (`⌘K`), Agent API Status dot, and single-user session lock icon.
- **`sub-nav-frosted` (Row 2 — 52px Height):**
  - **Surface:** `{colors.surface-frosted}` (`#F5F5F7` at 80% alpha + `saturate(180%) blur(20px)`), `border-bottom: 1px solid rgba(0, 0, 0, 0.08)`, pinned at `top: 44px`, `z-index: 40`.
  - **Left Content:** Current Context Title in `{typography.tagline}` (`21px`, weight `600`, `#1D1D1F`) + Revision Badge (`Rev 01`) and Auto-save indicator (`Saved 2s ago` in `12px` `#7A7A7A`).
  - **Right Content:** Contextual utility links in `{typography.button-utility}` (`14px`, `#1D1D1F`: `Outline`, `Clarifications (2)`, `Attachments (3)`, `Research Drawer`) terminating in a primary `{component.button-primary}` pill (`Export Report`).

### 5.2 Buttons
All buttons share `transition: transform 150ms cubic-bezier(0.25, 1, 0.5, 1), opacity 150ms ease`.
- **`button-primary` (Action Blue Pill):**
  - **Default:** Background `#0066CC`, text `#FFFFFF`, `{typography.body}` (`17px / 400`) or `{typography.button-utility}` (`14px / 400` in compact sub-nav), radius `{rounded.pill}` (`9999px`), padding `11px 22px` (`8px 18px` compact).
  - **Active / Pressed:** `transform: scale(0.95)`.
  - **Focus:** `outline: 2px solid #0071E3; outline-offset: 2px`.
  - **Disabled:** Background `#E0E0E0`, text `#7A7A7A`, `cursor: not-allowed`, no scale transform.
- **`button-secondary-pill` (Ghost Blue Pill):**
  - **Default:** Background `transparent`, text `#0066CC`, border `1px solid #0066CC`, radius `9999px`, padding `11px 22px`.
  - **Active / Pressed:** `background: rgba(0, 102, 204, 0.08)`, `transform: scale(0.95)`.
- **`button-pearl-capsule` (Neutral Workspace Action):**
  - **Default:** Background `#FAFAFC`, text `#333333` (`14px / 400`), border `3px solid #F0F0F0`, radius `{rounded.md}` (`11px`), padding `8px 14px`. Used for card actions (`View Chunks`, `Replace Image`, `Add Row`).
  - **Active / Pressed:** `transform: scale(0.95)`.
- **`button-dark-utility` (High-Contrast Utility Action):**
  - **Default:** Background `#1D1D1F`, text `#FFFFFF` (`14px / 400`), radius `{rounded.sm}` (`8px`), padding `8px 15px`. Used for `Run Intake Check`, `Refresh PDF Preview`, and inline AI toolbar submission.
  - **Active / Pressed:** `transform: scale(0.95)`.
- **`button-destructive` (Delete Action):**
  - **Default:** Background `#FFF2F2`, text `#C91919`, border `1px solid #F5B3B3`, radius `{rounded.pill}` (`9999px`), padding `8px 18px`.
- **`button-icon-circular` (Floating Canvas/Photo Control):**
  - **Default:** `44px × 44px`, background `rgba(210, 210, 215, 0.64)`, `backdrop-filter: blur(12px)`, icon `#1D1D1F`, radius `50%`. Used for PDF zoom (`+` / `-` / `Fit Page`) and image gallery preview controls.

### 5.3 Cards & Containers
- **`store-utility-card` (Project Folders, Vault Documents, Gallery Assets):**
  - **Surface:** Background `#FFFFFF`, border `1px solid #E0E0E0`, radius `{rounded.lg}` (`18px`), padding `24px`, zero shadow.
  - **Internal Layout:** Top client logo strip or 16:9/1:1 equipment preview (`8px` inner radius); middle title in `{typography.body-strong}` (`17px / 600`), metadata (`Client Ref`, `Water Depth`, `Last Edited`) in `{typography.caption}` (`14px` `#7A7A7A`); bottom row with status pill and `{component.text-link}` (`Open Studio →` in `#0066CC`).
- **`smart-image-placeholder-card` (In-Editor Visual Slot):**
  - **Surface:** Background `#F5F5F7`, border `1.5px dashed #0066CC`, radius `{rounded.lg}` (`18px`), padding `24px`.
  - **Content:** Camera/Rig icon + AI contextual prompt (e.g., *"Figure 4 Required: TH-30M Heave Compensated Drill Rig and Umbilical Winch"*) + two inline pills: `Select from Equipment Gallery` (`button-primary`) and `Upload Field Photo` (`button-secondary-pill`)[cite: 1].
- **`configurator-option-chip` (Template & Client Profile Selector):**
  - **Surface:** Background `#FFFFFF`, border `1px solid #E0E0E0`, radius `{rounded.pill}` (`9999px`), padding `12px 20px`.
  - **Selected State:** Border upgrades to `2px solid #0071E3`, subtle `#F0F7FF` background tint.

### 5.4 Tables & Engineering Data Grids
- **Workspace & Editor Data Table (`engineering-grid-table`):**
  - **Container:** Wrapped in a horizontal scroll container (`overflow-x: auto`) with `1px solid #E0E0E0` outer border and `8px` corner radius.
  - **Header Row (`<thead>`):** Multi-level support (`colspan` and `rowspan` for coordinate systems like `Minna/Nigeria West Belt` vs. `WGS84`), background `#F5F5F7`, text `{typography.caption-strong}` (`13px / 600`, `#1D1D1F`), cell borders `1px solid #E0E0E0`, padding `10px 12px`[cite: 1].
  - **Data Cells (`<td>`):** Background `#FFFFFF`, text `{typography.table-mono}` (`12.5px`, `SF Mono`, `tabular-nums`, `#1D1D1F`), cell borders `1px solid #E0E0E0`, padding `8px 12px`, `white-space: nowrap` on numeric coordinate columns.
  - **QA Mismatch Cell State:** Background `#FFF9EB`, border `1.5px solid #F5D07E`, with an inline amber info dot that opens a popover showing `Source Excel Value vs. Draft Value`.

### 5.5 Modals, Slide-Over Drawers & Floating Bars
- **Slide-Over Console Drawer (Research Agent & QA Verification Log):**
  - Slides in from the right edge (`width: 440px`), pinned below the `96px` top navbars.
  - Can toggle between Light Parchment (`#F5F5F7`) or Dark Console Mode (`#272729`) with `1px solid #E0E0E0` / `#38383A` left border.
- **Floating Inline AI Toolbar (`ai-selection-bar`):**
  - Appears `8px` above highlighted text or selected table cells in the TipTap editor.
  - Surface: `#1D1D1F` (Near-Black Ink), text `#FFFFFF`, radius `{rounded.pill}` (`9999px`), padding `6px 12px`.
  - Actions: Pill input (`Ask AI to edit selection...`) + quick chips (`Humanize`, `Match Vault Style`, `Condense`, `Verify Numbers`).
- **`floating-sticky-bar` (Intake Wizard & Clarification Approval Bar):**
  - Pinned to bottom of viewport (`height: 64px`), background `rgba(245, 245, 247, 0.80)` with `backdrop-filter: saturate(180%) blur(20px)`, `border-top: 1px solid rgba(0, 0, 0, 0.08)`.
  - Left: Status summary (`4 Raw Files Parsed · 3 Clarifications Resolved`). Right: `{component.button-primary}` (`Approve & Generate Draft`).

---

## 6. Navigation & Form UX Rules

### 6.1 Navigation Architecture
- **Desktop (`>= 834px`):** Persistent Two-Tier Cupertino Top Bar (`44px` Global Nav + `52px` Contextual Frosted Sub-Nav). Zero permanent left sidebar clutter. In the Studio (`/projects/[id]/studio`), clicking `Outline` in the Sub-Nav opens a clean, floating `260px` Table of Contents popover/drawer for instant section jumping (`1. Executive Summary` → `5. Field Results`)[cite: 1].
- **Tablet / Mobile (`< 834px`):** Global Nav collapses to Brand Glyph + Hamburger menu; Sub-Nav retains Project Title and the primary `Export` pill CTA.

### 6.2 Form & Input Standards
- **Search Inputs (`search-input`):** Height `44px`, background `#FFFFFF`, border `1px solid rgba(0, 0, 0, 0.08)`, radius `{rounded.pill}` (`9999px`), padding `12px 20px`, text `17px` `#1D1D1F`. Focus state: `2px solid #0071E3`.
- **Standard Form Inputs (Text, Reference Codes, Dates):** Height `44px`, background `#FFFFFF`, border `1px solid #E0E0E0`, radius `{rounded.sm}` (`8px`), padding `10px 14px`, text `17px` `#1D1D1F`.
- **Label Placement:** Stacked `6px` above the input in `{typography.caption-strong}` (`14px / 600`, `#1D1D1F`). Required fields use a subtle `(Required)` muted tag in `#7A7A7A` rather than noisy red asterisks.
- **Validation Timing:** Validate on `blur` for individual fields and on `submit` for wizard steps. Never display red error text while the user is actively typing a coordinate or reference code for the first time.

---

## 7. UI Feedback States (Loading, Empty & Error States)

### 7.1 Loading States & CLS Prevention
- **A4 PDF Preview Compilation:** Maintain exact A4 aspect ratio container (`1 : 1.4142`) on the right stage at all times so layout never shifts. During WeasyPrint recompilation, apply a `rgba(245, 245, 247, 0.65)` frosted overlay over the existing PDF page with a centered `14px` pill badge: `Updating paginated PDF & TOC...`.
- **Multi-Agent Drafting Stepper:** Displayed inside a `#272729` (Near-Black Tile 1) card with `#FFFFFF` text and `#2997FF` progress indicators:
  1. `Scanning Intake Files & Resolving Clarifications`
  2. `Retrieving Boilerplate & Style Rules from Vault`
  3. `Drafting Technical Sections & Engineering Tables`
  4. `Running Numeric Cross-Check & Anti-AI Humanizer Pass`
- **Skeleton Loaders:** Match exact `18px` card geometry using a subtle `#EAEAEF` → `#F5F5F7` pulse (`1.5s` ease-in-out).

### 7.2 Empty States
-Centered on a `#F5F5F7` or `#FFFFFF` tile with `64px` vertical air:
  - **Headline:** `{typography.display-md}` (`34px / 600`, `#1D1D1F`, tracking `-0.374px`).
  - **Subcopy:** `{typography.lead-airy}` (`24px / 300`, `#333333`, max-width `520px`).
  - **Action:** Single `{component.button-primary}` pill (`Upload Past Reports to Vault` or `Create First Project Folder`) `24px` below the subcopy.

### 7.3 Error & Fallback States
- **Inline Field & Upload Errors:** `1px solid #C91919` border on the input/dropzone, `#FFF2F2` background tint, and `14px` `#C91919` message directly below explaining the exact fix (e.g., *"File 'coordinates.xlsx' could not be read. Please upload a valid .xlsx or .csv sheet."*).
- **Toast Notifications:** Floating top-right below the `96px` nav stack, radius `18px`, background `#FFFFFF`, border `1px solid #E0E0E0`, padding `14px 20px`. Auto-dismisses after `4000ms` (persistent for QA warnings until dismissed).

---

## 8. Micro-Interactions & Motion Guidelines

- **Button Press Physics:** Every button and pill uses `transform: scale(0.95)` on `:active` with `transition: transform 150ms cubic-bezier(0.25, 1, 0.5, 1)`.
- **Drawer & Modal Transitions:** `250ms cubic-bezier(0.32, 0.72, 0, 1)` (Apple's signature spring-damped sheet curve) for slide-over Research/QA drawers and modal dialogs.
- **No Hover-Only Discovery:** Following the Apple iteration guide, critical actions (like replacing a Smart Image Placeholder, resolving a QA alert, or triggering an inline edit) are always visible in Default or Selected states—never hidden behind unlabelled hover states.
- **Reduced Motion:** Respect `@media (prefers-reduced-motion: reduce)` by replacing all slide and scale transforms with `120ms` opacity fades.

---

## 9. Responsive Behavior & Breakpoints

| Breakpoint Token | Viewport Range | Layout & Studio Adaptation |
| :--- | :--- | :--- |
| **Wide Desktop (`xl`)** | `>= 1441px` | Dashboard/Vault grids lock at `1440px` max-width (4 cards per row). Studio runs full-bleed `50/50` split with side-by-side Editor (`68ch` centered prose + full-width tables) and A4 PDF Preview. |
| **Desktop (`lg`)** | `1069px – 1440px` | 3-column utility card grids on Dashboard/Vault. Studio runs `50/50` split-screen canvas. |
| **Small Desktop (`md`)** | `834px – 1068px` | 2-column utility card grids. Studio split ratio defaults to `55%` Editor / `45%` PDF Preview; Research Drawer overlays rather than squeezing panes. |
| **Tablet (`sm`)** | `641px – 833px` | Global Nav collapses to hamburger. Studio automatically switches from side-by-side split to a sticky segmented pill toggle in the Sub-Nav: `[ Rich Editor | Live PDF Preview ]`. |
| **Phone (`xs`)** | `<= 640px` | Single-column card stack (`20px` side padding); vertical tile padding tightens from `80px` to `48px`; tables scroll horizontally with sticky first column (`S/N` / `Nomenclature`)[cite: 1]. |

---

## 10. Accessibility (a11y) Standards

- **Contrast Compliance:**
  - `#1D1D1F` on `#FFFFFF` (`16.8:1` — AAA) and `#1D1D1F` on `#F5F5F7` (`15.4:1` — AAA).
  - `#FFFFFF` on `#0066CC` Action Blue (`5.3:1` — AA).
  - `#2997FF` Sky Link Blue on `#272729` Dark Tile (`5.8:1` — AA).
- **Focus Rings:** Every interactive element displays `outline: 2px solid #0071E3; outline-offset: 2px` on `:focus-visible`.
- **Touch & Click Targets:** Minimum hit area of `44px × 44px` for all primary pill CTAs, circular gallery controls, and sub-nav actions.
- **Semantic Structure:** Proper landmark hierarchy (`<header>`, `<nav>`, `<main>`, `<aside>` for the Research/QA drawer), ARIA `role="region"` on the Split-Screen Editor and PDF Preview panes, and accessible `<caption >` + `<th scope="col">` attributes on all engineering tables.

---

## 11. Page-by-Page Layout Blueprint

### 11.1 `/login` — Private Passcode Gate
- **Layout Shell:** Full-viewport `#F5F5F7` Parchment canvas below the `44px` `#000000` Global Nav bar.
- **Visual Hierarchy:** Centered `420px` white `{component.store-utility-card}` (`18px` radius, `1px solid #E0E0E0` hairline, `32px` padding).
- **Components:** Studio title in `{typography.display-lg}` (`40px / 600`), subtitle in `{typography.caption}` (`14px` `#7A7A7A`), pill-shaped passcode input (`44px` height), and full-width `{component.button-primary}` pill (`Unlock Workspace`).

### 11.2 `/dashboard` — Client Projects Dashboard
- **Layout Shell:** Two-Tier Top Nav (`44px` Global Nav + `52px` Frosted Sub-Nav showing `Projects` on the left and a `+ New Project Folder` Action Blue pill CTA on the right).
- **Section 1 (Light Hero Summary Band — `#FFFFFF`):** Compact `48px` vertical padding band displaying workspace metrics (`Active Reports`, `Vault Style Rules Indexed`, `Reusable Equipment Assets`) in `40px / 600` numerals.
- **Section 2 (Projects Grid Band — `#F5F5F7`):** `1440px` container with a pill-shaped search bar (`{component.search-input}`) and status filter chips (`All`, `Clarification Needed`, `In Review`, `Exported`). Below sits a 3-column grid of `{component.store-utility-card}` items (`18px` radius). Each card displays the Client/Contractor logo header (e.g., *First E&P / GEMS / Enviros*), Document Title, Reference Code (`8385-GRN1-AARB-00003`), Revision badge (`Rev 01`), and `Open Studio →` link in `#0066CC`[cite: 1].

### 11.3 `/projects/new` — Project Setup, Raw Intake & Clarification Wizard
- **Layout Shell:** Two-Tier Top Nav + `980px` centered single-column stack on `#F5F5F7` + bottom `{component.floating-sticky-bar}`.
- **Step 1 Card (Client & Front-Matter Profile — `#FFFFFF`, `18px` radius):**
  - Template Selector chips (`Geotechnical Survey Field Report`, `Engineering Proposal`, `Custom Outline`).
  - 3-slot Header Logo Uploader (`Client Logo`, `Contractor Logo`, `Partner Logo`)[cite: 1].
  - Document Metadata inputs (`Client Name`, `Contractor Name`, `FAO`, `Client Ref`, `Contractor Ref`, `Revision Number`)[cite: 1].
  - Interactive `Document Authorization & Distribution Matrix` table (`Prepared By`, `Reviewed By`, `Approved By` with signature image picker)[cite: 1].
- **Step 2 Card (Raw Material Intake — `#FFFFFF`, `18px` radius):**
  - Drag-and-drop multi-file uploader for `.xlsx`/`.csv` coordinate logs, daily field notes, and field photos, plus a rich prompt textarea for campaign-specific instructions.
- **Step 3 Card (AI "Verify-First" Clarification Checklist — `#FFFFFF`, `18px` radius):**
  - Triggered after Intake Agent scans uploads. Displays a numbered list of `{component.store-utility-card}` items with `#FFF9EB` amber warning badges for missing or ambiguous data (e.g., missing water depth range, skipped borehole confirmation, or missing supervisor name). Each item has a direct text input and an `Omit from Report` pill toggle.
  - Bottom sticky frosted bar holds the primary `{component.button-primary}` (`Approve & Generate Draft`).

### 11.4 `/projects/[id]/studio` — Split-Screen Document Studio
- **Layout Shell:** Full-bleed `100vw × calc(100vh - 96px)` locked workspace below the `44px` Global Nav and `52px` Frosted Sub-Nav.
- **Sub-Nav Controls:** Left: Project Title + `Rev 01` badge + `Auto-saved`. Right: `Section Outline` toggle, `QA Alerts (0)` badge, `Attachments & Appendices (3)` modal button, `Research Agent` drawer toggle, and primary `Export` pill dropdown (`Export Master PDF (.pdf)` / `Export Editable Word (.docx)`).
- **Left Pane (`50%` Width — `#FFFFFF` Canvas):**
  - Scrollable TipTap Rich Editor surface (`48px` top/bottom padding, `40px` horizontal padding).
  - Supports structured numbered headings (`1.`, `2.1`, `3.1.1`), editable multi-column engineering tables (`{typography.table-mono}`), **Smart Image Placeholder Cards** (`18px` dashed `#0066CC` cards), and the floating `#1D1D1F` **Highlight-to-Prompt AI Toolbar**.
- **Right Pane (`50%` Width — `#F5F5F7` Parchment Stage):**
  - Renders vertically stacked, paginated A4 sheets (`210mm × 297mm` aspect ratio) centered on the `#F5F5F7` backdrop, elevated with the exclusive `rgba(0, 0, 0, 0.22) 3px 5px 30px 0` product shadow.
  - Displays exact corporate multi-logo headers, revision tables, signature blocks, auto-numbered Table of Contents / Figures / Tables, and appended external PDF attachments[cite: 1].
  - Floating bottom-right circular controls (`{component.button-icon-circular}`): Zoom Out, `100%`, Zoom In, and `Refresh PDF`.
- **Slide-Over Drawer (`440px` Right Overlay when toggled):**
  - Houses the **Embedded Research Agent** (Tavily + Internal Vault chat with one-click citation insertion) and the **QA & Anti-AI Humanizer Audit Log**.
- **Attachments & PDF Merger Modal:**
  - Centered `680px` modal (`18px` radius) allowing drag-and-drop ordering of external PDF attachments (`Attachment 1: Borehole Logs`, `Attachment 2: PCPT Plots`, `Attachment 3: Offshore Lab Summary`) that merge into the final exported PDF[cite: 1].

### 11.5 `/vault` — Knowledge & Style Vault
- **Layout Shell:** Two-Tier Top Nav + alternating full-bleed bands (`#FFFFFF` Hero Header → `#F5F5F7` Main Content Grid).
- **Sub-Nav Tabs:** Pill switcher for `Past Reports (8)`, `Author Style Fingerprint`, and `Equipment & Field Gallery (24)`.
- **Tab 1 (`Past Reports`):** Dropzone card at top; 3-column grid of indexed `.docx`/`.pdf` reports showing extracted section tags (`Abbreviations`, `Drilling Procedures`, `PCPT`, `Equipment Specs`) and a `View Indexed Boilerplate` Pearl button[cite: 1].
- **Tab 2 (`Author Style Fingerprint`):** Clean 2-column editorial view showing extracted writing rules, preferred engineering nomenclature (`mBSF`, `PCPT`, `COMPANY`), and the editable **Banned AI Clichés List**.
- **Tab 3 (`Equipment & Field Gallery`):** 4-column accessories-style grid of `{component.store-utility-card}` items (`18px` radius, `1:1` or `4:3` image crops with `8px` inner radius) for reusable assets like *DP-2 Dolphin Geo Survey*, *TH-30M Drill Rig*, *Umbilical Winch*, and *Triaxial Test Lab* with default captions[cite: 1].

### 11.6 `/research` — Standalone Research Workspace
- **Layout Shell:** Two-Tier Top Nav + `980px` centered editorial column on `#FFFFFF` with a sticky bottom pill prompt bar on `#F5F5F7`.
- **Components:** Source scope pill toggles (`Internal Vault`, `Live Web (Tavily)`, `Both`), chronological research thread with verified clickable source cards (`18px` radius, `#F5F5F7` fill), and a `Save Snippet to Project` button on every response.

### 11.7 `/settings` — Universal Defaults & Branding
- **Layout Shell:** Two-Tier Top Nav + `980px` centered stack of `#FFFFFF` utility cards on `#F5F5F7`.
- **Cards:**
  1. **Default Contractor & Author Identity:** Primary Contractor Name, Default Logo upload, Default Author Name, Email, Designation, and Digital Signature PNG upload[cite: 1].
  2. **AI Model Routing & API Keys:** OpenRouter model selectors (Default Drafting/Humanizer: `anthropic/claude-3.5-sonnet`; Default Intake/QA: `google/gemini-2.5-flash`), Tavily API status indicator, and Passcode Gate toggle.