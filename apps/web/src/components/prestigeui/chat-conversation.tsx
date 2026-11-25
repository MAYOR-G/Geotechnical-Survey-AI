"use client";

import * as React from "react";
import {
  Check,
  Copy,
  Eye,
  FileText,
  Loader2,
  Pencil,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Markdown } from "./ai-markdown";
import { ReasoningSteps, type ReasoningStep } from "./reasoning-steps";
import {
  CitedAnswer,
  type AnswerSource,
  type CitedAnswerStatus,
} from "./cited-answer";
import {
  PromptInput,
  type PromptAttachment,
  type PromptMessage,
} from "./prompt-input";
import { Tip, actionButton } from "./ai-ui";

export interface ChatArtifact {
  id: string;
  title: string;
  subtitle?: string;
  sectionCount?: number;
  revision?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  status?: "thinking" | "streaming" | "done" | "stopped" | "error";
  error?: string;
  createdAt: number;
  attachments?: PromptAttachment[];
  feedback?: "up" | "down" | null;
  steps?: ReasoningStep[];
  stepsStatus?: "running" | "done";
  stepsDuration?: number;
  sources?: AnswerSource[];
  citedStatus?: CitedAnswerStatus;
  artifact?: ChatArtifact;
}

interface ChatConversationProps {
  messages: ChatMessage[];
  onSubmit: (
    message: PromptMessage,
    ctx: { signal: AbortSignal },
  ) => void | Promise<void>;
  onStop?: () => void;
  onFeedback?: (id: string, value: "up" | "down") => void;
  onApproveStep?: (
    messageId: string,
    stepId: string,
    extraAnswer?: string,
  ) => void;
  onDenyStep?: (messageId: string, stepId: string) => void;
  onOpenArtifact?: (artifact: ChatArtifact, mode: "edit" | "preview") => void;
  projects?: Array<{ id: string; title: string }>;
  onInsertCitation?: (
    content: string,
    sources: AnswerSource[],
    projectId?: string,
  ) => void;
  quickPrompts?: string[];
  placeholder?: string;
  emptyTitle?: string;
  emptyState?: React.ReactNode;
  emptyAttachments?: PromptAttachment[];
  defaultPromptText?: string;
  maxWidthClass?: string;
  className?: string;
}

