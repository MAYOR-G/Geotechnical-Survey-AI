"use client";

import * as React from "react";
import {
  AlertCircle,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  Cpu,
  Database,
  Globe,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  Wrench,
  X,
} from "lucide-react";
import { cn, formatDurationMs } from "@/lib/utils";
import { Markdown } from "./ai-markdown";

export type ReasoningStepKind =
  | "thought"
  | "query"
  | "read"
  | "search"
  | "verify"
  | "tool";
export type ReasoningStepStatus =
  | "running"
  | "done"
  | "error"
  | "approval"
  | "denied";

export interface ReasoningStep {
  id: string;
  kind: ReasoningStepKind;
  status: ReasoningStepStatus;
  title?: string;
  detail?: string;
  content?: string;
  icon?: React.ComponentType<{ className?: string; strokeWidth?: string | number }>;
  startedAt?: number;
  duration?: number;
  code?: { lang: string; text: string };
  output?: string;
  error?: string;
  results?: Array<{ title: string; site?: string; url?: string }>;
  approval?: {
    message: string;
    allowLabel?: string;
    denyLabel?: string;
    inputPlaceholder?: string;
    clarificationId?: string;
  };
}

interface ReasoningStepsProps {
  steps: ReasoningStep[];
  status?: "running" | "done";
  startedAt?: number;
  duration?: number;
  onApprove?: (stepId: string, extraAnswer?: string) => void;
  onDeny?: (stepId: string) => void;
  defaultExpanded?: boolean;
  className?: string;
}

function StepIcon({ step }: { step: ReasoningStep }) {
  if (step.status === "running") {
    return <Loader2 className="size-3.5 animate-spin text-[#0066CC]" strokeWidth={1.75} />;
  }
  if (step.status === "error") {
    return <AlertCircle className="size-3.5 text-[#C91919]" strokeWidth={1.75} />;
  }
  if (step.status === "approval") {
    return <ShieldAlert className="size-3.5 text-[#945800]" strokeWidth={1.75} />;
  }
  if (step.status === "denied") {
    return <X className="size-3.5 text-[#7A7A7A]" strokeWidth={1.75} />;
  }
  if (step.icon) {
    const CustomIcon = step.icon;
    return <CustomIcon className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
  }
  switch (step.kind) {
    case "thought":
      return <Cpu className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
    case "query":
      return <Database className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
    case "read":
      return <BookOpen className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
    case "search":
      return <Globe className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
    case "verify":
      return <ShieldCheck className="size-3.5 text-[#106831]" strokeWidth={1.5} />;
    case "tool":
      return <Wrench className="size-3.5 text-[#7A7A7A]" strokeWidth={1.5} />;
  }
}

