"use client";

import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  maxWidthClass?: string;
  children: React.ReactNode;
}

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  maxWidthClass = "max-w-[680px]",
  children,
}: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-[#1D1D1F]/48 backdrop-blur-[8px]" />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-[92vw] -translate-x-1/2 -translate-y-1/2 rounded-[14px] border border-[#E0E0E0] bg-white p-6 max-h-[88vh] flex flex-col focus:outline-none",
            maxWidthClass,
          )}
        >
          <div className="flex items-start justify-between gap-4 border-b border-[#E0E0E0] pb-4">
            <div>
              <Dialog.Title className="text-[19px] font-semibold tracking-[-0.02em] text-[#1D1D1F]">
                {title}
              </Dialog.Title>
              {description ? (
                <Dialog.Description className="mt-1 text-[13.5px] text-[#7A7A7A]">
                  {description}
                </Dialog.Description>
              ) : null}
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Close modal"
                className="cupertino-press inline-flex size-8 items-center justify-center rounded-full bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E0E0E0]"
              >
                <X className="size-4" />
              </button>
            </Dialog.Close>
          </div>
          <div className="mt-4 flex-1 overflow-y-auto pr-1">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
