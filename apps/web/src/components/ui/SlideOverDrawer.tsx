"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SlideOverDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  dark?: boolean;
  children: React.ReactNode;
}

export function SlideOverDrawer({
  open,
  onClose,
  title,
  subtitle,
  dark = false,
  children,
}: SlideOverDrawerProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div
        className="fixed inset-0 bg-[#1D1D1F]/35 backdrop-blur-[6px]"
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={cn(
          "relative z-10 mt-[96px] flex h-[calc(100vh-96px)] w-full max-w-[440px] flex-col border-l",
          dark
            ? "border-[#38383A] bg-[#272729] text-white"
            : "border-[#E0E0E0] bg-[#F5F5F7] text-[#1D1D1F]",
        )}
      >
        <div
          className={cn(
            "flex items-center justify-between border-b px-5 py-3.5",
            dark ? "border-[#38383A]" : "border-[#E0E0E0] bg-white",
          )}
        >
          <div>
            <h2 className="text-[16px] font-semibold">{title}</h2>
            {subtitle ? (
              <p
                className={cn(
                  "text-[12px]",
                  dark ? "text-[#CCCCCC]" : "text-[#7A7A7A]",
                )}
              >
                {subtitle}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close drawer"
            className={cn(
              "cupertino-press inline-flex size-8 items-center justify-center rounded-full",
              dark
                ? "bg-[#2A2A2C] text-white hover:bg-[#38383A]"
                : "bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E0E0E0]",
            )}
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </aside>
    </div>
  );
}
