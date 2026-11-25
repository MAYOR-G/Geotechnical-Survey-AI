"use client";

import * as React from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Highlight from "@tiptap/extension-highlight";
import Placeholder from "@tiptap/extension-placeholder";
import {
  AlertTriangle,
  BarChart3,
  Camera,
  Check,
  ExternalLink,
  Globe,
  ImagePlus,
  Loader2,
  PenLine,
  Plus,
  Search,
  Sparkles,
  Upload,
  Wand2,
  X,
} from "lucide-react";
import { apiClient, resolveBackendUrl } from "@/lib/api-client";
import { useStudioStore } from "@/stores/useStudioStore";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type {
  DocumentAst,
  EngineeringTableData,
  Project,
  ReportSectionBlock,
} from "@/types/project";
import type { ExternalImageCandidate, GalleryAsset } from "@/types/vault";

interface SectionTipTapEditorProps {
  section: ReportSectionBlock;
  onUpdateHtml: (html: string) => void;
  onSelectText: (selectedText: string, sectionId: string) => void;
}

function SectionTipTapEditor({
  section,
  onUpdateHtml,
  onSelectText,
}: SectionTipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Highlight,
      Placeholder.configure({
        placeholder: "Write technical geotechnical engineering narrative...",
      }),
    ],
    content: section.html_content,
    immediatelyRender: false,
    onUpdate: ({ editor: ed }) => {
      onUpdateHtml(ed.getHTML());
    },
    onSelectionUpdate: ({ editor: ed }) => {
      const { from, to } = ed.state.selection;
      if (to > from) {
        const selected = ed.state.doc.textBetween(from, to, " ");
        if (selected.trim().length > 4) {
          onSelectText(selected.trim(), section.id);
        }
      }
    },
  });

  React.useEffect(() => {
    if (editor && editor.getHTML() !== section.html_content) {
      editor.commands.setContent(section.html_content, false);
    }
  }, [editor, section.html_content]);

  return (
    <div className="w-full">
      <EditorContent editor={editor} />
    </div>
  );
}

interface RichDocumentEditorProps {
  project: Project;
  galleryAssets: GalleryAsset[];
  onSaveAst: (nextAst: DocumentAst) => void;
  onProjectUpdated?: (updatedProject: Project) => void;
  onResolveQaAlert: (alertId: string, applyFix: boolean) => Promise<void>;
  onRefreshGallery: () => void;
  hideQuickJumpBar?: boolean;
}

const SECTION_EXPANSION_PRESETS = [
  "Expand this section with deeper borehole correlation and add a full summary table",
  "Add a detailed analysis comparing hydraulic fracture Option A vs Option B (Delft cavity expansion)",
  "Enforce Vault Author Style & Anti-AI Humanize with exact geotechnical field cadence",
  "Expand laboratory derivation with BS 1377:1990 & Eurocode 7 EN 1997-2 engineering interpretation",
];

const SCIENTIFIC_CHART_TYPES = [
  { id: "casagrande", label: "Casagrande Plasticity Chart (A-Line & U-Line)" },
  { id: "moisture_density", label: "Moisture Content & Bulk Unit Weight vs. Depth" },
  { id: "shear_strength", label: "Direct Shear Box & Triaxial Shear Strength vs. Depth" },
  { id: "long_section", label: "Interpreted Geological Long-Section & Bore Path" },
  { id: "geohazard", label: "Geohazard Exposure & Residual Risk Matrix" },
];

