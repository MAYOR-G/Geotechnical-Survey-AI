export type ProjectStatus =
  | "intake"
  | "clarifying"
  | "drafting"
  | "review"
  | "completed";

export interface HeaderLogo {
  role: "client" | "contractor" | "partner";
  label: string;
  url: string;
}

export interface RevisionRow {
  rev: string;
  date: string;
  description: string;
  prepared_by: string;
  checked_by: string;
  approved_by: string;
}

export interface AuthorizationRow {
  role: "Prepared By" | "Reviewed By" | "Approved By" | string;
  name: string;
  designation: string;
  email: string;
  date: string;
  signature_url?: string;
}

export interface EngineeringTableData {
  id: string;
  title: string;
  table_number?: string;
  multi_header?: Array<Array<{ label: string; colspan?: number; rowspan?: number }>>;
  columns: string[];
  rows: Array<Array<string | number>>;
  source_file?: string;
  footnote?: string;
}

export interface SmartPlaceholderNode {
  id: string;
  figure_number: string;
  prompt: string;
  suggested_category?: string;
  resolved_asset_id?: string | null;
  resolved_url?: string | null;
  caption?: string | null;
  secondary_url?: string | null;
  secondary_caption?: string | null;
  layout?: "single" | "side_by_side" | "stacked";
}

export interface ReportSectionBlock {
  id: string;
  section_number: string;
  title: string;
  category: string;
  html_content: string;
  tables?: EngineeringTableData[];
  placeholders?: SmartPlaceholderNode[];
}

export interface DocumentAst {
  report_title: string;
  report_subtitle: string;
  program_title?: string;
  location_line: string;
  campaign_dates: string;
  abbreviations: Array<{ term: string; definition: string }>;
  sections: ReportSectionBlock[];
}

export interface ProjectInputFile {
  id: string;
  project_id: string;
  filename: string;
  file_url: string;
  file_type: string;
  parsed_summary_json?: Record<string, unknown> | null;
  created_at: string;
}

export interface ProjectAttachment {
  id: string;
  project_id: string;
  attachment_number: string;
  title: string;
  file_url: string;
  display_order: number;
  page_count?: number;
  created_at: string;
}

export interface ClarificationItem {
  id: string;
  project_id: string;
  category: "missing_data" | "conflict" | "image_needed" | "scope_confirmation";
  question_text: string;
  context_reference: string;
  suggested_answer?: string | null;
  user_response?: string | null;
  is_resolved: boolean;
  omit_section: boolean;
}

export interface QaAlert {
  id: string;
  project_id: string;
  severity: "warning" | "error" | "info";
  section_id: string;
  field_label: string;
  source_value: string;
  draft_value: string;
  message: string;
  is_resolved: boolean;
}

export interface Project {
  id: string;
  title: string;
  subtitle?: string;
  document_type: string;
  status: ProjectStatus;
  client_name: string;
  contractor_name: string;
  client_ref_code: string;
  contractor_ref_code: string;
  revision_number: string;
  fao_text?: string;
  water_depth_range?: string;
  vessel_name?: string;
  header_logos_json: HeaderLogo[];
  revision_history_json: RevisionRow[];
  authorization_matrix_json: AuthorizationRow[];
  document_ast_json: DocumentAst;
  compiled_pdf_url?: string | null;
  compiled_docx_url?: string | null;
  created_at: string;
  updated_at: string;
  input_files?: ProjectInputFile[];
  attachments?: ProjectAttachment[];
  clarifications?: ClarificationItem[];
  qa_alerts?: QaAlert[];
}