export function ChatConversation({
  messages,
  onSubmit,
  onStop,
  onFeedback,
  onApproveStep,
  onDenyStep,
  onOpenArtifact,
  projects,
  onInsertCitation,
  quickPrompts,
  placeholder,
  emptyTitle,
  emptyState,
  emptyAttachments,
  defaultPromptText,
  maxWidthClass = "max-w-[700px]",
  className,
}: ChatConversationProps) {
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const isStreaming = messages.some(
    (m) => m.status === "thinking" || m.status === "streaming",
  );

  React.useEffect(() => {
    if (messages.length > 1 || isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [
    messages.length,
    isStreaming,
    messages[messages.length - 1]?.content,
    messages[messages.length - 1]?.steps?.length,
  ]);

  if (messages.length === 0) {
    return (
      <div
        className={cn(
          "flex h-full flex-col items-center justify-center overflow-y-auto bg-white px-5 pb-10",
          className,
        )}
      >
        <div className={cn("w-full", maxWidthClass)}>
          <h2 className="mb-6 text-center text-[28px] font-semibold tracking-[-0.02em] text-[#1D1D1F] sm:text-[32px]">
            {emptyTitle ?? "What are we working on today?"}
          </h2>
          {emptyState ? (
            <div className="mb-5 text-center">{emptyState}</div>
          ) : null}
          <PromptInput
            onSubmit={onSubmit}
            onStop={onStop}
            isStreaming={isStreaming}
            quickPrompts={quickPrompts}
            placeholder={placeholder}
            defaultText={defaultPromptText}
            initialAttachments={emptyAttachments}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex h-full flex-col bg-white", className)}>
      <div className="flex-1 overflow-y-auto px-5 pb-8 pt-4 sm:px-8">
        <div className={cn("mx-auto flex w-full flex-col gap-7", maxWidthClass)}>
          {messages.map((msg) => {
            if (msg.role === "user") {
              return (
                <div key={msg.id} className="flex flex-col items-end gap-1.5">
                  {msg.attachments && msg.attachments.length > 0 ? (
                    <div className="flex flex-wrap justify-end gap-1.5">
                      {msg.attachments.map((att) => (
                        <span
                          key={att.id}
                          className="inline-flex h-7 items-center gap-1.5 rounded-[8px] border border-[#E0E0E0] bg-[#FAFAFC] px-2.5 text-[12px] text-[#333333]"
                        >
                          <FileText
                            className="size-3.5 text-[#0066CC]"
                            strokeWidth={1.5}
                          />
                          <span>{att.name}</span>
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="max-w-[80%] rounded-[20px] bg-[#F5F5F7] px-4 py-2.5 text-[15px] leading-[1.55] text-[#1D1D1F]">
                    {msg.content}
                  </div>
                </div>
              );
            }

            return (
              <div key={msg.id} className="flex flex-col gap-3 bg-transparent">
                {/* Frameless Vertical Reasoning Timeline */}
                {msg.steps && msg.steps.length > 0 ? (
                  <ReasoningSteps
                    steps={msg.steps}
                    status={
                      msg.stepsStatus ??
                      (msg.status === "thinking" || msg.status === "streaming"
                        ? "running"
                        : "done")
                    }
                    startedAt={msg.createdAt}
                    duration={msg.stepsDuration}
                    onApprove={(stepId, extra) =>
                      onApproveStep?.(msg.id, stepId, extra)
                    }
                    onDeny={(stepId) => onDenyStep?.(msg.id, stepId)}
                  />
                ) : null}

                {msg.status === "thinking" &&
                (!msg.steps || msg.steps.length === 0) &&
                !msg.content ? (
                  <div className="inline-flex items-center gap-2 text-[13.5px] text-[#7A7A7A]">
                    <Loader2
                      className="size-3.5 animate-spin text-[#0066CC]"
                      strokeWidth={1.5}
                    />
                    <span>Initializing engineering verification...</span>
                  </div>
                ) : null}

                {/* Unboxed Cited Answer or Unboxed Prose directly on #FFFFFF */}
                {msg.sources && msg.sources.length > 0 ? (
                  <CitedAnswer
                    status={
                      msg.citedStatus ??
                      (msg.status === "streaming" ? "streaming" : "done")
                    }
                    sources={msg.sources}
                    content={msg.content}
                    feedback={msg.feedback}
                    onFeedback={
                      onFeedback ? (val) => onFeedback(msg.id, val) : undefined
                    }
                    projects={projects}
                    onInsertToProject={onInsertCitation}
                  />
                ) : msg.content ? (
                  <div className="text-[16px] leading-[1.6] text-[#1D1D1F]">
                    <Markdown
                      content={msg.content}
                      streaming={msg.status === "streaming"}
                    />
                  </div>
                ) : null}

                {/* Deliverable Artifact Pill */}
                {msg.artifact ? (
                  <div className="mt-1 flex flex-wrap items-center justify-between gap-3 rounded-[18px] border border-[#E0E0E0] bg-[#FAFAFC] px-4 py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-[10px] border border-[#E0E0E0] bg-white text-[#0066CC]">
                        <FileText className="size-4" strokeWidth={1.5} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-[14px] font-semibold text-[#1D1D1F]">
                            {msg.artifact.title}
                          </span>
                          {msg.artifact.revision ? (
                            <span className="rounded-[5px] border border-[#E0E0E0] bg-white px-1.5 py-0.5 font-mono text-[11px] text-[#333333]">
                              {msg.artifact.revision}
                            </span>
                          ) : null}
                        </div>
                        <p className="truncate text-[12.5px] text-[#7A7A7A]">
                          {msg.artifact.subtitle ||
                            `${msg.artifact.sectionCount ?? 10} sections · A4 report ready`}
                        </p>
                      </div>
                    </div>

                    {onOpenArtifact ? (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => onOpenArtifact(msg.artifact!, "edit")}
                          className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-full bg-[#0066CC] px-3.5 text-[12.5px] text-white hover:bg-[#0071E3]"
                        >
                          <Pencil className="size-3.5" strokeWidth={1.5} />
                          <span>Block Editor</span>
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            onOpenArtifact(msg.artifact!, "preview")
                          }
                          className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-full border border-[#0066CC] bg-white px-3.5 text-[12.5px] text-[#0066CC] hover:bg-[#F0F7FF]"
                        >
                          <Eye className="size-3.5" strokeWidth={1.5} />
                          <span>Live A4 PDF</span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {msg.status === "error" && msg.error ? (
                  <div className="rounded-[12px] border border-[#F5B3B3] bg-[#FFF2F2] px-4 py-3 text-[13.5px] text-[#C91919]">
                    {msg.error}
                  </div>
                ) : null}

                {msg.status === "stopped" ? (
                  <span className="text-[12.5px] text-[#7A7A7A]">
                    Generation stopped by engineer
                  </span>
                ) : null}

                {(!msg.sources || msg.sources.length === 0) &&
                msg.status === "done" &&
                msg.content ? (
                  <div className="-ml-1 flex items-center gap-1">
                    <Tip label={copiedId === msg.id ? "Copied" : "Copy response"}>
                      <button
                        type="button"
                        onClick={() => {
                          void navigator.clipboard.writeText(msg.content);
                          setCopiedId(msg.id);
                          window.setTimeout(() => setCopiedId(null), 1500);
                        }}
                        className={actionButton}
                      >
                        {copiedId === msg.id ? (
                          <Check
                            className="size-3.5 text-[#106831]"
                            strokeWidth={1.5}
                          />
                        ) : (
                          <Copy className="size-3.5" strokeWidth={1.5} />
                        )}
                      </button>
                    </Tip>
                    {onFeedback ? (
                      <>
                        <Tip label="Good response">
                          <button
                            type="button"
                            onClick={() => onFeedback(msg.id, "up")}
                            className={cn(
                              actionButton,
                              msg.feedback === "up" &&
                                "bg-[#F2FAF5] text-[#106831]",
                            )}
                          >
                            <ThumbsUp className="size-3.5" strokeWidth={1.5} />
                          </button>
                        </Tip>
                        <Tip label="Needs work">
                          <button
                            type="button"
                            onClick={() => onFeedback(msg.id, "down")}
                            className={cn(
                              actionButton,
                              msg.feedback === "down" &&
                                "bg-[#FFF2F2] text-[#C91919]",
                            )}
                          >
                            <ThumbsDown
                              className="size-3.5"
                              strokeWidth={1.5}
                            />
                          </button>
                        </Tip>
                      </>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Sleek Bottom Input Bar on Pure White */}
      <div className="shrink-0 bg-white px-5 pb-4 pt-1 sm:px-8">
        <div className={cn("mx-auto w-full", maxWidthClass)}>
          <PromptInput
            onSubmit={onSubmit}
            onStop={onStop}
            isStreaming={isStreaming}
            placeholder={placeholder}
          />
        </div>
      </div>
    </div>
  );
}
