import { API_BASE_URL } from "./constants";
import type {
  ClarificationItem,
  DocumentAst,
  Project,
  ProjectAttachment,
  ProjectInputFile,
  QaAlert,
} from "@/types/project";
import type {
  ExternalImageCandidate,
  GalleryAsset,
  ResearchThread,
  StyleGuide,
  VaultDocument,
  WorkspaceSettings,
} from "@/types/vault";

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
  error: {
    code: string;
    message: string;
    details?: unknown;
  } | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
  });

  const payload = (await res.json()) as ApiEnvelope<T>;
  if (!res.ok || !payload.success) {
    throw new Error(payload.error?.message || `API request failed (${res.status})`);
  }
  return payload.data;
}

export function resolveBackendUrl(url?: string | null): string {
  if (!url) return "";
  if (
    url.startsWith("http://") ||
    url.startsWith("https://") ||
    url.startsWith("data:")
  ) {
    return url;
  }
  const baseOrigin = API_BASE_URL.replace(/\/api\/v1$/, "");
  return `${baseOrigin}${url.startsWith("/") ? "" : "/"}${url}`;
}

export const apiClient = {
  // Projects
  listProjects: () => request<Project[]>("/projects"),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject: (body: Partial<Project>) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateProject: (id: string, body: Partial<Project>) =>
    request<Project>(`/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteProject: (id: string) =>
    request<{ deleted: boolean }>(`/projects/${id}`, { method: "DELETE" }),
  updateDocumentAst: (id: string, document_ast_json: DocumentAst) =>
    request<Project>(`/projects/${id}/document`, {
      method: "PATCH",
      body: JSON.stringify({ document_ast_json }),
    }),

  // Intake & Clarifications
  uploadIntakeFiles: (projectId: string, files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    return request<{
      uploaded: ProjectInputFile[];
      clarifications: ClarificationItem[];
    }>(`/projects/${projectId}/intake-files`, {
      method: "POST",
      body: fd,
    });
  },
  runIntakeAnalysis: (projectId: string, prompt: string) =>
    request<{ clarifications: ClarificationItem[] }>(
      `/projects/${projectId}/intake-analyze`,
      {
        method: "POST",
        body: JSON.stringify({ prompt }),
      },
    ),
  resolveClarifications: (
    projectId: string,
    items: Array<{
      id: string;
      user_response?: string;
      is_resolved: boolean;
      omit_section: boolean;
    }>,
  ) =>
    request<ClarificationItem[]>(`/projects/${projectId}/clarifications`, {
      method: "PATCH",
      body: JSON.stringify({ items }),
    }),

  // Studio AI, QA & Compilers
  inlineEdit: (
    projectId: string,
    body: { selection_text: string; instruction: string; section_context?: string },
  ) =>
    request<{ revised_text: string; style_notes: string }>(
      `/projects/${projectId}/inline-edit`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    ),
  expandSection: (
    projectId: string,
    sectionId: string,
    instruction: string,
  ) =>
    request<{ project: Project; section: unknown; page_count: number }>(
      `/projects/${projectId}/sections/${sectionId}/expand`,
      {
        method: "POST",
        body: JSON.stringify({ instruction }),
      },
    ),
  generateSectionChart: (
    projectId: string,
    sectionId: string,
    chart_type: string,
  ) =>
    request<{
      project: Project;
      chart: { title: string; caption: string; file_url: string; category: string };
      page_count: number;
    }>(`/projects/${projectId}/sections/${sectionId}/generate-chart`, {
      method: "POST",
      body: JSON.stringify({ chart_type }),
    }),
  getQaAlerts: (projectId: string) =>
    request<QaAlert[]>(`/projects/${projectId}/qa-alerts`),
  resolveQaAlert: (projectId: string, alertId: string, applyFix: boolean) =>
    request<{ alert: QaAlert; project: Project }>(
      `/projects/${projectId}/qa-alerts/${alertId}/resolve`,
      {
        method: "POST",
        body: JSON.stringify({ apply_fix: applyFix }),
      },
    ),
  compilePreview: (projectId: string) =>
    request<{ compiled_pdf_url: string; page_count: number }>(
      `/projects/${projectId}/compile-preview`,
      { method: "POST" },
    ),
  exportPackage: (projectId: string, format: "pdf" | "docx") =>
    request<{ download_url: string; filename: string; format: string }>(
      `/projects/${projectId}/export`,
      {
        method: "POST",
        body: JSON.stringify({ format }),
      },
    ),

  // Attachments
  uploadAttachment: (projectId: string, file: File, title: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title);
    return request<ProjectAttachment>(`/projects/${projectId}/attachments`, {
      method: "POST",
      body: fd,
    });
  },
  reorderAttachments: (projectId: string, orderedIds: string[]) =>
    request<ProjectAttachment[]>(`/projects/${projectId}/attachments/reorder`, {
      method: "PATCH",
      body: JSON.stringify({ ordered_ids: orderedIds }),
    }),
  deleteAttachment: (projectId: string, attachmentId: string) =>
    request<{ deleted: boolean }>(
      `/projects/${projectId}/attachments/${attachmentId}`,
      { method: "DELETE" },
    ),

  // Vault, Gallery & External Technical Image Search
  listVaultDocuments: () => request<VaultDocument[]>("/vault/documents"),
  uploadVaultDocument: (file: File, category: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("document_category", category);
    return request<VaultDocument>("/vault/documents", {
      method: "POST",
      body: fd,
    });
  },
  deleteVaultDocument: (id: string) =>
    request<{ deleted: boolean }>(`/vault/documents/${id}`, { method: "DELETE" }),
  listGalleryAssets: () => request<GalleryAsset[]>("/vault/gallery"),
  uploadGalleryAsset: (
    file: File,
    title: string,
    defaultCaption: string,
    category: string,
    tags: string[],
  ) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("title", title);
    fd.append("default_caption", defaultCaption);
    fd.append("category", category);
    fd.append("tags", tags.join(","));
    return request<GalleryAsset>("/vault/gallery", {
      method: "POST",
      body: fd,
    });
  },
  deleteGalleryAsset: (id: string) =>
    request<{ deleted: boolean }>(`/vault/gallery/${id}`, { method: "DELETE" }),
  searchExternalImages: (query: string, max_results = 8) =>
    request<ExternalImageCandidate[]>("/vault/images/search", {
      method: "POST",
      body: JSON.stringify({ query, max_results }),
    }),
  cacheExternalImage: (body: {
    image_url: string;
    title: string;
    caption?: string;
    category?: string;
    source_url?: string;
  }) =>
    request<GalleryAsset>("/vault/images/cache", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Research
  listResearchThreads: () => request<ResearchThread[]>("/research/threads"),
  deleteResearchThread: (id: string) =>
    request<{ deleted: boolean }>(`/research/threads/${id}`, { method: "DELETE" }),
  queryResearch: (body: {
    query: string;
    scope: "vault" | "web" | "both";
    thread_id?: string | null;
    project_id?: string | null;
  }) =>
    request<{
      thread: ResearchThread;
      sources: unknown[];
      answer: string;
      steps: unknown[];
    }>("/research/query", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // Settings & Auth
  getSettings: () => request<WorkspaceSettings>("/settings"),
  updateSettings: (
    body: Partial<WorkspaceSettings> & {
      style_guide_json?: StyleGuide;
    },
  ) =>
    request<WorkspaceSettings>("/settings", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  uploadBrandingAsset: (file: File, kind: "logo" | "signature") => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("kind", kind);
    return request<{ url: string }>("/settings/upload-asset", {
      method: "POST",
      body: fd,
    });
  },
  unlockPasscode: (passcode: string) =>
    request<{ authenticated: boolean }>("/auth/unlock", {
      method: "POST",
      body: JSON.stringify({ passcode }),
    }),
};
