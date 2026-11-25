export interface StyleGuide {
  tone: string;
  voice_rules: string[];
  preferred_nomenclature: string[];
  date_format: string;
  time_format: string;
  unit_conventions: Record<string, string>;
  standard_equations?: string[];
  banned_ai_phrases: string[];
}

export interface VaultChunk {
  id: string;
  vault_document_id: string;
  section_type: string;
  heading_title: string;
  content_text: string;
  tables_json?: Array<{
    id?: string;
    table_number?: string;
    title?: string;
    columns?: string[];
    rows?: string[][];
    row_count?: number;
  }>;
}

export interface ExtractedImageMeta {
  title: string;
  caption: string;
  category: string;
  ui_category?: string;
  dimensions?: string;
  file_url: string;
}

export interface ForensicEntityGraph {
  client_operators?: string[];
  lead_contractors?: string[];
  geotechnical_consultants?: string[];
  field_and_lab_subcontractors?: string[];
  key_personnel?: string[];
  equipment_and_vessels?: string[];
  document_reference_codes?: string[];
}

export interface ExtractedFormulaItem {
  name: string;
  formula_plain: string;
  formula_typst?: string;
}

export interface ExtractedTableSchema {
  table_number: string;
  title: string;
  columns: string[];
  row_count: number;
  section?: string;
}

export interface PdfLayoutBlueprint {
  source_document?: string;
  report_archetype?: string;
  splits_interpretative_factual?: boolean;
  page_size?: string;
  running_header?: string;
  cover_structure?: string[];
  front_matter_sections?: string[];
  heading_hierarchy?: string[];
  toc_style?: string;
  table_style?: string;
  figure_style?: string;
  detected_headings?: string[];
  table_schemas?: ExtractedTableSchema[];
  extracted_formulas?: ExtractedFormulaItem[];
  entities_json?: ForensicEntityGraph;
  metrics?: {
    table_count?: number;
    figure_count?: number;
    formula_count?: number;
    page_count?: number;
  };
}

export interface VaultDocument {
  id: string;
  filename: string;
  file_url: string;
  file_type: string;
  document_category: string;
  ingestion_status: string;
  chunk_count?: number;
  image_count?: number;
  extracted_images?: ExtractedImageMeta[];
  pdf_layout_blueprint?: PdfLayoutBlueprint;
  report_blueprint_json?: PdfLayoutBlueprint;
  entities_json?: ForensicEntityGraph;
  created_at: string;
  chunks?: VaultChunk[];
}

export interface GalleryAsset {
  id: string;
  title: string;
  default_caption: string;
  category: "vessel" | "drill_rig" | "lab_equipment" | "map" | "field_photo" | "logo" | "signature";
  file_url: string;
  tags: string[];
  created_at: string;
}

export interface ExternalImageCandidate {
  id: string;
  image_url: string;
  title: string;
  description: string;
  source_domain: string;
  source_url: string;
}

export interface WorkspaceSettings {
  id: string;
  default_contractor_name: string;
  default_contractor_logo_url: string;
  author_name: string;
  author_email: string;
  author_designation: string;
  author_signature_url: string;
  style_guide_json: StyleGuide;
  enable_passcode_gate: boolean;
  updated_at: string;
}

export interface ResearchSource {
  kind: "doc" | "file" | "chat" | "ticket" | "email" | "web" | "vault";
  site: string;
  label?: string;
  title: string;
  meta?: string;
  snippet: string;
  url?: string;
}

export interface ResearchMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ResearchSource[];
  steps?: unknown[];
  created_at: string;
}

export interface ResearchThread {
  id: string;
  project_id?: string | null;
  title: string;
  scope: "vault" | "web" | "both";
  messages_json: ResearchMessageItem[];
  created_at: string;
}
