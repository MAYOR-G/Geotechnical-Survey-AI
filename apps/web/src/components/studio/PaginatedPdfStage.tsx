"use client";

import * as React from "react";
import {
  FileText,
  Loader2,
  Minus,
  Plus,
  RefreshCw,
  RotateCcw,
} from "lucide-react";
import { resolveBackendUrl } from "@/lib/api-client";
import { useStudioStore } from "@/stores/useStudioStore";
import { Button } from "@/components/ui/Button";
import type { EngineeringTableData, Project, SmartPlaceholderNode } from "@/types/project";

interface PaginatedPdfStageProps {
  project: Project;
  isCompiling: boolean;
  onRefreshPdf: () => void;
  viewerMode?: "a4_sheets" | "compiled_pdf";
  onViewerModeChange?: (mode: "a4_sheets" | "compiled_pdf") => void;
  hideToolbar?: boolean;
}

function CorporateRunningHeader({ project }: { project: Project }) {
  const logos = project.header_logos_json || [];
  const clientLogo = logos.find((l) => l.role === "client")?.url || "";
  const contractorLogo = logos.find((l) => l.role === "contractor")?.url || "";
  const partnerLogo = logos.find((l) => l.role === "partner")?.url || "";

  return (
    <table className="w-full border-collapse border border-[#1D1D1F]">
      <tbody>
        <tr>
          <td className="w-[48%] border border-[#1D1D1F] px-3 py-2 align-middle">
            {clientLogo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={resolveBackendUrl(clientLogo)}
                alt={project.client_name || "Client"}
                className="h-9 w-auto object-contain"
              />
            ) : (
              <span className="text-[11px] font-semibold text-[#1D1D1F]">
                {project.client_name || "Client"}
              </span>
            )}
          </td>
          <td className="w-[52%] border border-[#1D1D1F] px-3 py-2 align-middle">
            <div className="flex items-center justify-end gap-4">
              {contractorLogo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={resolveBackendUrl(contractorLogo)}
                  alt={project.contractor_name || "Contractor"}
                  className="h-8 w-auto object-contain"
                />
              ) : (
                <span className="text-[11px] font-semibold text-[#1D1D1F]">
                  {project.contractor_name || "Contractor"}
                </span>
              )}
              {partnerLogo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={resolveBackendUrl(partnerLogo)}
                  alt="Partner"
                  className="h-6 w-auto object-contain"
                />
              ) : null}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}

