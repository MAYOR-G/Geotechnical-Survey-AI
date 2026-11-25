"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import {
  Check,
  Copy,
  Database,
  ExternalLink,
  FilePlus2,
  FileText,
  Globe,
  Loader2,
  RotateCcw,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { cn, formatDurationMs } from "@/lib/utils";
import { Markdown } from "./ai-markdown";
import { Tip, actionButton } from "./ai-ui";

export type AnswerSourceKind =
  | "doc"
  | "file"
  | "chat"
  | "ticket"
  | "email"
  | "web"
  | "vault";

export interface AnswerSource {
  kind: AnswerSourceKind;
  site: string;
  label?: string;
  title: string;
  meta?: string;
  snippet: string;
  url?: string;
}

export type CitedAnswerStatus = "searching" | "reading" | "streaming" | "done";

interface CitedAnswerProps {
  question?: string;
  statusText?: string;
  status: CitedAnswerStatus;
  sources: AnswerSource[];
  content: string;
  duration?: number;
  feedback?: "up" | "down" | null;
  onFeedback?: (value: "up" | "down") => void;
  onRetry?: () => void;
  projects?: Array<{ id: string; title: string }>;
  onInsertToProject?: (
    content: string,
    sources: AnswerSource[],
    projectId?: string,
  ) => void;
  className?: string;
}

function SourceIcon({ kind }: { kind: AnswerSourceKind }) {
  const Icon =
    kind === "web"
      ? Globe
      : kind === "vault"
        ? Database
        : FileText;
  return <Icon className="size-3 text-[#0066CC] shrink-0" strokeWidth={1.6} />;
}

