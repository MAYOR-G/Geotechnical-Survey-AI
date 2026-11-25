"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { ExternalLink, FileText, Globe, Mail, MessageSquare, Ticket, Database } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AnswerSource } from "./cited-answer";

interface MarkdownProps {
  content: string;
  streaming?: boolean;
  citations?: AnswerSource[];
  className?: string;
}

function SourceKindBadge({ kind }: { kind: AnswerSource["kind"] }) {
  const Icon =
    kind === "file"
      ? FileText
      : kind === "web"
        ? Globe
        : kind === "chat"
          ? MessageSquare
          : kind === "ticket"
            ? Ticket
            : kind === "email"
              ? Mail
              : kind === "vault"
                ? Database
                : FileText;
  return <Icon className="size-3.5 text-[#0066CC]" strokeWidth={1.6} />;
}

function CitationPill({
  index,
  source,
}: {
  index: number;
  source?: AnswerSource;
}) {
  if (!source) {
    return (
      <span className="mx-0.5 inline-flex items-center rounded-[5px] bg-[#F5F5F7] px-1.5 py-0.5 font-mono text-[11px] font-semibold text-[#0066CC] border border-[#E0E0E0]">
        [{index}]
      </span>
    );
  }

  return (
    <PopoverPrimitive.Root>
      <PopoverPrimitive.Trigger asChild>
        <button
          type="button"
          className="cupertino-press mx-0.5 inline-flex items-center rounded-[5px] bg-[#F0F7FF] px-1.5 py-0.5 font-mono text-[11px] font-semibold text-[#0066CC] border border-[#B8D9FF] hover:bg-[#0066CC] hover:text-white transition-colors align-baseline"
          aria-label={`Citation ${index}: ${source.title}`}
        >
          {index}
        </button>
      </PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          side="top"
          align="center"
          sideOffset={6}
          className="z-50 w-[320px] rounded-[14px] border border-[#E0E0E0] bg-white p-3.5 shadow-artifact text-left"
        >
          <div className="flex items-center justify-between gap-2 text-[11.5px] text-[#7A7A7A]">
            <span className="inline-flex items-center gap-1.5 font-semibold text-[#1D1D1F]">
              <SourceKindBadge kind={source.kind} />
              <span>{source.site}</span>
            </span>
            {source.meta ? <span>{source.meta}</span> : null}
          </div>
          <div className="mt-1.5 text-[13.5px] font-semibold text-[#1D1D1F] leading-snug">
            {source.title}
          </div>
          <p className="mt-1.5 text-[12.5px] leading-relaxed text-[#333333] line-clamp-4">
            {source.snippet}
          </p>
          {source.url ? (
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="mt-2.5 inline-flex items-center gap-1 text-[12px] font-semibold text-[#0066CC] hover:underline"
            >
              <span>Open source</span>
              <ExternalLink className="size-3" />
            </a>
          ) : null}
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}

function renderInline(
  text: string,
  citations?: AnswerSource[],
): React.ReactNode[] {
  // Split inline code, bold, italic, links, and citation brackets [1]
  const tokenRegex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[(\d+)\]|\[[^\]]+\]\([^)]+\))/g;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let keyCounter = 0;

  while ((match = tokenRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    keyCounter += 1;

    if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code
          key={keyCounter}
          className="rounded-[5px] bg-[#F5F5F7] px-1.5 py-0.5 font-mono text-[12.5px] text-[#1D1D1F] border border-[#E0E0E0]"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={keyCounter} className="font-semibold text-[#1D1D1F]">
          {renderInline(token.slice(2, -2), citations)}
        </strong>,
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      parts.push(
        <em key={keyCounter} className="italic">
          {renderInline(token.slice(1, -1), citations)}
        </em>,
      );
    } else if (match[2]) {
      const idx = parseInt(match[2], 10);
      const source = citations && idx >= 1 ? citations[idx - 1] : undefined;
      parts.push(<CitationPill key={keyCounter} index={idx} source={source} />);
    } else {
      const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token);
      if (linkMatch) {
        parts.push(
          <a
            key={keyCounter}
            href={linkMatch[2]}
            target="_blank"
            rel="noreferrer"
            className="text-[#0066CC] hover:underline"
          >
            {linkMatch[1]}
          </a>,
        );
      } else {
        parts.push(token);
      }
    }
    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function parseTable(lines: string[]) {
  const splitRow = (line: string) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());

  const headers = splitRow(lines[0]);
  const alignments = splitRow(lines[1]).map((sep) => {
    if (sep.startsWith(":") && sep.endsWith(":")) return "center";
    if (sep.endsWith(":")) return "right";
    return "left";
  });
  const rows = lines.slice(2).map(splitRow);
  return { headers, alignments, rows };
}

