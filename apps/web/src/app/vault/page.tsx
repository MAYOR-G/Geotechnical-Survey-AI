"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  Check,
  Database,
  FileText,
  ImagePlus,
  Images,
  Loader2,
  Plus,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { apiClient, resolveBackendUrl } from "@/lib/api-client";
import { FrostedSubNav } from "@/components/layout/FrostedSubNav";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { OptionChip } from "@/components/ui/OptionChip";
import { UtilityCard } from "@/components/ui/UtilityCard";
import type { VaultDocument } from "@/types/vault";

export default function VaultPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState<"reports" | "style" | "gallery">("reports");
  const [inspectDoc, setInspectDoc] = React.useState<VaultDocument | null>(null);
  const [inspectTab, setInspectTab] = React.useState<"chunks" | "images" | "blueprint">(
    "chunks",
  );
  const [uploadingDoc, setUploadingDoc] = React.useState(false);
  const [isDraggingReport, setIsDraggingReport] = React.useState(false);
  const [docCategory, setDocCategory] = React.useState("field_report");

  const [galleryFilter, setGalleryFilter] = React.useState("all");
  const [uploadAssetOpen, setUploadAssetOpen] = React.useState(false);
  const [assetTitle, setAssetTitle] = React.useState("");
  const [assetCaption, setAssetCaption] = React.useState("");
  const [assetCategory, setAssetCategory] = React.useState("vessel");
  const [assetTags, setAssetTags] = React.useState("");
  const [uploadingAsset, setUploadingAsset] = React.useState(false);

  const [newBanned, setNewBanned] = React.useState("");
  const [newTerm, setNewTerm] = React.useState("");
  const [savingStyle, setSavingStyle] = React.useState(false);
  const [styleSaved, setStyleSaved] = React.useState(false);
  const [vaultError, setVaultError] = React.useState("");

  const reportFileRef = React.useRef<HTMLInputElement>(null);
  const assetFileRef = React.useRef<HTMLInputElement>(null);

  const { data: vaultDocs = [], isLoading: loadingDocs } = useQuery({
    queryKey: ["vault-documents"],
    queryFn: apiClient.listVaultDocuments,
  });

  const { data: gallery = [] } = useQuery({
    queryKey: ["gallery-assets"],
    queryFn: apiClient.listGalleryAssets,
  });

  const { data: settings } = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: apiClient.getSettings,
  });

  const [styleGuide, setStyleGuide] = React.useState(settings?.style_guide_json);

  React.useEffect(() => {
    if (settings?.style_guide_json) {
      setStyleGuide(settings.style_guide_json);
    }
  }, [settings]);

  const handleUploadVaultDoc = async (files: FileList | File[] | null) => {
    const fileList = files ? Array.from(files) : [];
    if (fileList.length === 0) return;
    setVaultError("");
    setUploadingDoc(true);
    try {
      for (const file of fileList) {
        await apiClient.uploadVaultDocument(file, docCategory);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["vault-documents"] }),
        queryClient.invalidateQueries({ queryKey: ["gallery-assets"] }),
        queryClient.invalidateQueries({ queryKey: ["workspace-settings"] }),
      ]);
    } catch (err) {
      setVaultError(
        err instanceof Error
          ? err.message
          : "Failed to index historical report.",
      );
    } finally {
      setUploadingDoc(false);
      if (reportFileRef.current) reportFileRef.current.value = "";
    }
  };

  const handleUploadGalleryAsset = async (files: FileList | null) => {
    if (!files || !files[0]) return;
    setVaultError("");
    setUploadingAsset(true);
    try {
      await apiClient.uploadGalleryAsset(
        files[0],
        assetTitle || files[0].name,
        assetCaption || assetTitle || files[0].name,
        assetCategory,
        assetTags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      );
      setUploadAssetOpen(false);
      setAssetTitle("");
      setAssetCaption("");
      setAssetTags("");
      await queryClient.invalidateQueries({ queryKey: ["gallery-assets"] });
    } catch (err) {
      setVaultError(
        err instanceof Error ? err.message : "Failed to upload asset.",
      );
    } finally {
      setUploadingAsset(false);
    }
  };

  const handleSaveStyleGuide = async () => {
    if (!styleGuide) return;
    setVaultError("");
    setSavingStyle(true);
    try {
      await apiClient.updateSettings({ style_guide_json: styleGuide });
      await queryClient.invalidateQueries({ queryKey: ["workspace-settings"] });
      setStyleSaved(true);
      window.setTimeout(() => setStyleSaved(false), 2000);
    } catch (err) {
      setVaultError(
        err instanceof Error ? err.message : "Failed to save style fingerprint.",
      );
    } finally {
      setSavingStyle(false);
    }
  };

  const filteredGallery = gallery.filter(
    (g) => galleryFilter === "all" || g.category === galleryFilter,
  );

  return (
    <div className="min-h-[calc(100vh-44px)] bg-[#F5F5F7]">
      <FrostedSubNav
        title="Knowledge & Style Vault"
        rightContent={
          <div className="flex items-center gap-1 rounded-[8px] border border-[#E0E0E0] bg-white p-1">
            <button
              type="button"
              onClick={() => setTab("reports")}
              className={`h-7 rounded-[6px] px-3 text-[13px] font-medium transition-colors ${
                tab === "reports"
                  ? "bg-[#1D1D1F] text-white"
                  : "text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
            >
              Past reports ({vaultDocs.length})
            </button>
            <button
              type="button"
              onClick={() => setTab("style")}
              className={`h-7 rounded-[6px] px-3 text-[13px] font-medium transition-colors ${
                tab === "style"
                  ? "bg-[#1D1D1F] text-white"
                  : "text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
            >
              Style fingerprint
            </button>
            <button
              type="button"
              onClick={() => setTab("gallery")}
              className={`h-7 rounded-[6px] px-3 text-[13px] font-medium transition-colors ${
                tab === "gallery"
                  ? "bg-[#1D1D1F] text-white"
                  : "text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
            >
              Visual gallery ({gallery.length})
            </button>
          </div>
        }
      />

      <section className="border-b border-[#E0E0E0] bg-white">
        <div className="mx-auto max-w-[1600px] px-5 py-7 sm:px-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h2 className="text-[28px] sm:text-[32px] font-medium tracking-[-0.02em] text-[#1D1D1F]">
                {tab === "reports"
                  ? "Historical Reports & Institutional Boilerplate"
                  : tab === "style"
                    ? "Author Style Fingerprint & Anti-AI Guardrails"
                    : "Reusable Equipment, Map & Chart Gallery"}
              </h2>
              <p className="mt-1.5 text-[14.5px] text-[#6E6E73]">
                {tab === "reports"
                  ? "Uploading .docx or .pdf reports indexes section prose, learns your layout blueprint, and extracts every embedded photo and logo."
                  : tab === "style"
                    ? "Preferred engineering units, voice conventions, and banned generic AI phrases enforced across every draft."
                    : "Extracted vessels, drill rigs, regional maps, laboratory photographs, and cached technical figures."}
              </p>
            </div>

            {tab === "gallery" ? (
              <Button size="sm" onClick={() => setUploadAssetOpen(true)}>
                <ImagePlus className="size-4" strokeWidth={1.5} />
                <span>Add visual asset</span>
              </Button>
            ) : null}
          </div>
        </div>
      </section>

      <main className="mx-auto max-w-[1600px] px-5 py-8 sm:px-8">
        {vaultError ? (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-[12px] border border-[#FECACA] bg-[#FEF2F2] px-4 py-3 text-[13.5px] text-[#DC2626]">
            <span>{vaultError}</span>
            <button
              type="button"
              onClick={() => setVaultError("")}
              className="rounded-md p-1 hover:bg-[#FEE2E2]"
              aria-label="Dismiss error"
            >
              <X className="size-4" />
            </button>
          </div>
        ) : null}

        {tab === "reports" ? (
          <div className="space-y-6">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDraggingReport(true);
              }}
              onDragLeave={() => setIsDraggingReport(false)}
              onDrop={(e) => {
                e.preventDefault();
                setIsDraggingReport(false);
                if (!uploadingDoc && e.dataTransfer.files?.length) {
                  void handleUploadVaultDoc(e.dataTransfer.files);
                }
              }}
            >
              <UtilityCard
                className={`transition-colors ${
                  isDraggingReport ? "border-[#0066CC] bg-[#F0F7FF]" : "border-[#E0E0E0]"
                }`}
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-[17px] font-medium text-[#1D1D1F]">
                      Index historical report (.docx, .pdf, .txt)
                    </h3>
                    <p className="mt-1 text-[13.5px] text-[#6E6E73]">
                      Drag and drop or select reports to extract boilerplate chunks, semantic embeddings, style rules, and embedded figures.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <select
                      value={docCategory}
                      onChange={(e) => setDocCategory(e.target.value)}
                      className="h-9 rounded-[8px] border border-[#E0E0E0] bg-[#F5F5F7] px-3 text-[13px] text-[#1D1D1F]"
                    >
                      <option value="field_report">Field / Lab Report</option>
                      <option value="proposal">Engineering Proposal</option>
                      <option value="reference">Procedures Manual</option>
                    </select>
                    <input
                      ref={reportFileRef}
                      type="file"
                      multiple
                      accept=".docx,.pdf,.txt,.md"
                      onChange={(e) => void handleUploadVaultDoc(e.target.files)}
                      className="hidden"
                    />
                    <Button
                      size="sm"
                      disabled={uploadingDoc}
                      onClick={() => reportFileRef.current?.click()}
                    >
                      {uploadingDoc ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <UploadCloud className="size-4" strokeWidth={1.5} />
                      )}
                      <span>{uploadingDoc ? "Indexing report..." : "Upload report"}</span>
                    </Button>
                  </div>
                </div>
              </UtilityCard>
            </div>

            {loadingDocs ? (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-48 rounded-[14px] border border-[#E0E0E0] bg-white"
                  />
                ))}
              </div>
            ) : vaultDocs.length === 0 ? (
              <div className="rounded-[14px] border border-[#E0E0E0] bg-white px-6 py-16 text-center">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full border border-[#B8D9FF] bg-[#F0F7FF] text-[#0066CC]">
                  <UploadCloud className="size-5" strokeWidth={1.5} />
                </div>
                <h3 className="mt-4 text-[22px] font-medium tracking-[-0.015em] text-[#1D1D1F]">
                  Your Knowledge &amp; Style Vault is empty
                </h3>
                <p className="mx-auto mt-2 max-w-[540px] text-[14.5px] text-[#6E6E73]">
                  Upload historical geotechnical field or laboratory reports (.docx or .pdf) to extract reusable boilerplate chunks,
                  learn your Author Style Fingerprint, build your Visual Gallery, and clone your PDF layout blueprint.
                </p>
                <div
                  onClick={() => !uploadingDoc && reportFileRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDraggingReport(true);
                  }}
                  onDragLeave={() => setIsDraggingReport(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDraggingReport(false);
                    if (!uploadingDoc && e.dataTransfer.files?.length) {
                      void handleUploadVaultDoc(e.dataTransfer.files);
                    }
                  }}
                  className={`mx-auto mt-6 flex max-w-[460px] cursor-pointer flex-col items-center justify-center rounded-[12px] border border-dashed border-[#0066CC] px-6 py-8 transition-colors ${
                    isDraggingReport ? "bg-[#F0F7FF]" : "bg-[#F5F5F7] hover:bg-[#F0F7FF]/60"
                  }`}
                >
                  <Button type="button" disabled={uploadingDoc}>
                    {uploadingDoc ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <UploadCloud className="size-4" strokeWidth={1.5} />
                    )}
                    <span>{uploadingDoc ? "Indexing Report..." : "Upload Historical Reports"}</span>
                  </Button>
                  <span className="mt-2.5 text-[12px] text-[#6E6E73]">
                    Drag &amp; drop or select .docx, .pdf, and .txt files
                  </span>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
                {vaultDocs.map((doc) => {
                  const uniqueTypes = Array.from(
                    new Set((doc.chunks || []).map((c) => c.section_type)),
                  );
                  const chunkCount = doc.chunk_count ?? doc.chunks?.length ?? 0;
                  const imageCount = doc.image_count ?? doc.extracted_images?.length ?? 0;
                  return (
                    <UtilityCard
                      key={doc.id}
                      className="flex flex-col justify-between border-[#E0E0E0]"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="flex size-10 shrink-0 items-center justify-center rounded-[9px] bg-[#F0F7FF] text-[#0066CC] border border-[#B8D9FF]">
                              <FileText className="size-5" strokeWidth={1.5} />
                            </div>
                            <div className="min-w-0">
                              <h4 className="truncate text-[15px] font-medium text-[#1D1D1F]">
                                {doc.filename}
                              </h4>
                              <span className="font-mono text-[12px] text-[#6E6E73]">
                                {doc.file_type.toUpperCase()} · {chunkCount} chunks · {imageCount} figures extracted
                              </span>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={async () => {
                              await apiClient.deleteVaultDocument(doc.id);
                              await Promise.all([
                                queryClient.invalidateQueries({
                                  queryKey: ["vault-documents"],
                                }),
                                queryClient.invalidateQueries({
                                  queryKey: ["gallery-assets"],
                                }),
                              ]);
                            }}
                            className="rounded-[7px] p-1.5 text-[#6E6E73] hover:bg-[#FEF2F2] hover:text-[#DC2626]"
                            aria-label="Delete report"
                          >
                            <Trash2 className="size-4" strokeWidth={1.5} />
                          </button>
                        </div>

                        <div className="mt-4 flex flex-wrap gap-1.5">
                          {uniqueTypes.map((st) => (
                            <span
                              key={st}
                              className="rounded-[6px] border border-[#E0E0E0] bg-[#F5F5F7] px-2.5 py-0.5 text-[12px] text-[#333333]"
                            >
                              {st.replace("_", " ")}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="mt-5 flex items-center justify-between border-t border-[#E0E0E0] pt-4">
                        <span className="inline-flex items-center gap-1.5 rounded-[7px] border border-[#A3E2B8] bg-[#F2FAF5] px-2.5 py-1 text-[12px] font-medium text-[#16A34A]">
                          <Database className="size-3.5" strokeWidth={1.5} />
                          Indexed
                        </span>

                        <Button
                          variant="secondary-pill"
                          size="sm"
                          onClick={() => {
                            setInspectTab("chunks");
                            setInspectDoc(doc);
                          }}
                        >
                          <BookOpen className="size-4" strokeWidth={1.5} />
                          <span>Inspect report</span>
                        </Button>
                      </div>
                    </UtilityCard>
                  );
                })}
              </div>
            )}
          </div>
        ) : null}

        {tab === "style" && styleGuide ? (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <UtilityCard className="space-y-5 border-[#E0E0E0]">
              <div>
                <h3 className="text-[18px] font-medium text-[#1D1D1F]">
                  Voice rules and engineering nomenclature
                </h3>
                <p className="mt-1 text-[13.5px] text-[#6E6E73]">
                  Enforced automatically across iterative section drafting, humanizing passes, and inline edits.
                </p>
              </div>

              <div>
                <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
                  Target tone
                </label>
                <input
                  type="text"
                  value={styleGuide.tone}
                  onChange={(e) =>
                    setStyleGuide({ ...styleGuide, tone: e.target.value })
                  }
                  className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-2 block text-[13px] font-medium text-[#1D1D1F]">
                  Preferred geotechnical nomenclature
                </label>
                <div className="flex flex-wrap gap-2">
                  {styleGuide.preferred_nomenclature.map((term) => (
                    <span
                      key={term}
                      className="inline-flex h-7 items-center gap-1.5 rounded-[6px] border border-[#B8D9FF] bg-[#F0F7FF] px-2.5 font-mono text-[12px] text-[#0066CC]"
                    >
                      {term}
                      <button
                        type="button"
                        onClick={() =>
                          setStyleGuide({
                            ...styleGuide,
                            preferred_nomenclature:
                              styleGuide.preferred_nomenclature.filter(
                                (t) => t !== term,
                              ),
                          })
                        }
                      >
                        <X className="size-3.5" />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="mt-3 flex gap-2">
                  <input
                    type="text"
                    value={newTerm}
                    onChange={(e) => setNewTerm(e.target.value)}
                    placeholder="Add term (e.g., Wison-APB, mBSF, CPTu)"
                    className="h-9 flex-1 rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13.5px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                  />
                  <Button
                    variant="secondary-pill"
                    size="sm"
                    onClick={() => {
                      if (!newTerm.trim()) return;
                      setStyleGuide({
                        ...styleGuide,
                        preferred_nomenclature: [
                          ...styleGuide.preferred_nomenclature,
                          newTerm.trim(),
                        ],
                      });
                      setNewTerm("");
                    }}
                  >
                    <Plus className="size-4" />
                    Add
                  </Button>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-[13px] font-medium text-[#1D1D1F]">
                  Extracted style rules
                </label>
                <ul className="space-y-2 text-[13.5px] text-[#333333]">
                  {styleGuide.voice_rules.map((rule, i) => (
                    <li
                      key={i}
                      className="rounded-[9px] border border-[#E0E0E0] bg-[#F5F5F7] px-3.5 py-2.5"
                    >
                      {rule}
                    </li>
                  ))}
                </ul>
              </div>
            </UtilityCard>

            <UtilityCard className="flex flex-col justify-between space-y-5 border-[#E0E0E0]">
              <div className="space-y-4">
                <div>
                  <h3 className="text-[18px] font-medium text-[#1D1D1F]">
                    Banned AI clichés list
                  </h3>
                  <p className="mt-1 text-[13.5px] text-[#6E6E73]">
                    The Stage 5 Anti-AI Humanizer Agent strips these phrases before compiling reports.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {styleGuide.banned_ai_phrases.map((phrase) => (
                    <span
                      key={phrase}
                      className="inline-flex h-7 items-center gap-1.5 rounded-[6px] border border-[#FECACA] bg-[#FEF2F2] px-2.5 text-[12.5px] text-[#DC2626]"
                    >
                      {phrase}
                      <button
                        type="button"
                        onClick={() =>
                          setStyleGuide({
                            ...styleGuide,
                            banned_ai_phrases:
                              styleGuide.banned_ai_phrases.filter(
                                (p) => p !== phrase,
                              ),
                          })
                        }
                      >
                        <X className="size-3.5" />
                      </button>
                    </span>
                  ))}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newBanned}
                    onChange={(e) => setNewBanned(e.target.value)}
                    placeholder="Add banned phrase"
                    className="h-9 flex-1 rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13.5px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
                  />
                  <Button
                    variant="secondary-pill"
                    size="sm"
                    onClick={() => {
                      if (!newBanned.trim()) return;
                      setStyleGuide({
                        ...styleGuide,
                        banned_ai_phrases: [
                          ...styleGuide.banned_ai_phrases,
                          newBanned.trim(),
                        ],
                      });
                      setNewBanned("");
                    }}
                  >
                    <Plus className="size-4" />
                    Add
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 border-t border-[#E0E0E0] pt-4">
                {styleSaved ? (
                  <span className="inline-flex items-center gap-1 text-[13.5px] text-[#16A34A]">
                    <Check className="size-4" /> Style fingerprint saved
                  </span>
                ) : null}
                <Button
                  disabled={savingStyle}
                  onClick={() => void handleSaveStyleGuide()}
                >
                  {savingStyle ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Check className="size-4" strokeWidth={1.5} />
                  )}
                  <span>Save style fingerprint</span>
                </Button>
              </div>
            </UtilityCard>
          </div>
        ) : null}

        {tab === "gallery" ? (
          <div className="space-y-6">
            <div className="flex flex-wrap gap-2">
              {[
                { id: "all", label: "All assets" },
                { id: "vessel", label: "Survey vessels" },
                { id: "drill_rig", label: "Drill rigs & PCPT" },
                { id: "lab_equipment", label: "Lab & scientific plots" },
                { id: "map", label: "Location & geology maps" },
                { id: "field_photo", label: "Field cores & photos" },
              ].map((cat) => (
                <OptionChip
                  key={cat.id}
                  selected={galleryFilter === cat.id}
                  onClick={() => setGalleryFilter(cat.id)}
                >
                  {cat.label}
                </OptionChip>
              ))}
            </div>

            {filteredGallery.length === 0 ? (
              <div className="rounded-[14px] border border-[#E0E0E0] bg-white px-6 py-14 text-center">
                <h3 className="text-[20px] font-medium text-[#1D1D1F]">
                  No extracted or uploaded visual assets yet
                </h3>
                <p className="mx-auto mt-1.5 max-w-[480px] text-[14px] text-[#6E6E73]">
                  Upload a historical report in Past Reports to extract embedded photographs automatically, or add a visual asset manually.
                </p>
                <div className="mt-5">
                  <Button size="sm" onClick={() => setUploadAssetOpen(true)}>
                    <ImagePlus className="size-4" strokeWidth={1.5} />
                    <span>Add visual asset</span>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {filteredGallery.map((asset) => (
                  <UtilityCard
                    key={asset.id}
                    className="flex flex-col justify-between border-[#E0E0E0] p-4"
                  >
                    <div>
                      <div className="relative aspect-[16/10] w-full overflow-hidden rounded-[8px] border border-[#E0E0E0] bg-[#F5F5F7]">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={resolveBackendUrl(asset.file_url)}
                          alt={asset.title}
                          className="h-full w-full object-contain"
                        />
                        <button
                          type="button"
                          onClick={async () => {
                            await apiClient.deleteGalleryAsset(asset.id);
                            await queryClient.invalidateQueries({
                              queryKey: ["gallery-assets"],
                            });
                          }}
                          className="absolute right-2 top-2 rounded-[6px] border border-[#E0E0E0] bg-white/90 p-1.5 text-[#6E6E73] hover:bg-[#FEF2F2] hover:text-[#DC2626]"
                          aria-label={`Delete ${asset.title}`}
                        >
                          <Trash2 className="size-3.5" strokeWidth={1.5} />
                        </button>
                      </div>
                      <h4 className="mt-3 text-[14.5px] font-medium text-[#1D1D1F]">
                        {asset.title}
                      </h4>
                      <p className="mt-1 line-clamp-2 text-[12.5px] text-[#6E6E73]">
                        {asset.default_caption}
                      </p>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1.5 border-t border-[#E0E0E0] pt-3">
                      {(asset.tags || []).slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="rounded-[6px] bg-[#F5F5F7] px-2 py-0.5 font-mono text-[11px] text-[#333333]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </UtilityCard>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </main>

      {/* Inspect Report Chunks & Extracted Figures Modal */}
      <Modal
        open={Boolean(inspectDoc)}
        onOpenChange={(open) => {
          if (!open) setInspectDoc(null);
        }}
        title={inspectDoc?.filename || "Vault report"}
        description="Extracted heading boilerplate and figures saved to the Visual Gallery"
        maxWidthClass="max-w-[780px]"
      >
        <div className="mb-4 flex items-center gap-2 border-b border-[#E0E0E0] pb-3">
          <button
            type="button"
            onClick={() => setInspectTab("chunks")}
            className={`inline-flex h-8 items-center gap-1.5 rounded-[7px] px-3 text-[13px] font-medium ${
              inspectTab === "chunks"
                ? "bg-[#1D1D1F] text-white"
                : "bg-[#F5F5F7] text-[#6E6E73]"
            }`}
          >
            <BookOpen className="size-3.5" strokeWidth={1.5} />
            <span>Text chunks ({inspectDoc?.chunks?.length ?? 0})</span>
          </button>
          <button
            type="button"
            onClick={() => setInspectTab("images")}
            className={`inline-flex h-8 items-center gap-1.5 rounded-[7px] px-3 text-[13px] font-medium ${
              inspectTab === "images"
                ? "bg-[#1D1D1F] text-white"
                : "bg-[#F5F5F7] text-[#6E6E73]"
            }`}
          >
            <Images className="size-3.5" strokeWidth={1.5} />
            <span>Extracted figures ({inspectDoc?.extracted_images?.length ?? 0})</span>
          </button>
          <button
            type="button"
            onClick={() => setInspectTab("blueprint")}
            className={`inline-flex h-8 items-center gap-1.5 rounded-[7px] px-3 text-[13px] font-medium ${
              inspectTab === "blueprint"
                ? "bg-[#1D1D1F] text-white"
                : "bg-[#F5F5F7] text-[#6E6E73]"
            }`}
          >
            <FileText className="size-3.5" strokeWidth={1.5} />
            <span>PDF Layout Blueprint</span>
          </button>
        </div>

        {inspectTab === "chunks" ? (
          <div className="space-y-3">
            {(inspectDoc?.chunks || []).map((chk) => (
              <div
                key={chk.id}
                className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[14px] font-medium text-[#1D1D1F]">
                    {chk.heading_title}
                  </span>
                  <span className="rounded-[6px] border border-[#B8D9FF] bg-[#F0F7FF] px-2.5 py-0.5 font-mono text-[11.5px] text-[#0066CC]">
                    {chk.section_type}
                  </span>
                </div>
                <p className="mt-2 text-[13.5px] leading-relaxed text-[#333333]">
                  {chk.content_text}
                </p>
              </div>
            ))}
          </div>
        ) : inspectTab === "images" ? (
          (inspectDoc?.extracted_images?.length ?? 0) === 0 ? (
            <div className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-8 text-center text-[13.5px] text-[#6E6E73]">
              No embedded figures extracted from this document.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {(inspectDoc?.extracted_images || []).map((img, idx) => (
                <div
                  key={idx}
                  className="overflow-hidden rounded-[10px] border border-[#E0E0E0] bg-white"
                >
                  <div className="h-[160px] w-full bg-[#F5F5F7] p-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={resolveBackendUrl(img.file_url)}
                      alt={img.title}
                      className="h-full w-full object-contain"
                    />
                  </div>
                  <div className="p-3">
                    <div className="text-[13px] font-medium text-[#1D1D1F]">{img.title}</div>
                    <div className="mt-0.5 text-[12px] text-[#6E6E73]">{img.category}</div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-[10px] border border-[#B8D9FF] bg-[#F0F7FF] p-3.5 sm:col-span-2">
                <div className="text-[11.5px] font-medium text-[#0066CC]">
                  Forensic Report Archetype &amp; Split Structure
                </div>
                <div className="mt-1 font-mono text-[13px] font-semibold text-[#1D1D1F]">
                  {inspectDoc?.pdf_layout_blueprint?.report_archetype || "OFFSHORE_MARINE_GEOTECHNICAL_FIELD_REPORT"}
                  {inspectDoc?.pdf_layout_blueprint?.splits_interpretative_factual
                    ? " · Split: INTERPRETATIVE REPORT + FACTUAL REPORT"
                    : ""}
                </div>
              </div>
              <div className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-3.5">
                <div className="text-[11.5px] font-medium text-[#6E6E73]">Running header</div>
                <div className="mt-1 text-[13px] text-[#1D1D1F]">
                  {inspectDoc?.pdf_layout_blueprint?.running_header || "2-cell corporate header"}
                </div>
              </div>
              <div className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-3.5">
                <div className="text-[11.5px] font-medium text-[#6E6E73]">TOC style</div>
                <div className="mt-1 text-[13px] text-[#1D1D1F]">
                  {inspectDoc?.pdf_layout_blueprint?.toc_style || "Clickable internal links + dot leaders"}
                </div>
              </div>
              <div className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-3.5">
                <div className="text-[11.5px] font-medium text-[#6E6E73]">Table geometry</div>
                <div className="mt-1 text-[13px] text-[#1D1D1F]">
                  {inspectDoc?.pdf_layout_blueprint?.table_style || "0.6pt solid charcoal borders"}
                </div>
              </div>
              <div className="rounded-[10px] border border-[#E0E0E0] bg-[#F5F5F7] p-3.5">
                <div className="text-[11.5px] font-medium text-[#6E6E73]">Figure presentation</div>
                <div className="mt-1 text-[13px] text-[#1D1D1F]">
                  {inspectDoc?.pdf_layout_blueprint?.figure_style || "Grouped Typst figures with captions"}
                </div>
              </div>
            </div>

            {inspectDoc?.pdf_layout_blueprint?.entities_json ? (
              <div className="rounded-[10px] border border-[#E0E0E0] bg-white p-4">
                <div className="text-[12.5px] font-semibold text-[#1D1D1F]">
                  Forensic Corporate &amp; Entity Graph
                </div>
                <div className="mt-2.5 grid grid-cols-1 gap-2.5 text-[12.5px] sm:grid-cols-2">
                  <div>
                    <span className="font-semibold text-[#0066CC]">Client / Operator: </span>
                    <span className="text-[#333333]">
                      {(inspectDoc.pdf_layout_blueprint.entities_json.client_operators || []).join(", ") || "Detected on cover"}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#0066CC]">Lead Contractor: </span>
                    <span className="text-[#333333]">
                      {(inspectDoc.pdf_layout_blueprint.entities_json.lead_contractors || []).join(", ") || "Detected on cover"}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#0066CC]">Geotechnical Consultant: </span>
                    <span className="text-[#333333]">
                      {(inspectDoc.pdf_layout_blueprint.entities_json.geotechnical_consultants || []).join(", ") || "Detected on cover"}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#0066CC]">Subcontractors &amp; Personnel: </span>
                    <span className="text-[#333333]">
                      {[
                        ...(inspectDoc.pdf_layout_blueprint.entities_json.field_and_lab_subcontractors || []),
                        ...(inspectDoc.pdf_layout_blueprint.entities_json.key_personnel || []),
                      ].join(", ") || "Indexed"}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}

            {inspectDoc?.pdf_layout_blueprint?.extracted_formulas &&
            inspectDoc.pdf_layout_blueprint.extracted_formulas.length > 0 ? (
              <div className="rounded-[10px] border border-[#E0E0E0] bg-white p-4">
                <div className="text-[12.5px] font-semibold text-[#1D1D1F]">
                  Extracted Mathematical &amp; Laboratory Equations ({inspectDoc.pdf_layout_blueprint.extracted_formulas.length})
                </div>
                <div className="mt-2 space-y-1.5">
                  {inspectDoc.pdf_layout_blueprint.extracted_formulas.map((eq, i) => (
                    <div
                      key={i}
                      className="rounded-[7px] border border-[#E0E0E0] bg-[#F5F5F7] px-3 py-1.5 font-mono text-[12px] text-[#1D1D1F]"
                    >
                      <span className="font-semibold text-[#0066CC]">{eq.name}: </span>
                      <span>{eq.formula_plain}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {inspectDoc?.pdf_layout_blueprint?.cover_structure &&
            inspectDoc.pdf_layout_blueprint.cover_structure.length > 0 ? (
              <div className="rounded-[10px] border border-[#E0E0E0] bg-white p-4">
                <div className="text-[12.5px] font-semibold text-[#1D1D1F]">
                  Cloned Cover &amp; Front-Matter Structure
                </div>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-[13px] text-[#333333]">
                  {inspectDoc.pdf_layout_blueprint.cover_structure.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {inspectDoc?.pdf_layout_blueprint?.detected_headings &&
            inspectDoc.pdf_layout_blueprint.detected_headings.length > 0 ? (
              <div className="rounded-[10px] border border-[#E0E0E0] bg-white p-4">
                <div className="text-[12.5px] font-semibold text-[#1D1D1F]">
                  Detected Section Hierarchy ({inspectDoc.pdf_layout_blueprint.detected_headings.length})
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {inspectDoc.pdf_layout_blueprint.detected_headings.map((h, i) => (
                    <span
                      key={i}
                      className="rounded-[6px] border border-[#E0E0E0] bg-[#F5F5F7] px-2.5 py-1 font-mono text-[11.5px] text-[#1D1D1F]"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </Modal>

      {/* Add Visual Asset Modal */}
      <Modal
        open={uploadAssetOpen}
        onOpenChange={setUploadAssetOpen}
        title="Add reusable equipment, map, or field photo"
        description="Assets added here appear across all projects when resolving Smart Image Placeholders."
      >
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
              Asset title
            </label>
            <input
              type="text"
              value={assetTitle}
              onChange={(e) => setAssetTitle(e.target.value)}
              placeholder="e.g., DP-2 Survey Vessel Deck Configuration"
              className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
              Default report caption
            </label>
            <input
              type="text"
              value={assetCaption}
              onChange={(e) => setAssetCaption(e.target.value)}
              placeholder="e.g., Geotechnical survey vessel positioned on offshore location"
              className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
                Category
              </label>
              <select
                value={assetCategory}
                onChange={(e) => setAssetCategory(e.target.value)}
                className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
              >
                <option value="vessel">Vessel</option>
                <option value="drill_rig">Drill Rig</option>
                <option value="lab_equipment">Lab Equipment</option>
                <option value="map">Location Map</option>
                <option value="field_photo">Field Photo</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-[#1D1D1F]">
                Tags (comma separated)
              </label>
              <input
                type="text"
                value={assetTags}
                onChange={(e) => setAssetTags(e.target.value)}
                placeholder="e.g., DP-2, CPTu, Offshore"
                className="h-10 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[14px] text-[#1D1D1F] focus:border-[#0066CC] focus:outline-none"
              />
            </div>
          </div>

          <input
            ref={assetFileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => void handleUploadGalleryAsset(e.target.files)}
            className="hidden"
          />
          <Button
            disabled={uploadingAsset}
            onClick={() => assetFileRef.current?.click()}
            className="w-full"
          >
            {uploadingAsset ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <UploadCloud className="size-4" strokeWidth={1.5} />
            )}
            <span>Select image and save to visual gallery</span>
          </Button>
        </div>
      </Modal>
    </div>
  );
}
