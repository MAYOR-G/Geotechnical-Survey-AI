"use client";

import * as React from "react";
import {
  ArrowUp,
  FileSpreadsheet,
  FileText,
  Folder,
  Image as ImageIcon,
  Plus,
  Square,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface PromptAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
  subtitle?: string;
  kind?: "file" | "folder" | "image" | "spreadsheet";
  file?: File;
}

export interface PromptMessage {
  text: string;
  model: string;
  searchEnabled?: boolean;
  attachments?: PromptAttachment[];
}

interface PromptInputProps {
  onSubmit: (
    message: PromptMessage,
    helpers: { signal: AbortSignal },
  ) => void | Promise<void>;
  onStop?: () => void;
  isStreaming?: boolean;
  placeholder?: string;
  defaultModel?: string;
  defaultText?: string;
  quickPrompts?: string[];
  showSearchToggle?: boolean;
  defaultSearchEnabled?: boolean;
  onSearchToggle?: (enabled: boolean) => void;
  showDisclaimer?: boolean;
  initialAttachments?: PromptAttachment[];
  className?: string;
}

function formatAttachmentMeta(att: PromptAttachment): string {
  if (att.subtitle) return att.subtitle;
  const ext = att.name.includes(".")
    ? att.name.split(".").pop()?.toUpperCase() || "FILE"
    : att.kind === "folder"
      ? "Folder"
      : "FILE";
  if (!att.size) return ext;
  if (att.size >= 1024 * 1024) {
    return `${ext} · ${(att.size / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${ext} · ${Math.max(1, Math.round(att.size / 1024))} KB`;
}

function AttachmentIcon({ att }: { att: PromptAttachment }) {
  if (att.kind === "folder") {
    return <Folder className="size-4 text-[#0066CC]" strokeWidth={1.5} />;
  }
  if (att.kind === "image" || att.type.startsWith("image/")) {
    return <ImageIcon className="size-4 text-[#0066CC]" strokeWidth={1.5} />;
  }
  if (
    att.kind === "spreadsheet" ||
    /\.(xlsx|xls|csv)$/i.test(att.name)
  ) {
    return (
      <FileSpreadsheet className="size-4 text-[#0066CC]" strokeWidth={1.5} />
    );
  }
  return <FileText className="size-4 text-[#0066CC]" strokeWidth={1.5} />;
}

export function PromptInput({
  onSubmit,
  onStop,
  isStreaming = false,
  placeholder = "Ask a geotechnical question or instruct the authoring engine...",
  defaultModel = "tier1_tier2_pipeline",
  defaultText = "",
  quickPrompts,
  showDisclaimer = false,
  initialAttachments,
  className,
}: PromptInputProps) {
  const [text, setText] = React.useState(defaultText);
  const [model] = React.useState(defaultModel);
  const [attachments, setAttachments] = React.useState<PromptAttachment[]>(
    () => initialAttachments ?? [],
  );
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const abortRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    setAttachments(initialAttachments ?? []);
  }, [initialAttachments]);

  React.useEffect(() => {
    setText(defaultText);
  }, [defaultText]);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const next: PromptAttachment[] = Array.from(files).map((f, idx) => ({
      id: `${Date.now()}-${idx}-${f.name}`,
      name: f.name,
      size: f.size,
      type: f.type || "application/octet-stream",
      file: f,
    }));
    setAttachments((prev) => [...prev, ...next]);
  };

  const submitCurrent = async (overrideText?: string) => {
    const content = (overrideText ?? text).trim();
    if (!content && attachments.length === 0) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const fallbackText =
      content ||
      `Analyze uploaded file(s): ${attachments.map((a) => a.name).join(", ")}`;

    const payload: PromptMessage = {
      text: fallbackText,
      model,
      searchEnabled: true,
      attachments: attachments.length > 0 ? attachments : undefined,
    };

    if (!overrideText) {
      setText("");
      setAttachments([]);
    }
    await onSubmit(payload, { signal: controller.signal });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming) {
        void submitCurrent();
      }
    }
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="rounded-[22px] border border-[#E0E0E0] bg-white px-4 pb-2.5 pt-3 transition-colors focus-within:border-[#0071E3]">
        {attachments.length > 0 ? (
          <div className="mb-2.5 flex flex-wrap gap-2">
            {attachments.map((att) => (
              <div
                key={att.id}
                className="group relative flex min-w-[180px] max-w-[260px] items-center gap-2.5 rounded-[11px] border border-[#E0E0E0] bg-[#FAFAFC] px-3 py-1.5"
              >
                <AttachmentIcon att={att} />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[12.5px] font-semibold text-[#1D1D1F]">
                    {att.name}
                  </div>
                  <div className="truncate text-[11px] text-[#7A7A7A]">
                    {formatAttachmentMeta(att)}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setAttachments((prev) =>
                      prev.filter((a) => a.id !== att.id),
                    )
                  }
                  className="inline-flex size-5 shrink-0 items-center justify-center rounded-full text-[#7A7A7A] hover:bg-[#E0E0E0] hover:text-[#1D1D1F]"
                  aria-label={`Remove ${att.name}`}
                >
                  <X className="size-3" />
                </button>
              </div>
            ))}
          </div>
        ) : null}

        <textarea
          ref={textareaRef}
          rows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="max-h-[140px] min-h-[42px] w-full resize-none border-0 bg-transparent px-0.5 py-1 text-[15.5px] leading-[1.5] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:outline-none focus-visible:outline-none"
        />

        <div className="mt-1 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".xlsx,.xls,.csv,.docx,.pdf,.txt,.png,.jpg,.jpeg,.webp"
              onChange={(e) => handleFiles(e.target.files)}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="cupertino-press inline-flex h-8 items-center gap-1.5 rounded-full border border-[#E0E0E0] bg-[#FAFAFC] px-3 text-[12.5px] text-[#333333] hover:border-[#0066CC] hover:text-[#0066CC]"
              title="Attach Excel, CSV, DOCX, PDF, or field photo"
              aria-label="Attach files"
            >
              <Plus className="size-3.5" strokeWidth={1.75} />
              <span>Attach files</span>
            </button>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {isStreaming ? (
              <button
                type="button"
                onClick={() => {
                  abortRef.current?.abort();
                  onStop?.();
                }}
                className="cupertino-press inline-flex size-9 items-center justify-center rounded-full bg-[#1D1D1F] text-white hover:opacity-90"
                aria-label="Stop generation"
              >
                <Square className="size-3 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => void submitCurrent()}
                disabled={!text.trim() && attachments.length === 0}
                className="cupertino-press inline-flex size-9 items-center justify-center rounded-full bg-[#0066CC] text-white transition-colors hover:bg-[#0071E3] disabled:cursor-not-allowed disabled:bg-[#E0E0E0] disabled:text-[#7A7A7A]"
                aria-label="Send message"
              >
                <ArrowUp className="size-4" strokeWidth={1.85} />
              </button>
            )}
          </div>
        </div>
      </div>

      {showDisclaimer ? (
        <p className="mt-2 text-center text-[11.5px] text-[#7A7A7A]">
          Verify critical coordinates, depths, and engineering parameters before final issue.
        </p>
      ) : null}

      {quickPrompts && quickPrompts.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          {quickPrompts.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => void submitCurrent(chip)}
              disabled={isStreaming}
              className="cupertino-press inline-flex h-8 items-center rounded-full border border-[#E0E0E0] bg-white px-3.5 text-[12.5px] text-[#333333] transition-colors hover:border-[#0066CC] hover:text-[#0066CC] disabled:opacity-50"
            >
              {chip}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