export function Markdown({
  content,
  streaming = false,
  citations,
  className,
}: MarkdownProps) {
  const lines = content.split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push(
        <div
          key={`code-${i}`}
          className="my-3 overflow-hidden rounded-[12px] border border-[#38383A] bg-[#272729] text-white"
        >
          {lang ? (
            <div className="border-b border-[#272D3D] bg-[#11141C] px-3 py-1.5 font-mono text-[12px] text-[#A3A9B8]">
              {lang}
            </div>
          ) : null}
          <pre className="overflow-x-auto p-3.5 font-mono text-[12.5px] leading-relaxed text-[#F5F5F7]">
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>,
      );
      continue;
    }

    // Markdown table
    if (
      line.includes("|") &&
      i + 1 < lines.length &&
      /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(lines[i + 1])
    ) {
      const tableLines = [line, lines[i + 1]];
      i += 2;
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        tableLines.push(lines[i]);
        i += 1;
      }
      const { headers, alignments, rows } = parseTable(tableLines);
      blocks.push(
        <div
          key={`tbl-${i}`}
          className="my-3.5 overflow-x-auto rounded-[12px] border border-[#E4E4E7] bg-white"
        >
          <table className="w-full border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-[#E4E4E7] bg-[#FAFAFA]">
                {headers.map((head, idx) => (
                  <th
                    key={idx}
                    className="whitespace-nowrap px-4 py-2.5 text-[12.5px] font-medium text-[#71717A]"
                    style={{
                      textAlign:
                        (alignments[idx] as "left" | "right" | "center") || "left",
                    }}
                  >
                    {renderInline(head, citations)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rIdx) => (
                <tr
                  key={rIdx}
                  className="border-b border-[#F1F1F3] last:border-b-0"
                >
                  {headers.map((_, cIdx) => (
                    <td
                      key={cIdx}
                      className="px-4 py-2.5 text-[13.5px] text-[#18181B] tabular-nums"
                      style={{
                        textAlign:
                          (alignments[cIdx] as "left" | "right" | "center") ||
                          "left",
                      }}
                    >
                      {renderInline(row[cIdx] ?? "", citations)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // Headings
    const headingMatch = /^(#{1,4})\s+(.+)$/.exec(line);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      const headingClass =
        level === 1
          ? "mt-5 mb-2 text-[20px] font-semibold tracking-[-0.02em] text-[#1D1D1F]"
          : level === 2
            ? "mt-4 mb-1.5 text-[17px] font-semibold tracking-[-0.015em] text-[#1D1D1F]"
            : "mt-3 mb-1 text-[15px] font-semibold text-[#333333]";
      blocks.push(
        <div key={`h-${i}`} className={headingClass}>
          {renderInline(text, citations)}
        </div>,
      );
      i += 1;
      continue;
    }

    // Unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ""));
        i += 1;
      }
      blocks.push(
        <ul
          key={`ul-${i}`}
          className="my-2.5 list-disc space-y-1.5 pl-5 text-[15px] leading-[1.6] text-[#1D1D1F]"
        >
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, citations)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // Ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ""));
        i += 1;
      }
      blocks.push(
        <ol
          key={`ol-${i}`}
          className="my-2.5 list-decimal space-y-1.5 pl-5 text-[15px] leading-[1.6] text-[#1D1D1F]"
        >
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, citations)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    // Blank line
    if (line.trim() === "") {
      i += 1;
      continue;
    }

    // Paragraph (collect consecutive non-empty non-special lines)
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].trim().startsWith("```") &&
      !/^(#{1,4})\s+/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !(
        lines[i].includes("|") &&
        i + 1 < lines.length &&
        /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(lines[i + 1])
      )
    ) {
      paraLines.push(lines[i]);
      i += 1;
    }

    blocks.push(
      <p
        key={`p-${i}`}
        className="my-2 text-[15px] leading-[1.65] text-[#1D1D1F]"
      >
        {renderInline(paraLines.join(" "), citations)}
      </p>,
    );
  }

  return (
    <div className={cn("text-[#1D1D1F]", className)}>
      {blocks}
      {streaming ? (
        <span
          className="ml-1 inline-block h-4 w-1.5 animate-pulse rounded-full bg-[#0066CC] align-middle"
          aria-hidden="true"
        />
      ) : null}
    </div>
  );
}
