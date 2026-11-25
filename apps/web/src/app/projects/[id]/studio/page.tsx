"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  Columns2,
  Download,
  Eye,
  FileText,
  ListTree,
  Loader2,
  Maximize2,
  MessageSquare,
  Paperclip,
  Pencil,
  RefreshCw,
} from "lucide-react";
import { apiClient, resolveBackendUrl } from "@/lib/api-client";
import { API_BASE_URL } from "@/lib/constants";
import { useStudioStore } from "@/stores/useStudioStore";
import { FrostedSubNav } from "@/components/layout/FrostedSubNav";
import { Button } from "@/components/ui/Button";
import { SlideOverDrawer } from "@/components/ui/SlideOverDrawer";
import {
  ChatShell,
  type ShellChat,
} from "@/components/prestigeui/chat-shell";
import {
  ChatConversation,
  type ChatMessage,
} from "@/components/prestigeui/chat-conversation";
import type { PromptMessage } from "@/components/prestigeui/prompt-input";
import { BrandMark } from "@/components/prestigeui/prestige-brand";
import type { AnswerSource } from "@/components/prestigeui/cited-answer";
import { RichDocumentEditor } from "@/components/studio/RichDocumentEditor";
import { PaginatedPdfStage } from "@/components/studio/PaginatedPdfStage";
import { AttachmentsModal } from "@/components/studio/AttachmentsModal";
import type { DocumentAst } from "@/types/project";

