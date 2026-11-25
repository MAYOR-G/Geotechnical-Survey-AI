export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const ENGINE_MODES = [
  {
    id: "tier1_tier2_pipeline",
    label: "Two-Tier Drafting & Editorial QA Verifier",
    role: "Iterative Section Drafting + Senior Geotechnical QA Audit",
  },
  {
    id: "drafting_engine",
    label: "Drafting Engine",
    role: "Workhorse Research, Data Extraction & Section Authoring",
  },
  {
    id: "qa_verifier",
    label: "Editorial & QA Verifier",
    role: "Numeric Cross-Check & Anti-AI Humanizer Pass",
  },
] as const;

export const REPORT_SECTION_CATEGORIES = [
  "Front_Matter",
  "Abbreviations",
  "Executive_Summary",
  "Introduction",
  "Scope_of_Work",
  "Equipment_Specs",
  "Procedures",
  "Sequence_of_Events",
  "Field_Results",
  "Appendices",
] as const;