function A4TableRenderer({ tbl }: { tbl: EngineeringTableData }) {
  return (
    <div id={tbl.id} className="mt-4 scroll-mt-4">
      <div className="mb-1.5 text-[10.5px] font-semibold text-[#1D1D1F]">
        {tbl.table_number ? `${tbl.table_number}: ` : ""}
        {tbl.title}
      </div>
      <div className="overflow-x-auto border border-[#1D1D1F]">
        <table className="w-full border-collapse text-[8.5px]">
          <thead className="bg-[#F5F5F7]">
            {tbl.multi_header && tbl.multi_header.length > 0 ? (
              tbl.multi_header.map((headerRow, hIdx) => (
                <tr key={hIdx}>
                  {headerRow.map((cell, cIdx) => (
                    <th
                      key={cIdx}
                      colSpan={cell.colspan}
                      rowSpan={cell.rowspan}
                      className="border border-[#1D1D1F] px-1 py-1 text-center font-semibold text-[#1D1D1F]"
                    >
                      {cell.label}
                    </th>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                {tbl.columns.map((col, cIdx) => (
                  <th
                    key={cIdx}
                    className="border border-[#1D1D1F] px-1.5 py-1 text-left font-semibold text-[#1D1D1F]"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            )}
          </thead>
          <tbody>
            {tbl.rows.map((row, rIdx) => (
              <tr key={rIdx}>
                {tbl.columns.map((_, cIdx) => (
                  <td
                    key={cIdx}
                    className="whitespace-pre-line border border-[#6B7280] px-1.5 py-1 text-[#1D1D1F] tabular-nums"
                  >
                    {row[cIdx] ?? ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {tbl.footnote ? (
        <p className="mt-1 text-[9px] italic text-[#4B5565]">{tbl.footnote}</p>
      ) : null}
    </div>
  );
}

function UnboxedA4Figure({ ph }: { ph: SmartPlaceholderNode }) {
  const caption = ph.caption || `${ph.figure_number}: ${ph.prompt}`;
  const hasSecondary = Boolean(ph.secondary_url);
  const layout = ph.layout || (hasSecondary ? "side_by_side" : "single");

  if (!ph.resolved_url) {
    return (
      <div id={ph.id} className="my-5 scroll-mt-4 py-6 text-center text-[10.5px] text-[#71717A]">
        [{caption}]
      </div>
    );
  }

  if (hasSecondary && ph.secondary_url && layout === "side_by_side") {
    return (
      <figure id={ph.id} className="my-5 scroll-mt-4">
        <div className="grid grid-cols-2 items-start gap-3">
          <div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resolveBackendUrl(ph.resolved_url)}
              alt={caption}
              className="max-h-[300px] w-full object-contain"
            />
            {ph.secondary_caption ? (
              <figcaption className="mt-1.5 text-center text-[10px] font-semibold text-[#1D1D1F]">
                {caption}
              </figcaption>
            ) : null}
          </div>
          <div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resolveBackendUrl(ph.secondary_url)}
              alt={ph.secondary_caption || caption}
              className="max-h-[300px] w-full object-contain"
            />
            {ph.secondary_caption ? (
              <figcaption className="mt-1.5 text-center text-[10px] font-semibold text-[#1D1D1F]">
                {ph.secondary_caption}
              </figcaption>
            ) : null}
          </div>
        </div>
        {!ph.secondary_caption ? (
          <figcaption className="mt-2 text-center text-[10px] font-semibold text-[#1D1D1F]">
            {caption}
          </figcaption>
        ) : null}
      </figure>
    );
  }

  if (hasSecondary && ph.secondary_url && layout === "stacked") {
    return (
      <figure id={ph.id} className="my-5 scroll-mt-4 space-y-2 text-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={resolveBackendUrl(ph.resolved_url)}
          alt={caption}
          className="mx-auto max-h-[280px] w-full object-contain"
        />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={resolveBackendUrl(ph.secondary_url)}
          alt={caption}
          className="mx-auto max-h-[280px] w-full object-contain"
        />
        <figcaption className="pt-1 text-center text-[10px] font-semibold text-[#1D1D1F]">
          {caption}
        </figcaption>
      </figure>
    );
  }

  return (
    <figure id={ph.id} className="my-5 scroll-mt-4 text-center">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={resolveBackendUrl(ph.resolved_url)}
        alt={caption}
        className="mx-auto max-h-[420px] w-full object-contain"
      />
      <figcaption className="mt-2 text-center text-[10px] font-semibold text-[#1D1D1F]">
        {caption}
      </figcaption>
    </figure>
  );
}

function TocLinkRow({
  href,
  label,
  pageNumber,
  bold = false,
  onJump,
}: {
  href: string;
  label: string;
  pageNumber: number | string;
  bold?: boolean;
  onJump: (targetId: string) => void;
}) {
  const targetId = href.replace(/^#/, "");
  return (
    <a
      href={href}
      onClick={(e) => {
        e.preventDefault();
        onJump(targetId);
      }}
      className="group flex items-baseline gap-2 py-1 text-[11px] text-[#1D1D1F] transition-colors hover:text-[#0066CC]"
    >
      <span className={bold ? "font-semibold" : ""}>{label}</span>
      <span className="flex-1 border-b border-dotted border-[#9CA3AF] group-hover:border-[#0066CC]" />
      <span className="font-mono text-[10.5px] tabular-nums text-[#4B5565] group-hover:text-[#0066CC]">
        {pageNumber}
      </span>
    </a>
  );
}

export function PaginatedPdfStage({
  project,
  isCompiling,
  onRefreshPdf,
  viewerMode: controlledMode,
  onViewerModeChange,
  hideToolbar = false,
}: PaginatedPdfStageProps) {
  const { pdfZoom, setPdfZoom } = useStudioStore();
  const [internalMode, setInternalMode] = React.useState<"a4_sheets" | "compiled_pdf">(
    "a4_sheets",
  );

  const viewerMode = controlledMode ?? internalMode;
  const setViewerMode = (m: "a4_sheets" | "compiled_pdf") => {
    if (onViewerModeChange) onViewerModeChange(m);
    else setInternalMode(m);
  };

  const scrollToTarget = (targetId: string) => {
    const el = document.getElementById(targetId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const ast = project.document_ast_json || {
    report_title: project.title,
    report_subtitle: project.subtitle || "",
    program_title: project.document_type || "",
    location_line: "",
    campaign_dates: "",
    abbreviations: [],
    sections: [],
  };
  const sections = ast.sections || [];
  const hasAbbreviations = Boolean(ast.abbreviations && ast.abbreviations.length > 0);
  const firstSectionPage = hasAbbreviations ? 5 : 4;
  const scale = pdfZoom / 100;

  const figureEntries = sections.flatMap((sec, sIdx) =>
    (sec.placeholders || [])
      .filter((f) => f.figure_number.startsWith("Figure"))
      .map((fig) => ({
        fig,
        pageNumber: firstSectionPage + sIdx,
      })),
  );
  const tableEntries = sections.flatMap((sec, sIdx) =>
    (sec.tables || []).map((tbl) => ({
      tbl,
      pageNumber: firstSectionPage + sIdx,
    })),
  );
  const appendixIdx = sections.findIndex((s) => s.category === "Appendices");

  const authRows = project.authorization_matrix_json || [];
  const preparedBy = authRows.find((r) => r.role.toLowerCase().includes("prepar"));
  const reviewedBy = authRows.find((r) => r.role.toLowerCase().includes("review"));
  const approvedList = authRows.filter((r) => r.role.toLowerCase().includes("approv"));
  const approvedBy1 = approvedList[0];
  const approvedBy2 = approvedList[1] || authRows.find((r) => r.role.toLowerCase().includes("client"));

  return (
    <div className="relative flex h-full flex-col bg-[#F5F5F7]">
      {!hideToolbar ? (
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-[#E5E5EA] bg-white px-5 py-1.5">
          <div className="flex items-center gap-1 rounded-[8px] border border-[#E5E5EA] bg-[#F5F5F7] p-0.5">
            <button
              type="button"
              onClick={() => setViewerMode("a4_sheets")}
              className={`h-7 rounded-[6px] px-3 text-[12.5px] font-medium transition-colors ${
                viewerMode === "a4_sheets"
                  ? "bg-[#1D1D1F] text-white"
                  : "text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
            >
              Paginated A4 preview
            </button>
            <button
              type="button"
              onClick={() => setViewerMode("compiled_pdf")}
              className={`h-7 rounded-[6px] px-3 text-[12.5px] font-medium transition-colors ${
                viewerMode === "compiled_pdf"
                  ? "bg-[#1D1D1F] text-white"
                  : "text-[#6E6E73] hover:text-[#1D1D1F]"
              }`}
            >
              Compiled PDF ({project.attachments?.length ?? 0} merged)
            </button>
          </div>

          <button
            type="button"
            onClick={onRefreshPdf}
            disabled={isCompiling}
            className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-[7px] bg-[#1D1D1F] px-3 text-[12.5px] font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            {isCompiling ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : (
              <RefreshCw className="size-3.5" strokeWidth={1.5} />
            )}
            <span>{isCompiling ? "Compiling" : "Recompile PDF"}</span>
          </button>
        </div>
      ) : null}

      {isCompiling ? (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center bg-[#F5F5F7]/75 backdrop-blur-sm">
          <div className="inline-flex items-center gap-2.5 rounded-[10px] border border-[#E0E0E0] bg-white px-4 py-2.5 text-[13.5px] font-medium text-[#1D1D1F]">
            <Loader2 className="size-4 animate-spin text-[#0066CC]" />
            <span>Updating paginated A4 PDF and merging attachments</span>
          </div>
        </div>
      ) : null}

      {viewerMode === "compiled_pdf" && project.compiled_pdf_url ? (
        <div className="flex-1 p-4">
          <div className="mx-auto h-full max-w-[840px] overflow-hidden bg-white shadow-artifact">
            <iframe
              key={project.compiled_pdf_url}
              src={resolveBackendUrl(project.compiled_pdf_url)}
              title="Compiled Master PDF"
              className="h-full w-full border-0"
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
          <div
            className="mx-auto flex origin-top flex-col items-center gap-6 transition-transform duration-150"
            style={{ transform: `scale(${scale})`, width: "100%" }}
          >
            {/* PAGE 1: AUTHENTIC FULL-PAGE COVER TABLE */}
            <article className="w-full max-w-[780px] bg-white p-9 text-[#1D1D1F] shadow-artifact">
              <div className="flex min-h-[980px] flex-col justify-between border border-[#1D1D1F]">
                <div>
                  <div className="[&_table]:border-0 [&_td]:border-t-0 [&_td:first-child]:border-l-0 [&_td:last-child]:border-r-0">
                    <CorporateRunningHeader project={project} />
                  </div>

                  <div className="border-b border-[#1D1D1F] px-8 py-28 text-center">
                    {ast.program_title ? (
                      <div className="text-[20px] font-semibold text-[#1D1D1F]">
                        {ast.program_title}
                      </div>
                    ) : null}
                    <div className="mt-10 text-[28px] font-bold tracking-[-0.02em] text-[#1D1D1F]">
                      {project.title}
                    </div>
                    {(ast.report_subtitle || project.subtitle) ? (
                      <div className="mt-3 text-[21px] font-semibold text-[#1D1D1F]">
                        {ast.report_subtitle || project.subtitle}
                      </div>
                    ) : null}
                  </div>

                  <div className="border-b border-[#1D1D1F] py-5 text-center text-[15px] font-semibold">
                    Revision: {project.revision_number}
                  </div>

                  <div className="border-b border-[#1D1D1F] py-5 text-center text-[13px] font-semibold leading-relaxed">
                    <div>
                      {project.client_name || "Client"} Document Ref.{" "}
                      <span className="font-mono">
                        {project.client_ref_code || "Pending"}
                      </span>
                    </div>
                    <div>
                      {project.contractor_name || "Contractor"} Document Ref.{" "}
                      <span className="font-mono">
                        {project.contractor_ref_code || "Pending"}
                      </span>
                    </div>
                  </div>

                  <div className="border-b border-[#1D1D1F] px-4 py-4 text-[10px] leading-relaxed text-[#1D1D1F]">
                    This document is proprietary and confidential. Copyright is vested in {project.contractor_name || "the Contractor"}. All rights reserved.
                    Neither the whole nor any part of this document may be disclosed to any third party nor reproduced, stored in any retrieval
                    system, or transmitted in any form nor by any means without the prior written consent of the copyright owner.
                  </div>
                </div>

                <table className="w-full border-collapse text-[10.5px]">
                  <tbody>
                    <tr>
                      <td className="h-6 border-r border-b border-[#1D1D1F]" />
                      <td className="border-r border-b border-[#1D1D1F]" />
                      <td className="border-r border-b border-[#1D1D1F]" />
                      <td className="border-r border-b border-[#1D1D1F]" />
                      <td className="border-r border-b border-[#1D1D1F]" />
                      <td className="border-b border-[#1D1D1F]" />
                    </tr>
                    {(project.revision_history_json || []).map((rev, idx) => (
                      <tr key={idx}>
                        <td className="w-[10%] border-r border-b border-[#1D1D1F] p-1.5 text-center font-mono">{rev.rev}</td>
                        <td className="w-[14%] border-r border-b border-[#1D1D1F] p-1.5 text-center font-mono">{rev.date}</td>
                        <td className="w-[37%] border-r border-b border-[#1D1D1F] p-1.5 text-center">{rev.description}</td>
                        <td className="w-[13%] border-r border-b border-[#1D1D1F] p-1.5 text-center">{rev.prepared_by}</td>
                        <td className="w-[13%] border-r border-b border-[#1D1D1F] p-1.5 text-center">{rev.checked_by}</td>
                        <td className="w-[13%] border-b border-[#1D1D1F] p-1.5 text-center">{rev.approved_by}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-[#F5F5F7] font-semibold">
                      <td className="border-r border-[#1D1D1F] p-1.5 text-center">Rev</td>
                      <td className="border-r border-[#1D1D1F] p-1.5 text-center">Date</td>
                      <td className="border-r border-[#1D1D1F] p-1.5 text-center">Reason for Revision</td>
                      <td className="border-r border-[#1D1D1F] p-1.5 text-center">Prepared</td>
                      <td className="border-r border-[#1D1D1F] p-1.5 text-center">Checked</td>
                      <td className="p-1.5 text-center">Approved</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </article>

            {/* PAGE 2: DOCUMENT AUTHORISATION AND DISTRIBUTION */}
            <article className="flex min-h-[1040px] w-full max-w-[780px] flex-col justify-between bg-white p-9 text-[#1D1D1F] shadow-artifact">
              <div>
                <CorporateRunningHeader project={project} />

                <h3 className="mt-7 text-[13px] font-bold uppercase text-[#1D1D1F]">
                  DOCUMENT AUTHORISATION AND DISTRIBUTION
                </h3>

                <table className="mt-2 w-full border-collapse border border-[#1D1D1F] text-[10.5px]">
                  <thead className="bg-[#F5F5F7]">
                    <tr>
                      <th colSpan={4} className="border border-[#1D1D1F] p-2 text-left font-bold">
                        Document Authorisation and Distribution
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="w-[24%] border border-[#1D1D1F] p-2 font-semibold">Contractor</td>
                      <td colSpan={3} className="border border-[#1D1D1F] p-2 font-semibold">{project.contractor_name || "Pending"}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Client</td>
                      <td colSpan={3} className="border border-[#1D1D1F] p-2">{project.client_name || "Pending"}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">FAO</td>
                      <td colSpan={3} className="border border-[#1D1D1F] p-2">{project.fao_text || "Pending"}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Document Ref.</td>
                      <td colSpan={3} className="border border-[#1D1D1F] p-2 font-mono">{project.contractor_ref_code || "-"}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Title</td>
                      <td colSpan={3} className="border border-[#1D1D1F] p-2">
                        {project.title}{project.subtitle ? ` - ${project.subtitle}` : ""}
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Author</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">
                        {preparedBy?.name || "Pending"}{preparedBy?.email ? `, ${preparedBy.email}` : ""}
                      </td>
                      <td className="w-[24%] border border-[#1D1D1F] p-2 font-mono">
                        Date: {preparedBy?.date || "Pending"}
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Checked</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">
                        {reviewedBy?.name || "Pending"}{reviewedBy?.email ? `; ${reviewedBy.email}` : ""}
                      </td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">
                        Date: {reviewedBy?.date || "Pending"}
                      </td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Approved</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">
                        {approvedBy1?.name || "Pending"}{approvedBy1?.email ? `; ${approvedBy1.email}` : ""}
                      </td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">
                        Date: {approvedBy1?.date || "Pending"}
                      </td>
                    </tr>
                    <tr className="bg-[#F5F5F7] font-semibold">
                      <td className="border border-[#1D1D1F] p-2"></td>
                      <td className="border border-[#1D1D1F] p-2">DOCUMENT</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">ISSUED TO</td>
                    </tr>
                    <tr>
                      <td rowSpan={2} className="border border-[#1D1D1F] p-2 font-semibold">Authorised Copies</td>
                      <td className="border border-[#1D1D1F] p-2">Original</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">{project.client_name || "Client"}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2">Copy No. 1</td>
                      <td colSpan={2} className="border border-[#1D1D1F] p-2">{project.contractor_name || "Contractor"}</td>
                    </tr>
                  </tbody>
                </table>

                <p className="mt-7 text-[11px] text-[#1D1D1F]">
                  This document has been approved and authorised by the authorities whose signatures appear below:
                </p>

                <table className="mt-2 w-full border-collapse border border-[#1D1D1F] text-[10px]">
                  <thead className="bg-[#F5F5F7]">
                    <tr>
                      <th className="w-[16%] border border-[#1D1D1F] p-2 text-left"></th>
                      <th className="w-[21%] border border-[#1D1D1F] p-2 text-left">Prepared By</th>
                      <th className="w-[21%] border border-[#1D1D1F] p-2 text-left">Reviewed By</th>
                      <th className="w-[21%] border border-[#1D1D1F] p-2 text-left">Approved By</th>
                      <th className="w-[21%] border border-[#1D1D1F] p-2 text-left">Approved By</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Signature</td>
                      <td className="border border-[#1D1D1F] p-2">
                        {preparedBy?.signature_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={resolveBackendUrl(preparedBy.signature_url)}
                            alt="Prepared By Signature"
                            className="h-12 w-auto object-contain"
                          />
                        ) : null}
                      </td>
                      <td className="border border-[#1D1D1F] p-2" />
                      <td className="border border-[#1D1D1F] p-2" />
                      <td className="border border-[#1D1D1F] p-2" />
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Name</td>
                      <td className="border border-[#1D1D1F] p-2">{preparedBy?.name || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{reviewedBy?.name || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{approvedBy1?.name || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{approvedBy2?.name || ""}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Designation</td>
                      <td className="border border-[#1D1D1F] p-2">{preparedBy?.designation || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{reviewedBy?.designation || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{approvedBy1?.designation || ""}</td>
                      <td className="border border-[#1D1D1F] p-2">{approvedBy2?.designation || ""}</td>
                    </tr>
                    <tr>
                      <td className="border border-[#1D1D1F] p-2 font-semibold">Date</td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">{preparedBy?.date || ""}</td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">{reviewedBy?.date || ""}</td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">{approvedBy1?.date || ""}</td>
                      <td className="border border-[#1D1D1F] p-2 font-mono">{approvedBy2?.date || ""}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-8 flex items-center justify-between text-[9.5px] text-[#6E6E73]">
                <span>{project.contractor_ref_code || project.id}</span>
                <span className="font-mono">Page 2</span>
              </div>
            </article>

            {/* PAGE 3: INTERACTIVE CLICKABLE TOC, LIST OF FIGURES, TABLES & APPENDICES */}
            <article className="flex min-h-[1040px] w-full max-w-[780px] flex-col justify-between bg-white p-9 text-[#1D1D1F] shadow-artifact">
              <div>
                <CorporateRunningHeader project={project} />

                <h3 className="mt-7 text-[13px] font-bold text-[#1D1D1F]">
                  TABLE OF CONTENTS
                </h3>
                <div className="mt-2">
                  {hasAbbreviations ? (
                    <TocLinkRow
                      href="#pdf-abbreviations"
                      label="ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS"
                      pageNumber={4}
                      bold
                      onJump={scrollToTarget}
                    />
                  ) : null}
                  {sections.map((sec, idx) => (
                    <TocLinkRow
                      key={sec.id}
                      href={`#pdf-${sec.id}`}
                      label={`${sec.section_number} ${sec.title}`}
                      pageNumber={firstSectionPage + idx}
                      bold
                      onJump={scrollToTarget}
                    />
                  ))}
                </div>

                {figureEntries.length > 0 ? (
                  <div className="mt-6">
                    <h3 className="text-[12.5px] font-bold text-[#1D1D1F]">
                      LIST OF FIGURES
                    </h3>
                    <div className="mt-1.5">
                      {figureEntries.map(({ fig, pageNumber }) => (
                        <TocLinkRow
                          key={fig.id}
                          href={`#${fig.id}`}
                          label={fig.caption || `${fig.figure_number}: ${fig.prompt}`}
                          pageNumber={pageNumber}
                          onJump={scrollToTarget}
                        />
                      ))}
                    </div>
                  </div>
                ) : null}

                {tableEntries.length > 0 ? (
                  <div className="mt-6">
                    <h3 className="text-[12.5px] font-bold text-[#1D1D1F]">
                      LIST OF TABLES
                    </h3>
                    <div className="mt-1.5">
                      {tableEntries.map(({ tbl, pageNumber }, idx) => (
                        <TocLinkRow
                          key={tbl.id}
                          href={`#${tbl.id}`}
                          label={`${tbl.table_number || `Table ${idx + 1}`}: ${tbl.title}`}
                          pageNumber={pageNumber}
                          onJump={scrollToTarget}
                        />
                      ))}
                    </div>
                  </div>
                ) : null}

                {appendixIdx >= 0 ? (
                  <div className="mt-6">
                    <h3 className="text-[12.5px] font-bold text-[#1D1D1F]">
                      LIST OF APPENDICES
                    </h3>
                    <div className="mt-1.5">
                      <TocLinkRow
                        href={`#pdf-${sections[appendixIdx].id}`}
                        label="Appendix - A : Field Pictures"
                        pageNumber={firstSectionPage + appendixIdx}
                        onJump={scrollToTarget}
                      />
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mt-8 flex items-center justify-between text-[9.5px] text-[#6E6E73]">
                <span>{project.contractor_ref_code || project.id}</span>
                <span className="font-mono">Page 3</span>
              </div>
            </article>

            {/* PAGE 4: ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS */}
            {hasAbbreviations ? (
              <article
                id="pdf-abbreviations"
                className="flex min-h-[1040px] w-full max-w-[780px] scroll-mt-4 flex-col justify-between bg-white p-9 text-[#1D1D1F] shadow-artifact"
              >
                <div>
                  <CorporateRunningHeader project={project} />

                  <h3 className="mt-7 text-[13px] font-bold text-[#1D1D1F]">
                    ABBREVIATIONS, ACRONYMS AND GLOSSARY OF TERMS
                  </h3>
                  <p className="mt-2 text-[11px] text-[#1D1D1F]">
                    A list of abbreviations that have been used within the main body of the report as follows:
                  </p>
                  <table className="mt-3 w-full border-collapse border border-[#1D1D1F] text-[10px]">
                    <thead className="bg-[#F5F5F7]">
                      <tr>
                        <th className="w-[28%] border border-[#1D1D1F] p-1.5 text-left font-bold">Acronym</th>
                        <th className="border border-[#1D1D1F] p-1.5 text-left font-bold">Definition</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ast.abbreviations.map((ab, idx) => (
                        <tr key={idx}>
                          <td className="border border-[#6B7280] p-1.5 font-mono font-semibold">{ab.term}</td>
                          <td className="border border-[#6B7280] p-1.5">{ab.definition}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-8 flex items-center justify-between text-[9.5px] text-[#6E6E73]">
                  <span>{project.contractor_ref_code || project.id}</span>
                  <span className="font-mono">Page 4</span>
                </div>
              </article>
            ) : null}

            {/* PAGES 5+: REPORT SECTIONS, MULTI-HEADER TABLES & UNBOXED LARGE FIGURES */}
            {sections.map((sec, idx) => (
              <article
                key={sec.id}
                id={`pdf-${sec.id}`}
                className="flex min-h-[1040px] w-full max-w-[780px] scroll-mt-4 flex-col justify-between bg-white p-9 text-[#1D1D1F] shadow-artifact"
              >
                <div>
                  <CorporateRunningHeader project={project} />

                  <h2 className="mt-6 border-b border-[#1D1D1F] pb-1.5 text-[14px] font-bold text-[#1D1D1F]">
                    {sec.section_number} {sec.title}
                  </h2>

                  <div
                    className="mt-3 space-y-2.5 text-[11.5px] leading-[1.6] text-[#1D1D1F]"
                    dangerouslySetInnerHTML={{ __html: sec.html_content }}
                  />

                  {(sec.tables || []).map((tbl) => (
                    <A4TableRenderer key={tbl.id} tbl={tbl} />
                  ))}

                  {sec.placeholders && sec.placeholders.length > 0 ? (
                    <div className="mt-4 space-y-4">
                      {sec.placeholders.map((ph) => (
                        <UnboxedA4Figure key={ph.id} ph={ph} />
                      ))}
                    </div>
                  ) : null}

                  {sec.category === "Appendices" &&
                  project.attachments &&
                  project.attachments.length > 0 ? (
                    <div className="mt-6 space-y-2">
                      <div className="text-[11px] font-semibold text-[#1D1D1F]">
                        Appended External Laboratory &amp; Log Packages
                      </div>
                      {project.attachments.map((att) => (
                        <div
                          key={att.id}
                          className="flex items-center justify-between border border-[#D1D5DB] px-3 py-2 text-[10.5px]"
                        >
                          <span className="flex items-center gap-2 font-medium">
                            <FileText className="size-3.5 text-[#0066CC]" strokeWidth={1.5} />
                            {att.attachment_number}: {att.title}
                          </span>
                          <span className="font-mono text-[#6E6E73]">
                            {att.page_count} page(s) appended
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>

                <div className="mt-8 flex items-center justify-between text-[9.5px] text-[#6E6E73]">
                  <span>{project.contractor_ref_code || project.id}</span>
                  <span className="font-mono">Page {firstSectionPage + idx}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {/* Floating Zoom Controls */}
      {viewerMode === "a4_sheets" ? (
        <div className="absolute bottom-5 right-5 z-10 flex items-center gap-1 rounded-[10px] border border-[#E5E5EA] bg-white/95 p-1 shadow-artifact backdrop-blur-md">
          <Button
            variant="icon-circular"
            size="sm"
            aria-label="Zoom out"
            onClick={() => setPdfZoom(pdfZoom - 10)}
            className="border-0 shadow-none"
          >
            <Minus className="size-4" strokeWidth={1.5} />
          </Button>
          <button
            type="button"
            onClick={() => setPdfZoom(100)}
            className="cupertino-press h-8 rounded-[7px] px-2.5 font-mono text-[12px] font-medium text-[#1D1D1F] hover:bg-[#F5F5F7]"
          >
            {pdfZoom}%
          </button>
          <Button
            variant="icon-circular"
            size="sm"
            aria-label="Zoom in"
            onClick={() => setPdfZoom(pdfZoom + 10)}
            className="border-0 shadow-none"
          >
            <Plus className="size-4" strokeWidth={1.5} />
          </Button>
          <Button
            variant="icon-circular"
            size="sm"
            aria-label="Reset zoom"
            onClick={() => setPdfZoom(100)}
            className="border-0 shadow-none"
          >
            <RotateCcw className="size-3.5" strokeWidth={1.5} />
          </Button>
        </div>
      ) : null}
    </div>
  );
}
