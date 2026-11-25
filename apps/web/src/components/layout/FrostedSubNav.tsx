"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface FrostedSubNavProps {
  title: string;
  badge?: string;
  subtitle?: string;
  fullBleed?: boolean;
  compact?: boolean;
  leftExtra?: React.ReactNode;
  rightContent?: React.ReactNode;
  className?: string;
}

export function FrostedSubNav({
  title,
  badge,
  subtitle,
  fullBleed = false,
  compact = false,
  leftExtra,
  rightContent,
  className,
}: FrostedSubNavProps) {
  return (
    <div
      className={cn(
        "frosted-chrome w-full border-b border-black/[0.08]",
        fullBleed || compact
          ? "relative z-30 shrink-0"
          : "sticky top-[44px] z-40",
        "h-[52px]",
        className,
      )}
    >
      <div
        className={cn(
          "mx-auto flex h-full items-center justify-between gap-4 px-5 sm:px-8",
          fullBleed ? "max-w-full" : "max-w-[1440px]",
        )}
      >
        <div className="flex min-w-0 items-center gap-3">
          {leftExtra}
          <h1 className="truncate text-[19px] sm:text-[21px] font-semibold tracking-[-0.015em] text-[#1D1D1F]">
            {title}
          </h1>
          {badge ? (
            <span className="hidden sm:inline-flex items-center rounded-[5px] border border-[#E0E0E0] bg-white px-2 py-0.5 font-mono text-[12px] text-[#1D1D1F]">
              {badge}
            </span>
          ) : null}
          {subtitle ? (
            <span className="hidden xl:inline truncate text-[12.5px] text-[#7A7A7A]">
              {subtitle}
            </span>
          ) : null}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {rightContent}
        </div>
      </div>
    </div>
  );
}
