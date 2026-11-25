"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  Loader2,
  UploadCloud,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { FrostedSubNav } from "@/components/layout/FrostedSubNav";
import { Button } from "@/components/ui/Button";
import { UtilityCard } from "@/components/ui/UtilityCard";

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = React.useState("");
  const [scopePrompt, setScopePrompt] = React.useState("");
  const [files, setFiles] = React.useState<File[]>([]);
  const [dragging, setDragging] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState("");

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const { data: settings } = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: apiClient.getSettings,
  });

  const handleAddFiles = (incoming: FileList | File[] | null) => {
    if (!incoming) return;
    const arr = Array.from(incoming);
    if (arr.length === 0) return;
    setFiles((prev) => [...prev, ...arr]);
  };

  const handleCreateAndOpen = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      setError("Enter a report title to get started.");
      return;
    }

    setError("");
    setBusy(true);
    try {
      const created = await apiClient.createProject({
        title: cleanTitle,
        subtitle: scopePrompt.trim().slice(0, 240),
        document_type: "Geotechnical Survey Field Report",
        contractor_name: settings?.default_contractor_name || "",
        revision_number: "Rev 01",
      });

      if (files.length > 0) {
        try {
          await apiClient.uploadIntakeFiles(created.id, files);
        } catch (intakeErr) {
          await apiClient.deleteProject(created.id).catch(() => undefined);
          throw intakeErr;
        }
      }

      if (scopePrompt.trim() && typeof window !== "undefined") {
        window.sessionStorage.setItem(
          `geotech_initial_prompt_${created.id}`,
          scopePrompt.trim(),
        );
      }

      router.push(`/projects/${created.id}/studio`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create project.",
      );
      setBusy(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-44px)] bg-[#F5F5F7] pb-16">
      <FrostedSubNav
        title="New Report"
        subtitle="Minimalist kickoff — client details and parameters are verified conversationally in Studio"
      />

      <main className="mx-auto max-w-[680px] px-5 py-12">
        <form onSubmit={handleCreateAndOpen}>
          <UtilityCard className="space-y-6 p-8">
            <div>
              <h2 className="text-[28px] font-semibold tracking-[-0.02em] leading-tight text-[#1D1D1F]">
                Start a New Engineering Report
              </h2>
              <p className="mt-1.5 text-[14.5px] leading-relaxed text-[#7A7A7A]">
                {settings?.default_contractor_name
                  ? `Defaults applied: ${settings.default_contractor_name}${settings.author_name ? ` · ${settings.author_name}` : ""}.`
                  : "Enter a title and optional scope or field spreadsheets. The Studio Agent will verify any missing details with you."}
              </p>
            </div>

            {error ? (
              <div className="rounded-[12px] border border-[#F5B3B3] bg-[#FFF2F2] px-4 py-3 text-[13.5px] text-[#C91919]">
                {error}
              </div>
            ) : null}

            <div>
              <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                Report title{" "}
                <span className="font-normal text-[#7A7A7A]">(Required)</span>
              </label>
              <input
                type="text"
                autoFocus
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Geotechnical Investigation for Bonny River HDD Pipeline Crossing"
                className="h-11 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3.5 text-[16px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                Brief scope or initial prompt{" "}
                <span className="font-normal text-[#7A7A7A]">(Optional)</span>
              </label>
              <textarea
                rows={3}
                value={scopePrompt}
                onChange={(e) => setScopePrompt(e.target.value)}
                placeholder="Describe the client, site location, borehole/CPT scope, or specific engineering instructions..."
                className="w-full rounded-[8px] border border-[#E0E0E0] bg-white p-3.5 text-[15px] leading-relaxed text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                Raw field spreadsheets or notes{" "}
                <span className="font-normal text-[#7A7A7A]">(Optional)</span>
              </label>

              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  handleAddFiles(e.dataTransfer.files);
                }}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-[18px] border-[1.5px] border-dashed px-6 py-8 text-center transition-colors ${
                  dragging
                    ? "border-[#0066CC] bg-[#F0F7FF]"
                    : "border-[#E0E0E0] bg-[#FAFAFC] hover:border-[#0066CC]"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".xlsx,.xls,.csv,.docx,.pdf,.txt,.png,.jpg,.jpeg,.webp"
                  onChange={(e) => handleAddFiles(e.target.files)}
                  className="hidden"
                />
                <UploadCloud className="size-6 text-[#0066CC]" strokeWidth={1.5} />
                <p className="mt-2.5 text-[14.5px] font-semibold text-[#1D1D1F]">
                  Drop coordinate sheets (.xlsx/.csv), field logs, or photos
                </p>
                <p className="mt-0.5 text-[12.5px] text-[#7A7A7A]">
                  Exact coordinate decimals are parsed deterministically — or attach files later in Studio
                </p>
              </div>

              {files.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {files.map((file, idx) => (
                    <span
                      key={`${file.name}-${idx}`}
                      className="inline-flex h-8 items-center gap-2 rounded-full border border-[#E0E0E0] bg-white px-3 text-[12.5px] text-[#1D1D1F]"
                    >
                      <FileText className="size-3.5 text-[#0066CC]" strokeWidth={1.5} />
                      <span className="max-w-[220px] truncate">{file.name}</span>
                      <button
                        type="button"
                        onClick={() =>
                          setFiles((prev) => prev.filter((_, i) => i !== idx))
                        }
                        className="text-[#7A7A7A] hover:text-[#1D1D1F]"
                        aria-label={`Remove ${file.name}`}
                      >
                        <X className="size-3.5" />
                      </button>
                    </span>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="flex items-center justify-end border-t border-[#F0F0F0] pt-5">
              <Button type="submit" size="lg" disabled={busy || !title.trim()}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : null}
                <span>
                  {busy ? "Initializing Studio..." : "Open in Document Studio"}
                </span>
              </Button>
            </div>
          </UtilityCard>
        </form>
      </main>
    </div>
  );
}