function StepItem({
  step,
  onApprove,
  onDeny,
}: {
  step: ReasoningStep;
  onApprove?: (stepId: string, extraAnswer?: string) => void;
  onDeny?: (stepId: string) => void;
}) {
  const [showCode, setShowCode] = React.useState(
    step.status === "approval" || step.status === "error",
  );
  const [extraInput, setExtraInput] = React.useState("");

  const label =
    step.title ||
    (step.kind === "thought" ? "Engineering reasoning" : "Executing step");

  return (
    <div className="relative pl-6 pb-3 last:pb-0">
      <span
        className="absolute left-[6.5px] top-5 bottom-0 w-px bg-[#E0E0E0] last:hidden"
        aria-hidden="true"
      />

      <span className="absolute left-0 top-[2px] flex size-3.5 items-center justify-center bg-white">
        <StepIcon step={step} />
      </span>

      <div className="flex items-baseline justify-between gap-3">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 min-w-0">
          <span className="text-[13px] font-normal text-[#1D1D1F]">
            {label}
          </span>
          {step.detail ? (
            <span className="text-[12.5px] text-[#7A7A7A]">{step.detail}</span>
          ) : null}
          {step.status === "denied" ? (
            <span className="text-[12px] text-[#7A7A7A]">· Omitted</span>
          ) : null}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {step.code ? (
            <button
              type="button"
              onClick={() => setShowCode((v) => !v)}
              className="inline-flex items-center gap-1 font-mono text-[11.5px] text-[#7A7A7A] hover:text-[#1D1D1F]"
            >
              <Terminal className="size-3" strokeWidth={1.5} />
              <span>{showCode ? "Hide" : step.code.lang}</span>
            </button>
          ) : null}
          {step.duration !== undefined ? (
            <span className="font-mono text-[11.5px] tabular-nums text-[#7A7A7A]">
              {formatDurationMs(step.duration)}
            </span>
          ) : null}
        </div>
      </div>

      {step.content ? (
        <div className="mt-1 text-[13px] leading-relaxed text-[#333333]">
          <Markdown content={step.content} />
        </div>
      ) : null}

      {step.error ? (
        <div className="mt-1.5 text-[12.5px] text-[#C91919]">
          {step.error}
        </div>
      ) : null}

      {step.code && showCode ? (
        <pre className="mt-2 overflow-x-auto rounded-[8px] border border-[#E0E0E0] bg-[#FAFAFC] p-3 font-mono text-[12px] leading-relaxed text-[#1D1D1F]">
          <code>{step.code.text}</code>
        </pre>
      ) : null}

      {step.output ? (
        <div className="mt-1 text-[12.5px] text-[#7A7A7A]">
          <Markdown content={step.output} />
        </div>
      ) : null}

      {step.results && step.results.length > 0 ? (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {step.results.map((res, idx) =>
            res.url ? (
              <a
                key={idx}
                href={res.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-[5px] bg-[#F5F5F7] px-2 py-0.5 text-[11.5px] text-[#333333] hover:text-[#0066CC]"
              >
                <Globe className="size-3 text-[#0066CC]" strokeWidth={1.5} />
                <span className="max-w-[240px] truncate">{res.title}</span>
                {res.site ? <span className="text-[#7A7A7A]">· {res.site}</span> : null}
              </a>
            ) : (
              <span
                key={idx}
                className="inline-flex items-center gap-1 rounded-[5px] bg-[#F5F5F7] px-2 py-0.5 text-[11.5px] text-[#7A7A7A]"
              >
                <Globe className="size-3 text-[#0066CC]" strokeWidth={1.5} />
                <span className="text-[#1D1D1F]">{res.title}</span>
              </span>
            ),
          )}
        </div>
      ) : null}

      {step.status === "approval" && step.approval ? (
        <div className="mt-2.5 rounded-[12px] border border-[#F5D07E] bg-[#FFF9EB] p-4">
          <div className="flex items-start gap-2.5">
            <ShieldAlert className="mt-0.5 size-4 shrink-0 text-[#945800]" strokeWidth={1.6} />
            <div className="flex-1 min-w-0">
              <p className="text-[13.5px] font-semibold text-[#1D1D1F]">
                Verification required before drafting
              </p>
              <p className="mt-1 text-[13px] leading-relaxed text-[#333333]">
                {step.approval.message}
              </p>

              {step.approval.inputPlaceholder !== undefined ? (
                <input
                  type="text"
                  value={extraInput}
                  onChange={(e) => setExtraInput(e.target.value)}
                  placeholder={
                    step.approval.inputPlaceholder ||
                    "Enter verified engineering note"
                  }
                  className="mt-2.5 h-9 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3 text-[13px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0066CC] focus:outline-none"
                />
              ) : null}

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => onApprove?.(step.id, extraInput || undefined)}
                  className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-full bg-[#0066CC] px-3.5 text-[12.5px] text-white hover:bg-[#0071E3]"
                >
                  <Check className="size-3.5" strokeWidth={1.75} />
                  <span>{step.approval.allowLabel || "Confirm"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => onDeny?.(step.id)}
                  className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-full border border-[#E0E0E0] bg-white px-3.5 text-[12.5px] text-[#333333] hover:border-[#1D1D1F]"
                >
                  <X className="size-3.5" strokeWidth={1.75} />
                  <span>{step.approval.denyLabel || "Omit"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function ReasoningSteps({
  steps,
  status = "done",
  startedAt,
  duration,
  onApprove,
  onDeny,
  defaultExpanded = true,
  className,
}: ReasoningStepsProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);
  const [elapsedMs, setElapsedMs] = React.useState<number>(duration ?? 0);

  React.useEffect(() => {
    if (duration !== undefined) {
      setElapsedMs(duration);
      return;
    }
    if (status !== "running" || !startedAt) return;
    const interval = window.setInterval(() => {
      setElapsedMs(Date.now() - startedAt);
    }, 100);
    return () => window.clearInterval(interval);
  }, [status, startedAt, duration]);

  const hasPendingApproval = steps.some((s) => s.status === "approval");

  React.useEffect(() => {
    if (hasPendingApproval) setExpanded(true);
  }, [hasPendingApproval]);

  if (steps.length === 0 && status !== "running") return null;

  const activeStep = [...steps].reverse().find((s) => s.status === "running");

  return (
    <div className={cn("w-full bg-transparent", className)}>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-2 py-1 text-left text-[13px] text-[#7A7A7A] transition-colors hover:text-[#1D1D1F]"
      >
        {expanded ? (
          <ChevronDown className="size-3.5 shrink-0" strokeWidth={1.5} />
        ) : (
          <ChevronRight className="size-3.5 shrink-0" strokeWidth={1.5} />
        )}
        {status === "running" && !hasPendingApproval ? (
          <Loader2 className="size-3.5 animate-spin text-[#0066CC] shrink-0" strokeWidth={1.75} />
        ) : null}
        <span>
          {hasPendingApproval
            ? "Waiting for project verification"
            : status === "running"
              ? activeStep?.title || "Working..."
              : `Completed ${steps.length} reasoning ${steps.length === 1 ? "step" : "steps"}${elapsedMs > 0 ? ` in ${formatDurationMs(elapsedMs)}` : ""}`}
        </span>
      </button>

      {expanded ? (
        <div className="mt-2 ml-1.5">
          {steps.length === 0 ? (
            <div className="flex items-center gap-2 text-[13px] text-[#7A7A7A]">
              <Loader2 className="size-3.5 animate-spin text-[#0066CC]" strokeWidth={1.5} />
              <span>Connecting to research &amp; verification pipeline...</span>
            </div>
          ) : (
            steps.map((step) => (
              <StepItem
                key={step.id}
                step={step}
                onApprove={onApprove}
                onDeny={onDeny}
              />
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