export function RichDocumentEditor({
  project,
  galleryAssets,
  onSaveAst,
  onProjectUpdated,
  onResolveQaAlert,
  onRefreshGallery,
  hideQuickJumpBar = false,
}: RichDocumentEditorProps) {
  const { placeholderModalTarget, setPlaceholderModalTarget } = useStudioStore();
  const ast = project.document_ast_json;
  const sections = ast.sections || [];

  const [editorError, setEditorError] = React.useState("");
  const [selectedText, setSelectedText] = React.useState("");
  const [selectedSectionId, setSelectedSectionId] = React.useState("");
  const [aiInstruction, setAiInstruction] = React.useState("");
  const [aiLoading, setAiLoading] = React.useState(false);
  const [aiPreview, setAiPreview] = React.useState<{
    original: string;
    revised: string;
    notes: string;
    sectionId: string;
  } | null>(null);

  // Per-section AI expansion & scientific chart generation state
  const [activeExpandSectionId, setActiveExpandSectionId] = React.useState<string | null>(
    null,
  );
  const [expandPrompt, setExpandPrompt] = React.useState("");
  const [expandingSectionId, setExpandingSectionId] = React.useState<string | null>(
    null,
  );
  const [generatingChartSecId, setGeneratingChartSecId] = React.useState<string | null>(
    null,
  );

  // Tri-Source Figure Picker state (Vault Gallery + External Web Search + Local Upload)
  const [galleryTab, setGalleryTab] = React.useState<"gallery" | "web" | "upload">("gallery");
  const [webQuery, setWebQuery] = React.useState("");
  const [webResults, setWebResults] = React.useState<ExternalImageCandidate[]>([]);
  const [searchingWebImages, setSearchingWebImages] = React.useState(false);
  const [cachingImageUrl, setCachingImageUrl] = React.useState<string | null>(null);
  const [modalError, setModalError] = React.useState("");

  const [uploadTitle, setUploadTitle] = React.useState("");
  const [uploadCaption, setUploadCaption] = React.useState("");
  const [uploadingPhoto, setUploadingPhoto] = React.useState(false);
  const photoInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (placeholderModalTarget) {
      setWebQuery(placeholderModalTarget.prompt || project.title);
      setModalError("");
    }
  }, [placeholderModalTarget, project.title]);

  const openAlerts = (project.qa_alerts || []).filter((a) => !a.is_resolved);

  const updateFrontMatterField = (
    field: "report_title" | "report_subtitle" | "program_title" | "location_line" | "campaign_dates",
    value: string,
  ) => {
    onSaveAst({
      ...ast,
      [field]: value,
    });
  };

  const updateSectionHtml = (sectionId: string, html: string) => {
    const nextSections = sections.map((s) =>
      s.id === sectionId ? { ...s, html_content: html } : s,
    );
    onSaveAst({ ...ast, sections: nextSections });
  };

  const updateTableCell = (
    sectionId: string,
    tableId: string,
    rowIdx: number,
    colIdx: number,
    value: string,
  ) => {
    const nextSections = sections.map((sec) => {
      if (sec.id !== sectionId) return sec;
      const nextTables = (sec.tables || []).map((tbl) => {
        if (tbl.id !== tableId) return tbl;
        const nextRows = tbl.rows.map((r, rI) =>
          rI === rowIdx
            ? tbl.columns.map((_, cI) => (cI === colIdx ? value : (r[cI] ?? "")))
            : r,
        );
        return { ...tbl, rows: nextRows };
      });
      return { ...sec, tables: nextTables };
    });
    onSaveAst({ ...ast, sections: nextSections });
  };

  const addTableRow = (sectionId: string, tbl: EngineeringTableData) => {
    const emptyRow = tbl.columns.map(() => "");
    const nextSections = sections.map((sec) => {
      if (sec.id !== sectionId) return sec;
      return {
        ...sec,
        tables: (sec.tables || []).map((t) =>
          t.id === tbl.id ? { ...t, rows: [...t.rows, emptyRow] } : t,
        ),
      };
    });
    onSaveAst({ ...ast, sections: nextSections });
  };

  const runInlineAi = async (instruction: string) => {
    const targetText = selectedText.trim();
    if (!targetText || !selectedSectionId) return;
    setEditorError("");
    setAiLoading(true);
    try {
      const res = await apiClient.inlineEdit(project.id, {
        selection_text: targetText,
        instruction,
        section_context: selectedSectionId,
      });
      setAiPreview({
        original: targetText,
        revised: res.revised_text,
        notes: res.style_notes,
        sectionId: selectedSectionId,
      });
    } catch (err) {
      setEditorError(
        err instanceof Error ? err.message : "Inline AI revision failed.",
      );
    } finally {
      setAiLoading(false);
    }
  };

  const applyAiPreview = () => {
    if (!aiPreview) return;
    const sec = sections.find((s) => s.id === aiPreview.sectionId);
    if (sec) {
      const nextHtml = sec.html_content.includes(aiPreview.original)
        ? sec.html_content.replace(aiPreview.original, aiPreview.revised)
        : `${sec.html_content}<p>${aiPreview.revised}</p>`;
      updateSectionHtml(sec.id, nextHtml);
    }
    setAiPreview(null);
    setSelectedText("");
    setAiInstruction("");
  };

  const handleExpandSection = async (sectionId: string, instruction: string) => {
    const cleanInst = instruction.trim();
    if (!cleanInst) return;
    setEditorError("");
    setExpandingSectionId(sectionId);
    try {
      const res = await apiClient.expandSection(project.id, sectionId, cleanInst);
      if (onProjectUpdated && res.project) {
        onProjectUpdated(res.project);
      } else if (res.project) {
        onSaveAst(res.project.document_ast_json);
      }
      setExpandPrompt("");
      setActiveExpandSectionId(null);
    } catch (err) {
      setEditorError(
        err instanceof Error ? err.message : "Section expansion failed.",
      );
    } finally {
      setExpandingSectionId(null);
    }
  };

  const handleGenerateChart = async (sectionId: string, chartType: string) => {
    setEditorError("");
    setGeneratingChartSecId(sectionId);
    try {
      const res = await apiClient.generateSectionChart(project.id, sectionId, chartType);
      if (onProjectUpdated && res.project) {
        onProjectUpdated(res.project);
      } else if (res.project) {
        onSaveAst(res.project.document_ast_json);
      }
      onRefreshGallery();
    } catch (err) {
      setEditorError(
        err instanceof Error ? err.message : "Chart generation failed.",
      );
    } finally {
      setGeneratingChartSecId(null);
    }
  };

  const assignPlaceholderAsset = (asset: GalleryAsset) => {
    if (!placeholderModalTarget) return;
    const { sectionId, placeholderId, figureNumber } = placeholderModalTarget;
    const nextSections = sections.map((sec) => {
      if (sec.id !== sectionId) return sec;
      return {
        ...sec,
        placeholders: (sec.placeholders || []).map((ph) =>
          ph.id === placeholderId
            ? {
              ...ph,
              resolved_asset_id: asset.id,
              resolved_url: asset.file_url,
              caption: asset.default_caption.startsWith("Figure")
                ? asset.default_caption
                : `${figureNumber}: ${asset.default_caption}`,
            }
            : ph,
        ),
      };
    });
    onSaveAst({ ...ast, sections: nextSections });
    setPlaceholderModalTarget(null);
  };

  const handleSearchWebImages = async (explicitQuery?: string) => {
    const q = (explicitQuery ?? webQuery).trim();
    if (!q) return;
    setModalError("");
    setSearchingWebImages(true);
    try {
      const results = await apiClient.searchExternalImages(q, 8);
      setWebResults(results);
      if (results.length === 0) {
        setModalError("No technical images matched that query. Try broader regional or equipment keywords.");
      }
    } catch (err) {
      setModalError(
        err instanceof Error ? err.message : "External image search failed.",
      );
    } finally {
      setSearchingWebImages(false);
    }
  };

  const handleSelectExternalImage = async (candidate: ExternalImageCandidate) => {
    if (!placeholderModalTarget) return;
    setModalError("");
    setCachingImageUrl(candidate.image_url);
    try {
      const cachedAsset = await apiClient.cacheExternalImage({
        image_url: candidate.image_url,
        title: candidate.title || placeholderModalTarget.prompt,
        caption: candidate.description || candidate.title || placeholderModalTarget.prompt,
        category: "map",
        source_url: candidate.source_url,
      });
      onRefreshGallery();
      assignPlaceholderAsset(cachedAsset);
    } catch (err) {
      setModalError(
        err instanceof Error
          ? err.message
          : "Could not download and cache external image. Please pick another candidate.",
      );
    } finally {
      setCachingImageUrl(null);
    }
  };

  const handleUploadNewPhoto = async (files: FileList | null) => {
    if (!files || !files[0] || !placeholderModalTarget) return;
    setModalError("");
    setUploadingPhoto(true);
    try {
      const asset = await apiClient.uploadGalleryAsset(
        files[0],
        uploadTitle || files[0].name,
        uploadCaption || placeholderModalTarget.prompt,
        "field_photo",
        ["field", project.client_name].filter(Boolean),
      );
      onRefreshGallery();
      assignPlaceholderAsset(asset);
    } catch (err) {
      setModalError(
        err instanceof Error ? err.message : "Failed to upload field photograph.",
      );
    } finally {
      setUploadingPhoto(false);
    }
  };

  return (
    <div className="flex h-full flex-col bg-white">
      {!hideQuickJumpBar ? (
        <div className="flex shrink-0 items-center gap-1.5 overflow-x-auto border-b border-[#E0E0E0] bg-[#F5F5F7] px-5 py-1.5">
          <button
            type="button"
            onClick={() => {
              document
                .getElementById("sec-cover-front-matter")
                ?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            className="cupertino-press inline-flex h-7 shrink-0 items-center gap-1.5 rounded-[7px] border border-[#E0E0E0] bg-white px-2.5 text-[12px] font-medium text-[#333333] hover:border-[#0066CC] hover:text-[#1D1D1F]"
          >
            <span className="font-mono text-[#0066CC]">Cover</span>
            <span>Front Matter</span>
          </button>
          {sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => {
                document
                  .getElementById(sec.id)
                  ?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
              className="cupertino-press inline-flex h-7 shrink-0 items-center gap-1.5 rounded-[7px] border border-[#E0E0E0] bg-white px-2.5 text-[12px] font-medium text-[#333333] hover:border-[#0066CC] hover:text-[#1D1D1F]"
            >
              <span className="font-mono text-[#0066CC]">{sec.section_number}</span>
              <span className="max-w-[150px] truncate">{sec.title}</span>
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex-1 overflow-y-auto px-6 py-4 sm:px-8">
        {editorError ? (
          <div className="mx-auto mb-5 flex max-w-[1040px] items-center justify-between gap-3 rounded-[10px] border border-[#FECACA] bg-[#FEF2F2] px-4 py-2.5 text-[13px] text-[#DC2626]">
            <span>{editorError}</span>
            <button
              type="button"
              onClick={() => setEditorError("")}
              className="rounded p-1 hover:bg-[#FEE2E2]"
              aria-label="Dismiss error"
            >
              <X className="size-4" />
            </button>
          </div>
        ) : null}

        {/* Floating Highlight-to-Prompt AI Bar */}
        {selectedText ? (
          <div className="sticky top-0 z-30 mx-auto mb-6 max-w-[1040px] rounded-[12px] border border-[#272D3D] bg-[#0B0D14] p-3.5 text-white">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2.5">
              <div className="flex items-center gap-2 text-[13px] font-medium text-[#EEF0F5]">
                <PenLine className="size-4 text-[#2997FF]" strokeWidth={1.5} />
                <span>Revise or expand highlighted passage</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {["Humanize", "Match Vault style", "Expand analysis", "Verify numbers"].map(
                  (chip) => (
                    <button
                      key={chip}
                      type="button"
                      disabled={aiLoading}
                      onClick={() => void runInlineAi(chip)}
                      className="cupertino-press h-7 rounded-[6px] bg-white/10 px-2.5 text-[12px] text-[#EEF0F5] hover:bg-[#0066CC]"
                    >
                      {chip}
                    </button>
                  ),
                )}
                <button
                  type="button"
                  onClick={() => {
                    setSelectedText("");
                    setAiPreview(null);
                  }}
                  className="ml-1 rounded-[6px] p-1 text-[#A3A9B8] hover:bg-white/10 hover:text-white"
                  aria-label="Close inline editor"
                >
                  <X className="size-4" />
                </button>
              </div>
            </div>

            <div className="mt-2.5 flex items-center gap-2">
              <input
                type="text"
                value={aiInstruction}
                onChange={(e) => setAiInstruction(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && aiInstruction.trim()) {
                    void runInlineAi(aiInstruction);
                  }
                }}
                placeholder="Enter rewrite instruction (e.g., Expand borehole correlation with exact depths)"
                className="h-9 flex-1 rounded-[8px] border border-white/15 bg-[#11141C] px-3 text-[13.5px] text-white placeholder:text-[#7A8296] focus:border-[#2997FF] focus:outline-none"
              />
              <button
                type="button"
                disabled={aiLoading || !aiInstruction.trim()}
                onClick={() => void runInlineAi(aiInstruction)}
                className="cupertino-press inline-flex h-9 items-center gap-1.5 rounded-[8px] bg-[#0066CC] px-4 text-[13px] font-medium text-white hover:bg-[#0055B3] disabled:opacity-50"
              >
                {aiLoading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Wand2 className="size-4" strokeWidth={1.5} />
                )}
                <span>Apply</span>
              </button>
            </div>

            {aiPreview ? (
              <div className="mt-3 rounded-[10px] border border-white/10 bg-[#11141C] p-3.5 text-[13.5px]">
                <div className="text-[12px] font-medium text-[#2997FF]">
                  Proposed revision · {aiPreview.notes}
                </div>
                <p className="mt-1.5 leading-relaxed text-[#EEF0F5]">
                  {aiPreview.revised}
                </p>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={applyAiPreview}
                    className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-[7px] bg-[#0066CC] px-3 text-[12.5px] font-medium text-white"
                  >
                    <Check className="size-3.5" />
                    <span>Accept change</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setAiPreview(null)}
                    className="cupertino-press h-8 rounded-[7px] border border-white/15 px-3 text-[12.5px] text-[#A3A9B8]"
                  >
                    Discard
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        {/* Code-Free Cover & Front Matter Block Editor */}
        <div className="mx-auto max-w-[1040px]">
          <section
            id="sec-cover-front-matter"
            className="rounded-[14px] border border-[#E0E0E0] bg-[#F5F5F7] p-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E0E0E0] pb-3">
              <div className="flex items-center gap-2">
                <span className="rounded-[6px] border border-[#B8D9FF] bg-[#F0F7FF] px-2.5 py-0.5 font-mono text-[12px] font-medium text-[#0066CC]">
                  Cover &amp; Front Matter
                </span>
                <span className="font-mono text-[12px] text-[#6E6E73]">
                  {project.contractor_ref_code || project.id} · Rev {project.revision_number}
                </span>
              </div>
              <span className="text-[12px] text-[#6E6E73]">
                Synchronized directly with Typst A4 Cover Page &amp; Word Header
              </span>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="mb-1 block text-[12px] font-semibold text-[#1D1D1F]">
                  Report Title
                </label>
                <input
                  type="text"
                  value={ast.report_title || project.title}
                  onChange={(e) => updateFrontMatterField("report_title", e.target.value)}
                  className="h-9 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] font-medium text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-[12px] font-semibold text-[#1D1D1F]">
                  Program / Campaign Banner
                </label>
                <input
                  type="text"
                  value={ast.program_title || ""}
                  onChange={(e) => updateFrontMatterField("program_title", e.target.value)}
                  placeholder="e.g., OFFSHORE PIPELINE CROSSING – GEOTECHNICAL INVESTIGATION"
                  className="h-9 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-[12px] font-semibold text-[#1D1D1F]">
                  Report Subtitle / Deliverable Type
                </label>
                <input
                  type="text"
                  value={ast.report_subtitle || project.subtitle || ""}
                  onChange={(e) => updateFrontMatterField("report_subtitle", e.target.value)}
                  placeholder="e.g., GEOTECHNICAL LABORATORY INVESTIGATIONS — FINAL REPORT"
                  className="h-9 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                />
              </div>
            </div>
          </section>

          {/* Sections */}
          <div className="mt-8 space-y-10">
            {sections.map((sec) => {
              const sectionAlerts = openAlerts.filter(
                (a) => a.section_id === sec.id,
              );
              const isExpandOpen = activeExpandSectionId === sec.id;
              const isExpanding = expandingSectionId === sec.id;
              const isGeneratingChart = generatingChartSecId === sec.id;

              return (
                <section
                  key={sec.id}
                  id={sec.id}
                  className="scroll-mt-14 border-b border-[#E0E0E0] pb-8 last:border-b-0"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="text-[19px] font-medium tracking-[-0.015em] text-[#1D1D1F]">
                      <span className="mr-2 font-mono text-[#0066CC]">
                        {sec.section_number}
                      </span>
                      {sec.title}
                    </h2>

                    <div className="flex flex-wrap items-center gap-2">
                      {/* Generate Scientific Matplotlib Chart Dropdown */}
                      <div className="relative inline-flex items-center">
                        <BarChart3 className="pointer-events-none absolute left-2.5 size-3.5 text-[#0066CC]" strokeWidth={1.6} />
                        <select
                          aria-label="Generate scientific chart for section"
                          value=""
                          disabled={isGeneratingChart}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (val) void handleGenerateChart(sec.id, val);
                          }}
                          className="h-8 cursor-pointer rounded-[7px] border border-[#E0E0E0] bg-white pl-8 pr-3 text-[12px] font-medium text-[#1D1D1F] hover:border-[#0066CC] focus:outline-none disabled:opacity-50"
                        >
                          <option value="">
                            {isGeneratingChart ? "Plotting chart..." : "+ Scientific Chart"}
                          </option>
                          {SCIENTIFIC_CHART_TYPES.map((ct) => (
                            <option key={ct.id} value={ct.id}>
                              {ct.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          setActiveExpandSectionId(isExpandOpen ? null : sec.id)
                        }
                        className={`cupertino-press inline-flex h-8 items-center gap-1.5 rounded-[7px] border px-3 text-[12.5px] font-medium transition-colors ${isExpandOpen
                          ? "border-[#0066CC] bg-[#0066CC] text-white"
                          : "border-[#B8D9FF] bg-[#F0F7FF] text-[#0066CC] hover:bg-[#E0EFFF]"
                          }`}
                      >
                        <Sparkles className="size-3.5" strokeWidth={1.6} />
                        <span>Expand / Refine with AI</span>
                      </button>
                    </div>
                  </div>

                  {/* Page / Section-Level AI Expansion Panel */}
                  {isExpandOpen ? (
                    <div className="mt-3.5 rounded-[12px] border border-[#B8D9FF] bg-[#F0F7FF]/70 p-4">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[13px] font-semibold text-[#1D1D1F]">
                          Senior Geotechnical Section Expansion &amp; Typst Re-Typesetting
                        </span>
                        <button
                          type="button"
                          onClick={() => setActiveExpandSectionId(null)}
                          className="rounded-[6px] p-1 text-[#6E6E73] hover:bg-white"
                        >
                          <X className="size-3.5" />
                        </button>
                      </div>

                      <div className="mt-2.5 flex flex-wrap gap-1.5">
                        {SECTION_EXPANSION_PRESETS.map((preset) => (
                          <button
                            key={preset}
                            type="button"
                            disabled={isExpanding}
                            onClick={() => void handleExpandSection(sec.id, preset)}
                            className="cupertino-press rounded-full border border-[#B8D9FF] bg-white px-3 py-1 text-[11.5px] font-medium text-[#1D1D1F] hover:border-[#0066CC] hover:text-[#0066CC] disabled:opacity-50"
                          >
                            {preset}
                          </button>
                        ))}
                      </div>

                      <div className="mt-3 flex items-center gap-2">
                        <input
                          type="text"
                          value={expandPrompt}
                          onChange={(e) => setExpandPrompt(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && expandPrompt.trim()) {
                              void handleExpandSection(sec.id, expandPrompt);
                            }
                          }}
                          placeholder="Tell the AI how to expand or refine this section (e.g., Add a full summary table of BH1–BH10 stratigraphy)..."
                          className="h-9 flex-1 rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] text-[#1D1D1F] placeholder:text-[#6E6E73] focus:border-[#0066CC] focus:outline-none"
                        />
                        <Button
                          size="sm"
                          disabled={isExpanding || !expandPrompt.trim()}
                          onClick={() => void handleExpandSection(sec.id, expandPrompt)}
                        >
                          {isExpanding ? (
                            <Loader2 className="size-3.5 animate-spin" />
                          ) : (
                            <Wand2 className="size-3.5" strokeWidth={1.6} />
                          )}
                          <span>{isExpanding ? "Expanding & Compiling..." : "Expand & Compile PDF"}</span>
                        </Button>
                      </div>
                    </div>
                  ) : null}

                  {sectionAlerts.map((al) => (
                    <div
                      key={al.id}
                      className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-[10px] border border-[#F5D07E] bg-[#FFF9EB] px-4 py-3"
                    >
                      <div className="flex items-start gap-2.5 text-[13.5px] text-[#945800]">
                        <AlertTriangle className="mt-0.5 size-4 shrink-0" strokeWidth={1.6} />
                        <div>
                          <span className="font-medium text-[#1D1D1F]">
                            {al.field_label}:
                          </span>{" "}
                          {al.message}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => void onResolveQaAlert(al.id, true)}
                        className="cupertino-press h-8 rounded-[7px] bg-[#1D1D1F] px-3 text-[12.5px] font-medium text-white hover:opacity-90"
                      >
                        Fix to {al.source_value}
                      </button>
                    </div>
                  ))}

                  <div className="mt-4">
                    <SectionTipTapEditor
                      section={sec}
                      onUpdateHtml={(html) => updateSectionHtml(sec.id, html)}
                      onSelectText={(sel, sId) => {
                        setSelectedText(sel);
                        setSelectedSectionId(sId);
                      }}
                    />
                  </div>

                  {(sec.tables || []).map((tbl) => (
                    <div key={tbl.id} className="mt-6">
                      <div className="mb-2.5 flex items-center justify-between gap-2">
                        <h3 className="text-[14.5px] font-medium text-[#1D1D1F]">
                          {tbl.table_number ? `${tbl.table_number}: ` : ""}
                          {tbl.title}
                        </h3>
                        <button
                          type="button"
                          onClick={() => addTableRow(sec.id, tbl)}
                          className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-[7px] border border-[#E0E0E0] bg-white px-3 text-[12.5px] font-medium text-[#333333] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"
                        >
                          <Plus className="size-3.5" strokeWidth={1.5} />
                          <span>Add row</span>
                        </button>
                      </div>
                      <div className="engineering-table-wrap">
                        <table className="engineering-table">
                          <thead>
                            {tbl.multi_header && tbl.multi_header.length > 0 ? (
                              tbl.multi_header.map((headerRow, hIdx) => (
                                <tr key={hIdx}>
                                  {headerRow.map((cell, cIdx) => (
                                    <th
                                      key={cIdx}
                                      colSpan={cell.colspan}
                                      rowSpan={cell.rowspan}
                                      className="text-center"
                                    >
                                      {cell.label}
                                    </th>
                                  ))}
                                </tr>
                              ))
                            ) : (
                              <tr>
                                {tbl.columns.map((col, cIdx) => (
                                  <th key={cIdx}>{col}</th>
                                ))}
                              </tr>
                            )}
                          </thead>
                          <tbody>
                            {tbl.rows.map((row, rIdx) => (
                              <tr key={rIdx}>
                                {tbl.columns.map((_, cIdx) => (
                                  <td key={cIdx} className="p-0">
                                    <input
                                      type="text"
                                      value={String(row[cIdx] ?? "")}
                                      onChange={(e) =>
                                        updateTableCell(
                                          sec.id,
                                          tbl.id,
                                          rIdx,
                                          cIdx,
                                          e.target.value,
                                        )
                                      }
                                      className="w-full min-w-[92px] border-0 bg-transparent px-3 py-2 font-mono text-[12.5px] tabular-nums text-[#1D1D1F] focus:bg-[#F0F7FF] focus:outline-none"
                                    />
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {tbl.footnote ? (
                        <p className="mt-1.5 text-[12px] italic text-[#6E6E73]">{tbl.footnote}</p>
                      ) : null}
                    </div>
                  ))}

                  {(sec.placeholders || []).map((ph) => (
                    <div key={ph.id} className="mt-6">
                      {ph.resolved_url ? (
                        <div className="group rounded-[12px] border border-[#E0E0E0] bg-[#F5F5F7] p-4">
                          <div className="flex flex-col items-center">
                            {ph.secondary_url && ph.layout === "side_by_side" ? (
                              <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveBackendUrl(ph.resolved_url)}
                                  alt={ph.caption || ph.prompt}
                                  className="max-h-[340px] w-full object-contain"
                                />
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveBackendUrl(ph.secondary_url)}
                                  alt={ph.secondary_caption || ph.caption || ph.prompt}
                                  className="max-h-[340px] w-full object-contain"
                                />
                              </div>
                            ) : ph.secondary_url && ph.layout === "stacked" ? (
                              <div className="w-full space-y-2.5 text-center">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveBackendUrl(ph.resolved_url)}
                                  alt={ph.caption || ph.prompt}
                                  className="mx-auto max-h-[320px] w-full object-contain"
                                />
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={resolveBackendUrl(ph.secondary_url)}
                                  alt={ph.caption || ph.prompt}
                                  className="mx-auto max-h-[320px] w-full object-contain"
                                />
                              </div>
                            ) : (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img
                                src={resolveBackendUrl(ph.resolved_url)}
                                alt={ph.caption || ph.prompt}
                                className="max-h-[420px] w-full object-contain"
                              />
                            )}
                            <p className="mt-2.5 text-center text-[13.5px] font-medium text-[#1D1D1F]">
                              {ph.secondary_caption
                                ? `${ph.caption || ph.prompt} · ${ph.secondary_caption}`
                                : ph.caption || `${ph.figure_number}: ${ph.prompt}`}
                            </p>
                            <div className="mt-2.5 flex flex-wrap items-center justify-center gap-2">
                              <Button
                                variant="secondary-pill"
                                size="sm"
                                onClick={() => {
                                  setGalleryTab("gallery");
                                  setPlaceholderModalTarget({
                                    sectionId: sec.id,
                                    placeholderId: ph.id,
                                    figureNumber: ph.figure_number,
                                    prompt: ph.prompt,
                                  });
                                }}
                              >
                                <ImagePlus className="size-3.5" strokeWidth={1.5} />
                                <span>Swap from Vault</span>
                              </Button>
                              <Button
                                variant="secondary-pill"
                                size="sm"
                                onClick={() => {
                                  setGalleryTab("web");
                                  setPlaceholderModalTarget({
                                    sectionId: sec.id,
                                    placeholderId: ph.id,
                                    figureNumber: ph.figure_number,
                                    prompt: ph.prompt,
                                  });
                                  void handleSearchWebImages(ph.prompt);
                                }}
                              >
                                <Globe className="size-3.5" strokeWidth={1.5} />
                                <span>Search External Web</span>
                              </Button>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-[12px] border-[1.5px] border-dashed border-[#0066CC] bg-[#F5F5F7] p-5">
                          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
                            <div className="flex items-start gap-3">
                              <div className="flex size-10 shrink-0 items-center justify-center rounded-[9px] border border-[#B8D9FF] bg-white text-[#0066CC]">
                                <Camera className="size-5" strokeWidth={1.5} />
                              </div>
                              <div>
                                <span className="font-mono text-[12px] font-medium text-[#0066CC]">
                                  {ph.figure_number} · Figure slot
                                </span>
                                <p className="mt-0.5 text-[14px] font-medium text-[#1D1D1F]">
                                  {ph.prompt}
                                </p>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-2">
                              <Button
                                size="sm"
                                onClick={() => {
                                  setGalleryTab("gallery");
                                  setPlaceholderModalTarget({
                                    sectionId: sec.id,
                                    placeholderId: ph.id,
                                    figureNumber: ph.figure_number,
                                    prompt: ph.prompt,
                                  });
                                }}
                              >
                                <ImagePlus className="size-4" strokeWidth={1.5} />
                                <span>Vault Gallery</span>
                              </Button>
                              <Button
                                variant="secondary-pill"
                                size="sm"
                                onClick={() => {
                                  setGalleryTab("web");
                                  setPlaceholderModalTarget({
                                    sectionId: sec.id,
                                    placeholderId: ph.id,
                                    figureNumber: ph.figure_number,
                                    prompt: ph.prompt,
                                  });
                                  void handleSearchWebImages(ph.prompt);
                                }}
                              >
                                <Globe className="size-4" strokeWidth={1.5} />
                                <span>Search Web</span>
                              </Button>
                              <Button
                                variant="secondary-pill"
                                size="sm"
                                onClick={() => {
                                  setGalleryTab("upload");
                                  setPlaceholderModalTarget({
                                    sectionId: sec.id,
                                    placeholderId: ph.id,
                                    figureNumber: ph.figure_number,
                                    prompt: ph.prompt,
                                  });
                                }}
                              >
                                <Upload className="size-4" strokeWidth={1.5} />
                                <span>Upload Photo</span>
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tri-Source Smart Image Placeholder Picker Modal */}
      <Modal
        open={Boolean(placeholderModalTarget)}
        onOpenChange={(open) => {
          if (!open) setPlaceholderModalTarget(null);
        }}
        title={
          placeholderModalTarget
            ? `Insert ${placeholderModalTarget.figureNumber}`
            : "Insert figure"
        }
        description={placeholderModalTarget?.prompt}
        maxWidthClass="max-w-[820px]"
      >
        <div className="mb-4 flex flex-wrap items-center gap-2 border-b border-[#E0E0E0] pb-3">
          <button
            type="button"
            onClick={() => setGalleryTab("gallery")}
            className={`h-9 rounded-[8px] px-3.5 text-[13px] font-medium transition-colors ${galleryTab === "gallery"
              ? "bg-[#1D1D1F] text-white"
              : "bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
          >
            Vault &amp; Charts ({galleryAssets.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setGalleryTab("web");
              if (webResults.length === 0 && (placeholderModalTarget?.prompt || webQuery)) {
                void handleSearchWebImages(webQuery || placeholderModalTarget?.prompt);
              }
            }}
            className={`inline-flex h-9 items-center gap-1.5 rounded-[8px] px-3.5 text-[13px] font-medium transition-colors ${galleryTab === "web"
              ? "bg-[#1D1D1F] text-white"
              : "bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
          >
            <Globe className="size-3.5" strokeWidth={1.6} />
            <span>Search External Web</span>
          </button>
          <button
            type="button"
            onClick={() => setGalleryTab("upload")}
            className={`h-9 rounded-[8px] px-3.5 text-[13px] font-medium transition-colors ${galleryTab === "upload"
              ? "bg-[#1D1D1F] text-white"
              : "bg-[#F5F5F7] text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
          >
            Upload Photo
          </button>
        </div>

        {modalError ? (
          <div className="mb-4 rounded-[10px] border border-[#FECACA] bg-[#FEF2F2] px-3.5 py-2.5 text-[13px] text-[#DC2626]">
            {modalError}
          </div>
        ) : null}

        {galleryTab === "gallery" ? (
          galleryAssets.length === 0 ? (
            <div className="rounded-[12px] border border-[#E0E0E0] bg-[#F5F5F7] p-8 text-center">
              <p className="text-[14px] font-medium text-[#1D1D1F]">
                No Vault visuals indexed yet
              </p>
              <p className="mt-1 text-[13px] text-[#6E6E73]">
                Switch to Search External Web to find regional geological maps and survey vessels, or upload a field photo.
              </p>
            </div>
          ) : (
            <div className="grid max-h-[60vh] grid-cols-1 gap-4 overflow-y-auto sm:grid-cols-2">
              {galleryAssets.map((asset) => (
                <button
                  key={asset.id}
                  type="button"
                  onClick={() => assignPlaceholderAsset(asset)}
                  className="group flex flex-col overflow-hidden rounded-[12px] border border-[#E0E0E0] bg-white text-left transition-colors hover:border-[#0066CC]"
                >
                  <div className="h-[156px] w-full bg-[#F5F5F7] p-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={resolveBackendUrl(asset.file_url)}
                      alt={asset.title}
                      className="h-full w-full rounded-[6px] object-contain"
                    />
                  </div>
                  <div className="p-3.5">
                    <div className="text-[13.5px] font-medium text-[#1D1D1F] group-hover:text-[#0066CC]">
                      {asset.title}
                    </div>
                    <p className="mt-1 line-clamp-2 text-[12.5px] text-[#6E6E73]">
                      {asset.default_caption}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )
        ) : galleryTab === "web" ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[#6E6E73]" />
                <input
                  type="text"
                  value={webQuery}
                  onChange={(e) => setWebQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      void handleSearchWebImages();
                    }
                  }}
                  placeholder="Search regional geological maps, DP-2 vessels, HDD rigs, or basin diagrams..."
                  className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white pl-9 pr-3 text-[13.5px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                />
              </div>
              <Button
                size="sm"
                disabled={searchingWebImages || !webQuery.trim()}
                onClick={() => void handleSearchWebImages()}
              >
                {searchingWebImages ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Search className="size-4" strokeWidth={1.6} />
                )}
                <span>{searchingWebImages ? "Searching..." : "Search"}</span>
              </Button>
            </div>

            <p className="text-[12px] text-[#6E6E73]">
              Selected external images are downloaded, normalized to local RGB PNG/JPEG storage, and attributed so Typst PDF compilation never breaks on hotlinks.
            </p>

            {searchingWebImages ? (
              <div className="flex items-center justify-center gap-2.5 rounded-[12px] border border-[#E0E0E0] bg-[#F5F5F7] py-12 text-[13.5px] text-[#6E6E73]">
                <Loader2 className="size-4 animate-spin text-[#0066CC]" />
                <span>Searching live technical image sources...</span>
              </div>
            ) : (
              <div className="grid max-h-[52vh] grid-cols-1 gap-4 overflow-y-auto sm:grid-cols-2">
                {webResults.map((cand, idx) => {
                  const isCaching = cachingImageUrl === cand.image_url;
                  return (
                    <div
                      key={`${cand.image_url}-${idx}`}
                      className="flex flex-col justify-between overflow-hidden rounded-[12px] border border-[#E0E0E0] bg-white"
                    >
                      <div>
                        <div className="h-[156px] w-full bg-[#F5F5F7] p-2">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={cand.image_url}
                            alt={cand.title}
                            className="h-full w-full rounded-[6px] object-contain"
                          />
                        </div>
                        <div className="p-3.5">
                          <div className="line-clamp-1 text-[13.5px] font-medium text-[#1D1D1F]">
                            {cand.title}
                          </div>
                          <p className="mt-1 line-clamp-2 text-[12px] text-[#6E6E73]">
                            {cand.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between gap-2 border-t border-[#E0E0E0] bg-[#F5F5F7] px-3.5 py-2.5">
                        {cand.source_url ? (
                          <a
                            href={cand.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 truncate font-mono text-[11px] text-[#6E6E73] hover:text-[#0066CC]"
                          >
                            <span className="truncate">
                              {cand.source_domain || "source"}
                            </span>
                            <ExternalLink className="size-3 shrink-0" />
                          </a>
                        ) : (
                          <span className="font-mono text-[11px] text-[#6E6E73]">
                            Web figure
                          </span>
                        )}
                        <Button
                          size="sm"
                          disabled={cachingImageUrl !== null}
                          onClick={() => void handleSelectExternalImage(cand)}
                        >
                          {isCaching ? (
                            <Loader2 className="size-3.5 animate-spin" />
                          ) : (
                            <Check className="size-3.5" strokeWidth={1.6} />
                          )}
                          <span>{isCaching ? "Caching..." : "Cache & Insert"}</span>
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
                Photo title
              </label>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="e.g., DP-2 Survey Vessel Deck Configuration"
                className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
                Figure caption
              </label>
              <input
                type="text"
                value={uploadCaption}
                onChange={(e) => setUploadCaption(e.target.value)}
                placeholder={placeholderModalTarget?.prompt || "Figure caption"}
                className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
              />
            </div>
            <div
              onClick={() => photoInputRef.current?.click()}
              className="flex cursor-pointer flex-col items-center justify-center rounded-[12px] border border-dashed border-[#0066CC] bg-[#F5F5F7] p-8 text-center hover:bg-[#F0F7FF]"
            >
              <input
                ref={photoInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) => void handleUploadNewPhoto(e.target.files)}
                className="hidden"
              />
              {uploadingPhoto ? (
                <Loader2 className="size-6 animate-spin text-[#0066CC]" />
              ) : (
                <Upload className="size-6 text-[#0066CC]" strokeWidth={1.5} />
              )}
              <span className="mt-2 text-[14px] font-medium text-[#1D1D1F]">
                Select PNG or JPG field photograph to insert and save
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
