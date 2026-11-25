"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FileSpreadsheet,
  FolderPlus,
  Layers,
  Paperclip,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { FrostedSubNav } from "@/components/layout/FrostedSubNav";
import { Button } from "@/components/ui/Button";
import { UtilityCard } from "@/components/ui/UtilityCard";
import { OptionChip } from "@/components/ui/OptionChip";
import { SearchPillInput } from "@/components/ui/SearchPillInput";
import { formatRelativeTime } from "@/lib/utils";
import type { ProjectStatus } from "@/types/project";

const STATUS_BADGES: Record<
  ProjectStatus,
  { label: string; bg: string; border: string; text: string }
> = {
  intake: {
    label: "Intake",
    bg: "bg-[#F5F5F7]",
    border: "border-[#E0E0E0]",
    text: "text-[#333333]",
  },
  clarifying: {
    label: "Clarification needed",
    bg: "bg-[#FFF9EB]",
    border: "border-[#F5D07E]",
    text: "text-[#945800]",
  },
  drafting: {
    label: "Drafting",
    bg: "bg-[#F0F7FF]",
    border: "border-[#B8D9FF]",
    text: "text-[#0066CC]",
  },
  review: {
    label: "Draft ready",
    bg: "bg-[#F0F7FF]",
    border: "border-[#B8D9FF]",
    text: "text-[#0066CC]",
  },
  completed: {
    label: "Exported",
    bg: "bg-[#F2FAF5]",
    border: "border-[#A3E2B8]",
    text: "text-[#106831]",
  },
};

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<string>("all");

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: apiClient.listProjects,
  });

  const { data: vaultDocs = [] } = useQuery({
    queryKey: ["vault-documents"],
    queryFn: apiClient.listVaultDocuments,
  });

  const { data: gallery = [] } = useQuery({
    queryKey: ["gallery-assets"],
    queryFn: apiClient.listGalleryAssets,
  });

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return projects.filter((p) => {
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (!q) return true;
      return (
        p.title.toLowerCase().includes(q) ||
        p.client_name.toLowerCase().includes(q) ||
        p.contractor_ref_code.toLowerCase().includes(q) ||
        p.client_ref_code.toLowerCase().includes(q) ||
        (p.subtitle || "").toLowerCase().includes(q)
      );
    });
  }, [projects, search, statusFilter]);

  const totalChunks = vaultDocs.reduce(
    (sum, doc) => sum + (doc.chunk_count || doc.chunks?.length || 0),
    0,
  );
  const openQaCount = projects.reduce(
    (sum, p) => sum + (p.qa_alerts || []).filter((a) => !a.is_resolved).length,
    0,
  );

  return (
    <div className="min-h-[calc(100vh-44px)] bg-[#F5F5F7]">
      <FrostedSubNav
        title="Projects"
        subtitle="Offshore and geotechnical engineering deliverables"
        rightContent={
          <Link href="/projects/new">
            <Button size="sm">
              <FolderPlus className="size-4" strokeWidth={1.5} />
              <span>New project folder</span>
            </Button>
          </Link>
        }
      />

      {/* Pure White Summary Band */}
      <section className="w-full border-b border-[#E0E0E0] bg-white">
        <div className="mx-auto max-w-[1440px] px-5 py-10 sm:px-8">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <h2 className="text-[34px] sm:text-[40px] font-semibold tracking-[-0.02em] leading-[1.1] text-[#1D1D1F]">
                Field Reports &amp; Survey Deliverables
              </h2>
              <p className="mt-2 max-w-[640px] text-[17px] leading-[1.47] text-[#333333]">
                Author, cross-check, and typeset publication-grade A4 geotechnical reports grounded in your Knowledge Vault.
              </p>
            </div>

            <div className="flex flex-wrap items-baseline gap-8 sm:gap-12">
              <div>
                <div className="text-[36px] font-semibold leading-none tabular-nums text-[#1D1D1F]">
                  {projects.length}
                </div>
                <div className="mt-1.5 text-[13px] text-[#7A7A7A]">
                  Active reports
                </div>
              </div>
              <div>
                <div className="text-[36px] font-semibold leading-none tabular-nums text-[#1D1D1F]">
                  {totalChunks}
                </div>
                <div className="mt-1.5 text-[13px] text-[#7A7A7A]">
                  Vault style chunks ({vaultDocs.length} docs)
                </div>
              </div>
              <div>
                <div className="text-[36px] font-semibold leading-none tabular-nums text-[#1D1D1F]">
                  {gallery.length}
                </div>
                <div className="mt-1.5 text-[13px] text-[#7A7A7A]">
                  Reusable visuals ({openQaCount} QA open)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Parchment Projects Grid Band */}
      <section className="mx-auto max-w-[1440px] px-5 py-10 sm:px-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <SearchPillInput
            value={search}
            onChange={setSearch}
            className="md:max-w-[420px]"
          />

          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: "all", label: "All" },
              { id: "clarifying", label: "Clarification needed" },
              { id: "review", label: "In review" },
              { id: "completed", label: "Exported" },
            ].map((chip) => (
              <OptionChip
                key={chip.id}
                selected={statusFilter === chip.id}
                onClick={() => setStatusFilter(chip.id)}
              >
                {chip.label}
              </OptionChip>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-[280px] animate-pulse rounded-[18px] border border-[#E0E0E0] bg-white"
              />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="mt-10 rounded-[18px] border border-[#E0E0E0] bg-white px-6 py-16 text-center">
            <h3 className="text-[32px] font-semibold tracking-[-0.02em] text-[#1D1D1F]">
              No documentation projects yet
            </h3>
            <p className="mx-auto mt-3 max-w-[520px] text-[18px] font-light leading-relaxed text-[#333333]">
              Start a new client report folder by entering a title, brief scope, or uploading raw field spreadsheets.
            </p>
            <div className="mt-6">
              <Link href="/projects/new">
                <Button size="lg">
                  <FolderPlus className="size-4" strokeWidth={1.5} />
                  <span>Create First Project Folder</span>
                </Button>
              </Link>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="mt-10 rounded-[18px] border border-[#E0E0E0] bg-white px-6 py-16 text-center">
            <h3 className="text-[24px] font-semibold tracking-[-0.015em] text-[#1D1D1F]">
              No matching documentation projects
            </h3>
            <p className="mx-auto mt-2 max-w-[520px] text-[15px] text-[#7A7A7A]">
              Adjust your search filter or create a new project folder.
            </p>
          </div>
        ) : (
          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((proj) => {
              const badge = STATUS_BADGES[proj.status] || STATUS_BADGES.intake;
              const openAlerts = (proj.qa_alerts || []).filter(
                (a) => !a.is_resolved,
              ).length;
              const openClar = (proj.clarifications || []).filter(
                (c) => !c.is_resolved && !c.omit_section,
              ).length;

              return (
                <UtilityCard
                  key={proj.id}
                  className="flex flex-col justify-between transition-colors hover:border-[#0066CC]"
                >
                  <div>
                    <div className="flex items-center justify-between gap-3 border-b border-[#F0F0F0] pb-4">
                      <span className="truncate text-[13px] font-semibold text-[#333333]">
                        {proj.client_name || proj.contractor_name || "Geotechnical Deliverable"}
                      </span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="rounded-[5px] border border-[#E0E0E0] bg-[#F5F5F7] px-2 py-0.5 font-mono text-[11.5px] text-[#1D1D1F]">
                          {proj.revision_number}
                        </span>
                        <button
                          type="button"
                          onClick={async () => {
                            await apiClient.deleteProject(proj.id);
                            await queryClient.invalidateQueries({
                              queryKey: ["projects"],
                            });
                          }}
                          className="rounded-full p-1 text-[#7A7A7A] hover:bg-[#FFF2F2] hover:text-[#C91919]"
                          aria-label={`Delete ${proj.title}`}
                        >
                          <Trash2 className="size-3.5" strokeWidth={1.5} />
                        </button>
                      </div>
                    </div>

                    <h3 className="mt-4 text-[17px] font-semibold leading-snug text-[#1D1D1F]">
                      {proj.title}
                    </h3>
                    {proj.subtitle ? (
                      <p className="mt-1 line-clamp-2 text-[14px] text-[#7A7A7A]">
                        {proj.subtitle}
                      </p>
                    ) : null}

                    <div className="mt-5 space-y-2 rounded-[11px] border border-[#E0E0E0] bg-[#FAFAFC] p-3.5 text-[13px]">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[#7A7A7A]">Reference</span>
                        <span className="font-mono text-[12px] text-[#1D1D1F] truncate">
                          {proj.contractor_ref_code || proj.id}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[#7A7A7A]">Scope</span>
                        <span className="inline-flex items-center gap-3 font-mono text-[12px] tabular-nums text-[#333333]">
                          <span className="inline-flex items-center gap-1" title="Uploaded files">
                            <FileSpreadsheet className="size-3.5 text-[#0066CC]" strokeWidth={1.5} />
                            {proj.input_files?.length ?? 0}
                          </span>
                          <span className="inline-flex items-center gap-1" title="Merged PDF attachments">
                            <Paperclip className="size-3.5 text-[#0066CC]" strokeWidth={1.5} />
                            {proj.attachments?.length ?? 0}
                          </span>
                          <span className="inline-flex items-center gap-1" title="Drafted chapters">
                            <Layers className="size-3.5 text-[#0066CC]" strokeWidth={1.5} />
                            {proj.document_ast_json?.sections?.length ?? 0}
                          </span>
                        </span>
                      </div>
                    </div>

                    {(openAlerts > 0 || openClar > 0) && (
                      <div className="mt-3.5 flex flex-wrap gap-2">
                        {openAlerts > 0 ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#F5D07E] bg-[#FFF9EB] px-2.5 py-0.5 text-[12px] text-[#945800]">
                            <AlertTriangle className="size-3.5" strokeWidth={1.5} />
                            {openAlerts} QA alert
                          </span>
                        ) : null}
                        {openClar > 0 ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#F5D07E] bg-[#FFF9EB] px-2.5 py-0.5 text-[12px] text-[#945800]">
                            <ShieldCheck className="size-3.5" strokeWidth={1.5} />
                            {openClar} verification
                          </span>
                        ) : null}
                      </div>
                    )}
                  </div>

                  <div className="mt-6 flex items-center justify-between border-t border-[#F0F0F0] pt-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[12px] ${badge.bg} ${badge.border} ${badge.text}`}
                      >
                        {proj.status === "completed" ? (
                          <CheckCircle2 className="size-3.5" strokeWidth={1.5} />
                        ) : null}
                        {badge.label}
                      </span>
                      <span className="text-[12px] text-[#7A7A7A]">
                        {formatRelativeTime(proj.updated_at)}
                      </span>
                    </div>

                    <Link
                      href={`/projects/${proj.id}/studio`}
                      className="inline-flex items-center gap-1 text-[14px] font-semibold text-[#0066CC] hover:underline"
                    >
                      <span>Open Studio</span>
                      <ArrowRight className="size-4" strokeWidth={1.75} />
                    </Link>
                  </div>
                </UtilityCard>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