export default function ProjectStudioPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const queryClient = useQueryClient();

  const {
    layoutMode,
    canvasMode,
    splitPercent,
    activeDrawer,
    attachmentsModalOpen,
    setLayoutMode,
    setCanvasMode,
    setSplitPercent,
    setActiveDrawer,
    setAttachmentsModalOpen,
  } = useStudioStore();

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.getProject(projectId),
  });

  const { data: galleryAssets = [] } = useQuery({
    queryKey: ["gallery-assets"],
    queryFn: apiClient.listGalleryAssets,
  });

  const { data: settings } = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: apiClient.getSettings,
  });

  const [saveState, setSaveState] = React.useState<"saved" | "saving" | "error">("saved");
  const [compilingPdf, setCompilingPdf] = React.useState(false);
  const [pdfViewerMode, setPdfViewerMode] = React.useState<"a4_sheets" | "compiled_pdf">(
    "compiled_pdf",
  );
  const [exportingFmt, setExportingFmt] = React.useState<"pdf" | "docx" | null>(
    null,
  );
  const [mobilePane, setMobilePane] = React.useState<"chat" | "document">("document");

  const saveTimerRef = React.useRef<number | null>(null);
  const saveSeqRef = React.useRef(0);
  const splitContainerRef = React.useRef<HTMLDivElement>(null);
  const isResizingRef = React.useRef(false);
  const launchedInitialPromptRef = React.useRef(false);

  // Studio Agent Chat State
  const [chats, setChats] = React.useState<ShellChat[]>([]);
  const [activeChatId, setActiveChatId] = React.useState<string>("main");
  const [threads, setThreads] = React.useState<Record<string, ChatMessage[]>>(
    {},
  );
  const streamAbortRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    return () => {
      streamAbortRef.current?.abort();
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
    };
  }, []);

  React.useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isResizingRef.current || !splitContainerRef.current) return;
      const rect = splitContainerRef.current.getBoundingClientRect();
      const pct = ((e.clientX - rect.left) / rect.width) * 100;
      setSplitPercent(pct);
    };
    const onMouseUp = () => {
      isResizingRef.current = false;
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [setSplitPercent]);

  React.useEffect(() => {
    if (!project) return;
    setChats((prev) =>
      prev.length > 0
        ? prev
        : [
            {
              id: "main",
              title: project.client_ref_code || project.title,
              pinned: true,
              updatedAt: Date.now(),
            },
          ],
    );

    setThreads((prev) => {
      if (prev.main) return prev;
      return { main: [] };
    });
  }, [project]);

  const handleSaveAst = (nextAst: DocumentAst) => {
    if (!project) return;
    const seq = ++saveSeqRef.current;
    queryClient.setQueryData(["project", projectId], {
      ...project,
      document_ast_json: nextAst,
    });
    setSaveState("saving");
    if (saveTimerRef.current) window.clearTimeout(saveTimerRef.current);
    saveTimerRef.current = window.setTimeout(async () => {
      try {
        const updated = await apiClient.updateDocumentAst(projectId, nextAst);
        if (seq !== saveSeqRef.current) return;
        queryClient.setQueryData(["project", projectId], updated);
        const compiled = await apiClient.compilePreview(projectId);
        if (seq !== saveSeqRef.current) return;
        queryClient.setQueryData(["project", projectId], {
          ...updated,
          compiled_pdf_url: compiled.compiled_pdf_url,
        });
        setSaveState("saved");
      } catch {
        if (seq === saveSeqRef.current) {
          setSaveState("error");
        }
      }
    }, 850);
  };

  const handleRefreshPdf = async () => {
    setCompilingPdf(true);
    try {
      const res = await apiClient.compilePreview(projectId);
      const latest = queryClient.getQueryData<typeof project>(["project", projectId]);
      if (latest) {
        queryClient.setQueryData(["project", projectId], {
          ...latest,
          compiled_pdf_url: res.compiled_pdf_url,
        });
      }
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    } finally {
      setCompilingPdf(false);
    }
  };

  const handleExport = async (format: "pdf" | "docx") => {
    setExportingFmt(format);
    try {
      const res = await apiClient.exportPackage(projectId, format);
      const url = resolveBackendUrl(res.download_url);
      const link = document.createElement("a");
      link.href = url;
      link.download = res.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    } finally {
      setExportingFmt(null);
    }
  };

  const patchMessage = (
    chatId: string,
    msgId: string,
    updater: (m: ChatMessage) => ChatMessage,
  ) => {
    setThreads((prev) => ({
      ...prev,
      [chatId]: (prev[chatId] ?? []).map((m) =>
        m.id === msgId ? updater(m) : m,
      ),
    }));
  };

  const handleChatSubmit = React.useCallback(
    async (
      message: PromptMessage,
      { signal }: { signal: AbortSignal },
    ) => {
      const chatId = activeChatId;
      const stamp = Date.now();
      const userMsgId = `u-${stamp}`;
      const assistantMsgId = `a-${stamp}`;

      streamAbortRef.current?.abort();
      const controller = new AbortController();
      streamAbortRef.current = controller;
      signal.addEventListener("abort", () => controller.abort());

      const rawFiles = (message.attachments ?? [])
        .map((att) => att.file)
        .filter((f): f is File => f instanceof File);

      const promptText =
        message.text.trim() ||
        (rawFiles.length > 0
          ? `Parse ${rawFiles.map((f) => f.name).join(", ")} and run the 5-stage report drafting pipeline.`
          : "Run the 5-stage report drafting and QA pipeline.");

      setThreads((prev) => ({
        ...prev,
        [chatId]: [
          ...(prev[chatId] ?? []),
          {
            id: userMsgId,
            role: "user",
            content: promptText,
            attachments: message.attachments,
            createdAt: stamp,
          },
          {
            id: assistantMsgId,
            role: "assistant",
            model: message.model,
            content: "",
            status: "thinking",
            stepsStatus: "running",
            steps: [],
            createdAt: stamp,
          },
        ],
      }));

      try {
        if (rawFiles.length > 0) {
          patchMessage(chatId, assistantMsgId, (m) => ({
            ...m,
            steps: [
              ...(m.steps ?? []),
              {
                id: "intake-upload",
                kind: "read",
                status: "running",
                title: `Uploading & parsing ${rawFiles.length} attached file(s)`,
                detail: rawFiles.map((f) => f.name).join(", "),
              },
            ],
          }));
          const uploadStart = Date.now();
          await apiClient.uploadIntakeFiles(projectId, rawFiles);
          await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
          patchMessage(chatId, assistantMsgId, (m) => ({
            ...m,
            steps: (m.steps ?? []).map((s) =>
              s.id === "intake-upload"
                ? {
                    ...s,
                    status: "done",
                    duration: Date.now() - uploadStart,
                    output: `Deterministically parsed **${rawFiles.length}** file(s) into project intake tables.`,
                  }
                : s,
            ),
          }));
        }

        const response = await fetch(
          `${API_BASE_URL}/projects/${projectId}/chat-stream`,
          {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: promptText,
              model: message.model,
            }),
            signal: controller.signal,
          },
        );

        if (!response.ok || !response.body) {
          throw new Error(`Agent stream error (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() || "";

          for (const rawEvent of events) {
            const lines = rawEvent.split("\n");
            let eventName = "message";
            let dataStr = "";
            for (const ln of lines) {
              if (ln.startsWith("event:")) eventName = ln.slice(6).trim();
              if (ln.startsWith("data:")) dataStr += ln.slice(5).trim();
            }
            if (!dataStr) continue;
            const payload = JSON.parse(dataStr);

            if (eventName === "reasoning_step") {
              patchMessage(chatId, assistantMsgId, (m) => {
                const existing = (m.steps ?? []).some((s) => s.id === payload.id);
                if (!existing) {
                  return {
                    ...m,
                    steps: [
                      ...(m.steps ?? []),
                      {
                        id: payload.id,
                        kind: payload.kind || "thought",
                        status: payload.status || "running",
                        title: payload.title,
                        detail: payload.detail,
                        duration: payload.duration,
                        output: payload.output,
                        results: payload.results,
                      },
                    ],
                  };
                }
                return {
                  ...m,
                  steps: (m.steps ?? []).map((s) =>
                    s.id === payload.id
                      ? {
                          ...s,
                          kind: payload.kind || s.kind,
                          status: payload.status || "done",
                          title: payload.title || s.title,
                          detail: payload.detail ?? s.detail,
                          duration: payload.duration ?? s.duration,
                          output: payload.output ?? s.output,
                          results: payload.results ?? s.results,
                        }
                      : s,
                  ),
                };
              });
            } else if (eventName === "step_start") {
              patchMessage(chatId, assistantMsgId, (m) => {
                if ((m.steps ?? []).some((s) => s.id === payload.id)) return m;
                return {
                  ...m,
                  steps: [
                    ...(m.steps ?? []),
                    {
                      id: payload.id,
                      kind: payload.kind || "tool",
                      status: "running",
                      title: payload.title,
                      detail: payload.detail,
                    },
                  ],
                };
              });
            } else if (eventName === "step_done") {
              patchMessage(chatId, assistantMsgId, (m) => ({
                ...m,
                steps: (m.steps ?? []).map((s) =>
                  s.id === payload.id
                    ? {
                        ...s,
                        status: "done",
                        duration: payload.duration,
                        output: payload.output,
                        results: payload.results,
                      }
                    : s,
                ),
              }));
            } else if (eventName === "approval_needed") {
              patchMessage(chatId, assistantMsgId, (m) => ({
                ...m,
                steps: [
                  ...(m.steps ?? []),
                  {
                    id: payload.id,
                    kind: "tool",
                    status: "approval",
                    title: payload.title,
                    detail: payload.detail,
                    approval: {
                      clarificationId: payload.clarification_id,
                      message: payload.message,
                      allowLabel: payload.allowLabel,
                      denyLabel: payload.denyLabel,
                      inputPlaceholder: payload.inputPlaceholder,
                    },
                  },
                ],
              }));
            } else if (eventName === "sources") {
              patchMessage(chatId, assistantMsgId, (m) => ({
                ...m,
                sources: payload.sources as AnswerSource[],
                citedStatus: "streaming",
              }));
            } else if (eventName === "error") {
              throw new Error(
                payload.message || "Agent execution failed. Check .env API credentials.",
              );
            } else if (eventName === "complete") {
              if (payload.project) {
                queryClient.setQueryData(["project", projectId], payload.project);
                await queryClient.invalidateQueries({ queryKey: ["gallery-assets"] });
              }
              patchMessage(chatId, assistantMsgId, (m) => ({
                ...m,
                status: "done",
                stepsStatus: "done",
                stepsDuration: Date.now() - stamp,
                content: payload.answer || m.content,
                sources: payload.sources || m.sources,
                citedStatus: payload.sources ? "done" : m.citedStatus,
                artifact: payload.artifact || m.artifact,
              }));
            }
          }
        }
      } catch (err) {
        patchMessage(chatId, assistantMsgId, (m) => ({
          ...m,
          status: controller.signal.aborted ? "stopped" : "error",
          stepsStatus: "done",
          error: controller.signal.aborted
            ? undefined
            : err instanceof Error
              ? err.message
              : "Stream error",
        }));
      }
    },
    [activeChatId, projectId, queryClient],
  );

  // Seamlessly continue initial prompt stored during /projects/new launch
  React.useEffect(() => {
    if (!project || launchedInitialPromptRef.current) return;
    const key = `geotech_initial_prompt_${projectId}`;
    const pendingPrompt =
      typeof window !== "undefined" ? window.sessionStorage.getItem(key) : null;
    if (!pendingPrompt) return;
    launchedInitialPromptRef.current = true;
    window.sessionStorage.removeItem(key);
    setMobilePane("chat");
    const autoController = new AbortController();
    void handleChatSubmit(
      { text: pendingPrompt, model: "studio-engine" },
      { signal: autoController.signal },
    );
  }, [project, projectId, handleChatSubmit]);

  const handleStepApproval = async (
    msgId: string,
    stepId: string,
    approve: boolean,
    extraAnswer?: string,
  ) => {
    const targetMsg = (threads[activeChatId] ?? []).find((m) => m.id === msgId);
    const step = targetMsg?.steps?.find((s) => s.id === stepId);
    const clarificationId = step?.approval?.clarificationId;

    if (clarificationId) {
      await apiClient.resolveClarifications(projectId, [
        {
          id: clarificationId,
          user_response:
            extraAnswer || step?.approval?.inputPlaceholder || "Confirmed",
          is_resolved: true,
          omit_section: !approve,
        },
      ]);
      await queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    }

    patchMessage(activeChatId, msgId, (m) => ({
      ...m,
      steps: (m.steps ?? []).map((s) =>
        s.id === stepId
          ? {
              ...s,
              status: approve ? "done" : "denied",
              duration: 180,
              output: approve
                ? `Confirmed: **${extraAnswer || s.approval?.inputPlaceholder || "Approved"}**`
                : "Omitted per engineer decision.",
            }
          : s,
      ),
    }));
  };

  const handleResolveQaAlert = async (alertId: string, applyFix: boolean) => {
    const res = await apiClient.resolveQaAlert(projectId, alertId, applyFix);
    queryClient.setQueryData(["project", projectId], res.project);
  };

  const handleInsertCitation = (content: string) => {
    if (!project) return;
    const ast = project.document_ast_json;
    const sections = ast.sections || [];
    if (sections.length === 0) return;
    const targetSec = sections[1] || sections[0];
    const cleanParagraph = `<p><strong>Research reference note:</strong> ${content.replace(/\n+/g, " ")}</p>`;
    const nextAst: DocumentAst = {
      ...ast,
      sections: sections.map((s) =>
        s.id === targetSec.id
          ? { ...s, html_content: `${s.html_content}${cleanParagraph}` }
          : s,
      ),
    };
    handleSaveAst(nextAst);
    setCanvasMode("edit");
    if (layoutMode === "chat") setLayoutMode("split");
  };

  if (isLoading || !project) {
    return (
      <div className="flex h-[calc(100dvh-44px)] items-center justify-center bg-white">
        <div className="inline-flex items-center gap-2.5 rounded-[10px] border border-[#E0E0E0] bg-white px-5 py-3 text-[14px] font-medium text-[#1D1D1F]">
          <Loader2 className="size-4 animate-spin text-[#0066CC]" />
          <span>Loading Geotechnical Document Studio</span>
        </div>
      </div>
    );
  }

  const openAlerts = (project.qa_alerts || []).filter((a) => !a.is_resolved);
  const sections = project.document_ast_json?.sections || [];
  const subtitleLabel =
    saveState === "saving"
      ? "Saving & compiling..."
      : saveState === "error"
        ? "Save error"
        : "Saved";

  return (
    <div className="flex h-[calc(100dvh-44px)] flex-col overflow-hidden bg-white">
      {/* Studio Contextual Sub-Nav */}
      <FrostedSubNav
        compact
        fullBleed
        title={project.title}
        badge={`Rev ${project.revision_number}`}
        subtitle={subtitleLabel}
        rightContent={
          <div className="flex items-center gap-2">
            {/* Desktop Workspace View Switcher: Agent+Canvas vs Editor+Live PDF vs Full Canvas */}
            <div className="hidden xl:flex items-center gap-0.5 rounded-[8px] border border-[#E0E0E0] bg-white p-0.5">
              <button
                type="button"
                onClick={() => setLayoutMode("split")}
                className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                  layoutMode === "split"
                    ? "bg-[#1D1D1F] text-white"
                    : "text-[#6E6E73] hover:text-[#1D1D1F]"
                }`}
              >
                <MessageSquare className="size-3.5" strokeWidth={1.5} />
                <span>Agent + Canvas</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setLayoutMode("editor_pdf");
                  setPdfViewerMode("compiled_pdf");
                }}
                className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                  layoutMode === "editor_pdf"
                    ? "bg-[#1D1D1F] text-white"
                    : "text-[#6E6E73] hover:text-[#1D1D1F]"
                }`}
              >
                <Columns2 className="size-3.5" strokeWidth={1.5} />
                <span>Editor + Live PDF</span>
              </button>
              <button
                type="button"
                onClick={() => setLayoutMode("canvas")}
                className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                  layoutMode === "canvas"
                    ? "bg-[#1D1D1F] text-white"
                    : "text-[#6E6E73] hover:text-[#1D1D1F]"
                }`}
              >
                <Maximize2 className="size-3.5" strokeWidth={1.5} />
                <span>Full Canvas</span>
              </button>
            </div>

            {/* Mobile/Tablet Pane Switcher */}
            <div className="flex lg:hidden items-center rounded-[8px] border border-[#E0E0E0] bg-white p-0.5">
              <button
                type="button"
                onClick={() => setMobilePane("chat")}
                className={`h-8 rounded-[6px] px-3 text-[12.5px] font-medium ${
                  mobilePane === "chat"
                    ? "bg-[#1D1D1F] text-white"
                    : "text-[#6E6E73]"
                }`}
              >
                Agent
              </button>
              <button
                type="button"
                onClick={() => setMobilePane("document")}
                className={`h-8 rounded-[6px] px-3 text-[12.5px] font-medium ${
                  mobilePane === "document"
                    ? "bg-[#1D1D1F] text-white"
                    : "text-[#6E6E73]"
                }`}
              >
                Document
              </button>
            </div>

            <button
              type="button"
              onClick={() =>
                setActiveDrawer(
                  activeDrawer === "outline" ? "none" : "outline",
                )
              }
              className="cupertino-press hidden sm:inline-flex h-9 items-center gap-1.5 rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7]"
            >
              <ListTree className="size-4 text-[#0066CC]" strokeWidth={1.5} />
              <span>Outline ({sections.length})</span>
            </button>

            <button
              type="button"
              onClick={() =>
                setActiveDrawer(activeDrawer === "qa_log" ? "none" : "qa_log")
              }
              className={`cupertino-press inline-flex h-9 items-center gap-1.5 rounded-[8px] border px-3 text-[13px] font-medium ${
                openAlerts.length > 0
                  ? "border-[#F5D07E] bg-[#FFF9EB] text-[#945800]"
                  : "border-[#A3E2B8] bg-[#F2FAF5] text-[#16A34A]"
              }`}
            >
              {openAlerts.length > 0 ? (
                <AlertTriangle className="size-4" strokeWidth={1.5} />
              ) : (
                <CheckCircle2 className="size-4" strokeWidth={1.5} />
              )}
              <span>QA ({openAlerts.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setAttachmentsModalOpen(true)}
              className="cupertino-press hidden md:inline-flex h-9 items-center gap-1.5 rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7]"
            >
              <Paperclip className="size-4 text-[#0066CC]" strokeWidth={1.5} />
              <span>Attachments ({project.attachments?.length ?? 0})</span>
            </button>

            <Button
              size="sm"
              disabled={exportingFmt !== null}
              onClick={() => void handleExport("pdf")}
            >
              {exportingFmt === "pdf" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Download className="size-4" strokeWidth={1.5} />
              )}
              <span>Export PDF</span>
            </Button>

            <Button
              variant="secondary-pill"
              size="sm"
              className="hidden sm:inline-flex"
              disabled={exportingFmt !== null}
              onClick={() => void handleExport("docx")}
            >
              {exportingFmt === "docx" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <FileText className="size-4 text-[#0066CC]" strokeWidth={1.5} />
              )}
              <span>Export Word</span>
            </Button>
          </div>
        }
      />

      {/* Full-Viewport Split Workspace */}
      <div
        ref={splitContainerRef}
        className="flex min-h-0 flex-1 overflow-hidden select-none sm:select-auto"
      >
        {layoutMode === "editor_pdf" ? (
          <>
            {/* SIDE-BY-SIDE MODE: LEFT BLOCK EDITOR (#FFFFFF) + RIGHT LIVE PAGINATED TYPST PDF (#F5F5F7) */}
            <div
              style={{ "--split-w": `${splitPercent}%` } as React.CSSProperties}
              className="flex h-full w-full lg:w-[var(--split-w)] shrink-0 flex-col bg-white"
            >
              <div className="flex h-10 shrink-0 items-center justify-between gap-2 border-b border-[#E0E0E0] bg-white px-4">
                <div className="flex items-center gap-2 text-[12.5px] font-medium text-[#1D1D1F]">
                  <Pencil className="size-3.5 text-[#0066CC]" strokeWidth={1.6} />
                  <span>Block &amp; Table Editor</span>
                </div>
                <select
                  aria-label="Jump to report section"
                  defaultValue=""
                  onChange={(e) => {
                    const targetId = e.target.value;
                    if (!targetId) return;
                    document
                      .getElementById(targetId)
                      ?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                  className="h-7 max-w-[200px] rounded-[7px] border border-[#E0E0E0] bg-[#F5F5F7] px-2 text-[12px] font-medium text-[#333333] focus:border-[#0066CC] focus:outline-none"
                >
                  <option value="">Jump to section...</option>
                  {sections.map((sec) => (
                    <option key={sec.id} value={sec.id}>
                      {sec.section_number} {sec.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="min-h-0 flex-1">
                <RichDocumentEditor
                  project={project}
                  galleryAssets={galleryAssets}
                  hideQuickJumpBar
                  onSaveAst={handleSaveAst}
                  onProjectUpdated={(updatedProj) => {
                    queryClient.setQueryData(["project", projectId], updatedProj);
                  }}
                  onResolveQaAlert={handleResolveQaAlert}
                  onRefreshGallery={() =>
                    void queryClient.invalidateQueries({
                      queryKey: ["gallery-assets"],
                    })
                  }
                />
              </div>
            </div>

            <div
              onMouseDown={() => {
                isResizingRef.current = true;
              }}
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize editor and PDF panes"
              className="hidden lg:flex w-1.5 shrink-0 cursor-col-resize items-center justify-center bg-[#E0E0E0] transition-colors hover:bg-[#0066CC]"
            >
              <div className="h-8 w-0.5 rounded-full bg-[#7A7A7A]" />
            </div>

            <div className="hidden lg:flex h-full min-w-0 flex-1 flex-col bg-[#F5F5F7]">
              <div className="flex h-10 shrink-0 items-center justify-between gap-2 border-b border-[#E0E0E0] bg-white px-4">
                <div className="flex items-center gap-0.5 rounded-[8px] border border-[#E0E0E0] bg-[#F5F5F7] p-0.5">
                  <button
                    type="button"
                    onClick={() => setPdfViewerMode("compiled_pdf")}
                    className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                      pdfViewerMode === "compiled_pdf"
                        ? "bg-[#0066CC] text-white"
                        : "text-[#6E6E73] hover:text-[#1D1D1F]"
                    }`}
                  >
                    <FileText className="size-3" strokeWidth={1.6} />
                    <span>Live Typst A4 PDF ({project.attachments?.length ?? 0})</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPdfViewerMode("a4_sheets")}
                    className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                      pdfViewerMode === "a4_sheets"
                        ? "bg-[#0066CC] text-white"
                        : "text-[#6E6E73] hover:text-[#1D1D1F]"
                    }`}
                  >
                    <Eye className="size-3" strokeWidth={1.6} />
                    <span>Paginated HTML Preview</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => void handleRefreshPdf()}
                  disabled={compilingPdf}
                  className="cupertino-press inline-flex h-7 items-center gap-1.5 rounded-[7px] bg-[#1D1D1F] px-2.5 text-[12px] font-medium text-white hover:opacity-90 disabled:opacity-60"
                >
                  {compilingPdf ? (
                    <Loader2 className="size-3 animate-spin" />
                  ) : (
                    <RefreshCw className="size-3" strokeWidth={1.6} />
                  )}
                  <span>{compilingPdf ? "Compiling" : "Recompile PDF"}</span>
                </button>
              </div>
              <div className="min-h-0 flex-1">
                <PaginatedPdfStage
                  project={project}
                  isCompiling={compilingPdf}
                  onRefreshPdf={() => void handleRefreshPdf()}
                  viewerMode={pdfViewerMode}
                  onViewerModeChange={setPdfViewerMode}
                  hideToolbar
                />
              </div>
            </div>
          </>
        ) : (
          <>
            {/* LEFT PANE: AGENT CHAT + LIVE REASONING TELEMETRY + CITED ANSWERS */}
            {layoutMode !== "canvas" ? (
              <div
                style={
                  layoutMode === "split"
                    ? ({ "--split-w": `${splitPercent}%` } as React.CSSProperties)
                    : undefined
                }
                className={
                  layoutMode === "chat"
                    ? "h-full w-full"
                    : `${
                        mobilePane === "chat" ? "flex" : "hidden lg:flex"
                      } h-full w-full lg:w-[var(--split-w)] shrink-0 flex-col bg-white`
                }
              >
                <ChatShell
                  borderless
                  compactHeader
                  className="h-full"
                  defaultCollapsed
                  brand={
                    <span className="flex items-center gap-2">
                      <BrandMark className="size-5" />
                      <span>Studio threads</span>
                    </span>
                  }
                  user={{
                    name: settings?.author_name || "Workspace User",
                    email: settings?.author_email || settings?.default_contractor_name || "",
                    plan: project.client_name || "Field Studio",
                  }}
                  chats={chats}
                  activeId={activeChatId}
                  onSelect={setActiveChatId}
                  onNewChat={() => {
                    const nid = `chat-${Date.now()}`;
                    setChats((prev) => [
                      { id: nid, title: "New drafting task", updatedAt: Date.now() },
                      ...prev,
                    ]);
                    setThreads((prev) => ({ ...prev, [nid]: [] }));
                    setActiveChatId(nid);
                  }}
                  onRename={(id, t) =>
                    setChats((prev) =>
                      prev.map((c) => (c.id === id ? { ...c, title: t } : c)),
                    )
                  }
                  onPin={(id, pinned) =>
                    setChats((prev) =>
                      prev.map((c) => (c.id === id ? { ...c, pinned } : c)),
                    )
                  }
                  onDelete={(id) =>
                    setChats((prev) => prev.filter((c) => c.id !== id))
                  }
                >
                  <ChatConversation
                    key={activeChatId}
                    className="h-full"
                    messages={threads[activeChatId] ?? []}
                    onSubmit={handleChatSubmit}
                    onStop={() => streamAbortRef.current?.abort()}
                    onApproveStep={(msgId, stepId, extra) =>
                      void handleStepApproval(msgId, stepId, true, extra)
                    }
                    onDenyStep={(msgId, stepId) =>
                      void handleStepApproval(msgId, stepId, false)
                    }
                    onOpenArtifact={(_art, mode) => {
                      setCanvasMode(mode);
                      setMobilePane("document");
                      if (layoutMode === "chat") setLayoutMode("split");
                    }}
                    onInsertCitation={handleInsertCitation}
                    emptyTitle="What are we drafting today?"
                    quickPrompts={[
                      "Run 5-stage report drafting, QA & humanizer pipeline",
                      "Research ISO 19901-8 & BS 1377 standards for this site",
                      "Verify coordinate and borehole tables against uploaded files",
                    ]}
                  />
                </ChatShell>
              </div>
            ) : null}

            {/* Interactive Draggable Divider */}
            {layoutMode === "split" ? (
              <div
                onMouseDown={() => {
                  isResizingRef.current = true;
                }}
                role="separator"
                aria-orientation="vertical"
                aria-label="Resize studio panes"
                className="hidden lg:flex w-1.5 shrink-0 cursor-col-resize items-center justify-center bg-[#E0E0E0] transition-colors hover:bg-[#0066CC]"
              >
                <div className="h-8 w-0.5 rounded-full bg-[#7A7A7A]" />
              </div>
            ) : null}

            {/* RIGHT PANE: DOCUMENT BLOCK EDITOR OR LIVE TYPST A4 PDF */}
            {layoutMode !== "chat" ? (
              <div
                className={
                  layoutMode === "canvas"
                    ? "flex h-full w-full flex-col bg-white"
                    : `${
                        mobilePane === "document" ? "flex" : "hidden lg:flex"
                      } h-full min-w-0 flex-1 flex-col bg-white`
                }
              >
                <div className="flex h-10 shrink-0 items-center justify-between gap-2 border-b border-[#E0E0E0] bg-white px-4">
                  <div className="flex items-center gap-0.5 rounded-[8px] border border-[#E0E0E0] bg-[#F5F5F7] p-0.5">
                    <button
                      type="button"
                      onClick={() => setCanvasMode("edit")}
                      className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                        canvasMode === "edit"
                          ? "bg-[#0066CC] text-white"
                          : "text-[#6E6E73] hover:text-[#1D1D1F]"
                      }`}
                    >
                      <Pencil className="size-3" strokeWidth={1.6} />
                      <span>Block Editor</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCanvasMode("preview");
                        setPdfViewerMode("compiled_pdf");
                      }}
                      className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                        canvasMode === "preview" && pdfViewerMode === "compiled_pdf"
                          ? "bg-[#0066CC] text-white"
                          : "text-[#6E6E73] hover:text-[#1D1D1F]"
                      }`}
                    >
                      <FileText className="size-3" strokeWidth={1.6} />
                      <span>Compiled Typst PDF ({project.attachments?.length ?? 0})</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCanvasMode("preview");
                        setPdfViewerMode("a4_sheets");
                      }}
                      className={`inline-flex h-7 items-center gap-1.5 rounded-[6px] px-2.5 text-[12px] font-medium transition-colors ${
                        canvasMode === "preview" && pdfViewerMode === "a4_sheets"
                          ? "bg-[#0066CC] text-white"
                          : "text-[#6E6E73] hover:text-[#1D1D1F]"
                      }`}
                    >
                      <Eye className="size-3" strokeWidth={1.6} />
                      <span>Paginated A4</span>
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    {canvasMode === "edit" ? (
                      <select
                        aria-label="Jump to report section"
                        defaultValue=""
                        onChange={(e) => {
                          const targetId = e.target.value;
                          if (!targetId) return;
                          document
                            .getElementById(targetId)
                            ?.scrollIntoView({ behavior: "smooth", block: "start" });
                        }}
                        className="hidden md:block h-7 max-w-[180px] rounded-[7px] border border-[#E0E0E0] bg-[#F5F5F7] px-2 text-[12px] font-medium text-[#333333] focus:border-[#0066CC] focus:outline-none"
                      >
                        <option value="">Jump to section...</option>
                        {sections.map((sec) => (
                          <option key={sec.id} value={sec.id}>
                            {sec.section_number} {sec.title}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <button
                        type="button"
                        onClick={() => void handleRefreshPdf()}
                        disabled={compilingPdf}
                        className="cupertino-press inline-flex h-7 items-center gap-1.5 rounded-[7px] bg-[#1D1D1F] px-2.5 text-[12px] font-medium text-white hover:opacity-90 disabled:opacity-60"
                      >
                        {compilingPdf ? (
                          <Loader2 className="size-3 animate-spin" />
                        ) : (
                          <RefreshCw className="size-3" strokeWidth={1.6} />
                        )}
                        <span>{compilingPdf ? "Compiling" : "Recompile PDF"}</span>
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => {
                        setLayoutMode("editor_pdf");
                        setPdfViewerMode("compiled_pdf");
                      }}
                      className="cupertino-press hidden lg:inline-flex xl:hidden h-7 items-center gap-1.5 rounded-[7px] border border-[#E0E0E0] bg-[#F5F5F7] px-2.5 text-[12px] font-medium text-[#1D1D1F] hover:bg-[#ECECEC]"
                    >
                      <Columns2 className="size-3" strokeWidth={1.5} />
                      <span>Editor + PDF</span>
                    </button>
                  </div>
                </div>

                <div className="min-h-0 flex-1">
                  {canvasMode === "edit" ? (
                    <RichDocumentEditor
                      project={project}
                      galleryAssets={galleryAssets}
                      hideQuickJumpBar
                      onSaveAst={handleSaveAst}
                      onProjectUpdated={(updatedProj) => {
                        queryClient.setQueryData(["project", projectId], updatedProj);
                      }}
                      onResolveQaAlert={handleResolveQaAlert}
                      onRefreshGallery={() =>
                        void queryClient.invalidateQueries({
                          queryKey: ["gallery-assets"],
                        })
                      }
                    />
                  ) : (
                    <PaginatedPdfStage
                      project={project}
                      isCompiling={compilingPdf}
                      onRefreshPdf={() => void handleRefreshPdf()}
                      viewerMode={pdfViewerMode}
                      onViewerModeChange={setPdfViewerMode}
                      hideToolbar
                    />
                  )}
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>

      {/* Section Outline Slide-Over Drawer */}
      <SlideOverDrawer
        open={activeDrawer === "outline"}
        onClose={() => setActiveDrawer("none")}
        title="Report Table of Contents"
        subtitle={`${sections.length} structured sections`}
      >
        <div className="space-y-2">
          {sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => {
                if (layoutMode !== "editor_pdf") {
                  setCanvasMode("edit");
                }
                if (layoutMode === "chat") setLayoutMode("split");
                setActiveDrawer("none");
                window.setTimeout(() => {
                  document
                    .getElementById(sec.id)
                    ?.scrollIntoView({ behavior: "smooth" });
                }, 60);
              }}
              className="flex w-full items-center justify-between rounded-[10px] border border-[#E0E0E0] bg-white px-4 py-3 text-left hover:border-[#0066CC]"
            >
              <div>
                <div className="text-[14px] font-medium text-[#1D1D1F]">
                  <span className="mr-2 font-mono text-[#0066CC]">
                    {sec.section_number}
                  </span>
                  {sec.title}
                </div>
                <div className="mt-0.5 text-[12px] text-[#6E6E73]">
                  {sec.tables?.length ?? 0} table(s) ·{" "}
                  {sec.placeholders?.length ?? 0} figure(s)
                </div>
              </div>
            </button>
          ))}
        </div>
      </SlideOverDrawer>

      {/* QA Numeric Cross-Check Audit Drawer */}
      <SlideOverDrawer
        open={activeDrawer === "qa_log"}
        onClose={() => setActiveDrawer("none")}
        title="QA Numeric Cross-Check Log"
        subtitle="Spreadsheet vs. narrative audit"
        dark
      >
        <div className="space-y-3">
          {(project.qa_alerts || []).length === 0 ? (
            <div className="rounded-[12px] border border-[#272D3D] bg-[#11141C] p-4 text-[13.5px] text-[#A3A9B8]">
              All numbers, depths, and coordinates match uploaded raw intake files. Zero banned AI clichés detected.
            </div>
          ) : (
            (project.qa_alerts || []).map((al) => (
              <div
                key={al.id}
                className="rounded-[12px] border border-[#272D3D] bg-[#11141C] p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[13.5px] font-medium text-[#EEF0F5]">
                    {al.field_label}
                  </span>
                  <span
                    className={`rounded-[6px] px-2 py-0.5 text-[12px] font-medium ${
                      al.is_resolved
                        ? "bg-[#F2FAF5] text-[#16A34A]"
                        : "bg-[#FFF9EB] text-[#945800]"
                    }`}
                  >
                    {al.is_resolved ? "Verified" : "Mismatch"}
                  </span>
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed text-[#A3A9B8]">
                  {al.message}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 rounded-[8px] bg-[#0B0D14] p-3 font-mono text-[12px]">
                  <div>
                    <div className="text-[11px] text-[#7A8296]">Raw source</div>
                    <div className="text-[#4CC38A]">{al.source_value}</div>
                  </div>
                  <div>
                    <div className="text-[11px] text-[#7A8296]">Draft text</div>
                    <div className="text-[#F5D07E]">{al.draft_value}</div>
                  </div>
                </div>
                {!al.is_resolved ? (
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => void handleResolveQaAlert(al.id, true)}
                      className="cupertino-press h-8 rounded-[7px] bg-[#0066CC] px-3 text-[12.5px] font-medium text-white"
                    >
                      Auto-fix to {al.source_value}
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleResolveQaAlert(al.id, false)}
                      className="cupertino-press h-8 rounded-[7px] border border-[#272D3D] px-3 text-[12.5px] text-[#A3A9B8]"
                    >
                      Dismiss
                    </button>
                  </div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </SlideOverDrawer>

      {/* External PDF Attachments & Merger Modal */}
      <AttachmentsModal
        open={attachmentsModalOpen}
        onOpenChange={setAttachmentsModalOpen}
        projectId={project.id}
        attachments={project.attachments || []}
        onUpdated={() =>
          void queryClient.invalidateQueries({ queryKey: ["project", projectId] })
        }
        onRecompilePdf={() => {
          if (layoutMode !== "editor_pdf") {
            setCanvasMode("preview");
          }
          void handleRefreshPdf();
        }}
      />
    </div>
  );
}
