"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface FloatingStickyBarProps {
  leftContent: React.ReactNode;
  rightContent: React.ReactNode;
  className?: string;
}

export function FloatingStickyBar({
  leftContent,
  rightContent,
  className,
}: FloatingStickyBarProps) {
  return (
    <div
      className={cn(
        "frosted-chrome fixed bottom-0 left-0 right-0 z-30 h-16 border-t border-[#E2E8F0]",
        className,
      )}
    >
      <div className="mx-auto flex h-full max-w-[1280px] items-center justify-between gap-4 px-4 sm:px-6">
        <div className="text-[14px] text-[#4B5565]">{leftContent}</div>
        <div className="flex items-center gap-2.5">{rightContent}</div>
      </div>
    </div>
  );
}