export function CitedAnswer({
  question,
  statusText = "Searching Knowledge Vault and external technical standards...",
  status,
  sources,
  content,
  duration,
  feedback,
  onFeedback,
  onRetry,
  projects,
  onInsertToProject,
  className,
}: CitedAnswerProps) {
  const [copied, setCopied] = React.useState(false);
  const [pickerOpen, setPickerOpen] = React.useState(false);

  const handleCopy = () => {
    void navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className={cn("flex w-full flex-col bg-transparent font-sans text-[#1D1D1F]", className)}>
      {question ? (
        <div className="mb-5 max-w-[85%] self-end rounded-[18px] bg-[#F5F5F7] px-4 py-2.5 text-[15px] leading-[1.6] text-[#1D1D1F]">
          {question}
        </div>
      ) : null}

      {/* Subtle frameless source pills row */}
      {sources.length > 0 ? (
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          {sources.map((src, idx) => {
            const pillInner = (
              <>
                <span className="font-mono text-[11px] font-semibold text-[#0066CC]">
                  [{idx + 1}]
                </span>
                <SourceIcon kind={src.kind} />
                <span className="max-w-[180px] truncate text-[#333333]">
                  {src.kind === "vault" ? src.title : src.site}
                </span>
                {src.url ? (
                  <ExternalLink className="size-2.5 text-[#7A7A7A]" strokeWidth={1.5} />
                ) : null}
              </>
            );
            return src.url ? (
              <a
                key={`${src.title}-${idx}`}
                href={src.url}
                target="_blank"
                rel="noreferrer"
                title={src.title}
                className="inline-flex h-6 items-center gap-1.5 rounded-full bg-[#F5F5F7] px-2.5 text-[11.5px] transition-colors hover:bg-[#F0F7FF] hover:text-[#0066CC]"
              >
                {pillInner}
              </a>
            ) : (
              <span
                key={`${src.title}-${idx}`}
                title={`${src.title}: ${src.snippet}`}
                className="inline-flex h-6 items-center gap-1.5 rounded-full bg-[#F5F5F7] px-2.5 text-[11.5px]"
              >
                {pillInner}
              </span>
            );
          })}
          {status === "done" && duration !== undefined ? (
            <span className="ml-1 font-mono text-[11.5px] tabular-nums text-[#7A7A7A]">
              · {formatDurationMs(duration)}
            </span>
          ) : null}
        </div>
      ) : status !== "done" ? (
        <div className="mb-2 flex items-center gap-2 text-[13px] text-[#7A7A7A]">
          <Loader2 className="size-3.5 animate-spin text-[#0066CC]" strokeWidth={1.75} />
          <span>{statusText}</span>
        </div>
      ) : null}

      {/* Pure unboxed AI markdown prose directly on #FFFFFF */}
      {content ? (
        <div className="py-0.5 text-[16px] leading-[1.6] text-[#1D1D1F]">
          <Markdown
            content={content}
            streaming={status === "streaming"}
            citations={sources}
          />
        </div>
      ) : null}

      {status === "done" && content ? (
        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2">
          <div className="-ml-1 flex items-center gap-1">
            <Tip label={copied ? "Copied" : "Copy answer"}>
              <button
                type="button"
                aria-label="Copy answer"
                onClick={handleCopy}
                className={actionButton}
              >
                {copied ? (
                  <Check className="size-3.5 text-[#106831]" strokeWidth={1.5} />
                ) : (
                  <Copy className="size-3.5" strokeWidth={1.5} />
                )}
              </button>
            </Tip>
            {onFeedback ? (
              <>
                <Tip label="Helpful">
                  <button
                    type="button"
                    aria-label="Helpful"
                    onClick={() => onFeedback("up")}
                    className={cn(
                      actionButton,
                      feedback === "up" && "bg-[#F2FAF5] text-[#106831]",
                    )}
                  >
                    <ThumbsUp className="size-3.5" strokeWidth={1.5} />
                  </button>
                </Tip>
                <Tip label="Needs refinement">
                  <button
                    type="button"
                    aria-label="Needs refinement"
                    onClick={() => onFeedback("down")}
                    className={cn(
                      actionButton,
                      feedback === "down" && "bg-[#FFF2F2] text-[#C91919]",
                    )}
                  >
                    <ThumbsDown className="size-3.5" strokeWidth={1.5} />
                  </button>
                </Tip>
              </>
            ) : null}
            {onRetry ? (
              <Tip label="Run search again">
                <button
                  type="button"
                  aria-label="Run search again"
                  onClick={onRetry}
                  className={actionButton}
                >
                  <RotateCcw className="size-3.5" strokeWidth={1.5} />
                </button>
              </Tip>
            ) : null}
          </div>

          {onInsertToProject ? (
            projects && projects.length > 0 ? (
              <PopoverPrimitive.Root open={pickerOpen} onOpenChange={setPickerOpen}>
                <PopoverPrimitive.Trigger asChild>
                  <button
                    type="button"
                    className="cupertino-press inline-flex h-7 items-center gap-1.5 rounded-full border border-[#E0E0E0] bg-white px-3 text-[12px] text-[#333333] hover:border-[#0066CC] hover:text-[#0066CC]"
                  >
                    <FilePlus2 className="size-3.5" strokeWidth={1.5} />
                    <span>Send to Project</span>
                  </button>
                </PopoverPrimitive.Trigger>
                <PopoverPrimitive.Portal>
                  <PopoverPrimitive.Content
                    align="end"
                    sideOffset={6}
                    className="z-50 w-64 rounded-[14px] border border-[#E0E0E0] bg-white p-1.5"
                  >
                    <div className="px-2.5 py-1.5 text-[11px] font-semibold text-[#7A7A7A]">
                      Select target report
                    </div>
                    <div className="max-h-56 space-y-0.5 overflow-y-auto">
                      {projects.map((p) => (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => {
                            setPickerOpen(false);
                            onInsertToProject(content, sources, p.id);
                          }}
                          className="flex w-full items-center rounded-[8px] px-2.5 py-2 text-left text-[12.5px] text-[#1D1D1F] hover:bg-[#F5F5F7]"
                        >
                          <span className="truncate">{p.title}</span>
                        </button>
                      ))}
                    </div>
                  </PopoverPrimitive.Content>
                </PopoverPrimitive.Portal>
              </PopoverPrimitive.Root>
            ) : (
              <button
                type="button"
                onClick={() => onInsertToProject(content, sources)}
                className="cupertino-press inline-flex h-7 items-center gap-1.5 rounded-full border border-[#E0E0E0] bg-white px-3 text-[12px] text-[#333333] hover:border-[#0066CC] hover:text-[#0066CC]"
              >
                <FilePlus2 className="size-3.5" strokeWidth={1.5} />
                <span>Send to Project</span>
              </button>
            )
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
