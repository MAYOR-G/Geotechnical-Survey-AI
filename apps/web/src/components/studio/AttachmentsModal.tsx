"use client";

import * as React from "react";
import { ArrowDown, ArrowUp, FileText, Loader2, Trash2, UploadCloud } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import type { ProjectAttachment } from "@/types/project";

interface AttachmentsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  attachments: ProjectAttachment[];
  onUpdated: () => void;
  onRecompilePdf: () => void;
}

export function AttachmentsModal({
  open,
  onOpenChange,
  projectId,
  attachments,
  onUpdated,
  onRecompilePdf,
}: AttachmentsModalProps) {
  const [title, setTitle] = React.useState("");
  const [uploading, setUploading] = React.useState(false);
  const fileRef = React.useRef<HTMLInputElement>(null);

  const handleUpload = async (files: FileList | null) => {
    if (!files || !files[0]) return;
    setUploading(true);
    try {
      await apiClient.uploadAttachment(
        projectId,
        files[0],
        title.trim() || files[0].name.replace(/\.pdf$/i, ""),
      );
      setTitle("");
      onUpdated();
    } finally {
      setUploading(false);
    }
  };

  const move = async (idx: number, delta: -1 | 1) => {
    const nextIdx = idx + delta;
    if (nextIdx < 0 || nextIdx >= attachments.length) return;
    const copy = [...attachments];
    const [moved] = copy.splice(idx, 1);
    copy.splice(nextIdx, 0, moved);
    await apiClient.reorderAttachments(
      projectId,
      copy.map((a) => a.id),
    );
    onUpdated();
  };

  const handleDelete = async (id: string) => {
    await apiClient.deleteAttachment(projectId, id);
    onUpdated();
  };

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="External PDF Attachments & Appendices"
      description="Uploaded PDFs (Borehole Logs, PCPT Plots, Lab Summary Sheets) are merged sequentially at the end of the compiled Master PDF."
    >
      <div className="space-y-5">
        <div className="space-y-2">
          {attachments.length === 0 ? (
            <div className="rounded-[14px] border border-[#E0E0E0] bg-[#F5F5F7] p-6 text-center text-[13.5px] text-[#7A7A7A]">
              No external attachments added yet. Upload Borehole Logs or PCPT Plots below.
            </div>
          ) : (
            attachments.map((att, idx) => (
              <div
                key={att.id}
                className="flex items-center justify-between gap-3 rounded-[14px] border border-[#E0E0E0] bg-[#FAFAFC] px-4 py-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className="size-4 shrink-0 text-[#0066CC]" />
                  <div className="min-w-0">
                    <div className="text-[13.5px] font-semibold text-[#1D1D1F] truncate">
                      {att.attachment_number}: {att.title}
                    </div>
                    <div className="font-mono text-[11.5px] text-[#7A7A7A]">
                      Order #{att.display_order} · {att.page_count ?? 1} page(s)
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    disabled={idx === 0}
                    onClick={() => void move(idx, -1)}
                    className="rounded-[6px] border border-[#E0E0E0] bg-white p-1.5 text-[#333333] hover:bg-[#F5F5F7] disabled:opacity-40"
                    aria-label="Move up"
                  >
                    <ArrowUp className="size-3.5" />
                  </button>
                  <button
                    type="button"
                    disabled={idx === attachments.length - 1}
                    onClick={() => void move(idx, 1)}
                    className="rounded-[6px] border border-[#E0E0E0] bg-white p-1.5 text-[#333333] hover:bg-[#F5F5F7] disabled:opacity-40"
                    aria-label="Move down"
                  >
                    <ArrowDown className="size-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleDelete(att.id)}
                    className="rounded-[6px] border border-[#F5B3B3] bg-[#FFF2F2] p-1.5 text-[#C91919] hover:bg-[#FFE5E5]"
                    aria-label="Delete attachment"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="rounded-[14px] border border-[#E0E0E0] bg-white p-4 space-y-3">
          <div className="text-[13px] font-semibold text-[#1D1D1F]">
            Append New External PDF
          </div>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Attachment Title (e.g., Attachment 4: Triaxial Stress-Strain Plots)"
            className="h-10 w-full rounded-[8px] border border-[#E0E0E0] px-3 text-[13.5px]"
          />
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            onChange={(e) => void handleUpload(e.target.files)}
            className="hidden"
          />
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Button
              variant="secondary-pill"
              size="sm"
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
            >
              {uploading ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <UploadCloud className="size-3.5" />
              )}
              <span>Choose PDF File</span>
            </Button>

            <Button
              size="sm"
              onClick={() => {
                onRecompilePdf();
                onOpenChange(false);
              }}
            >
              Recompile &amp; Merge Master PDF
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
