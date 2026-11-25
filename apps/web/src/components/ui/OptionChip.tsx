"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface OptionChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
}

export function OptionChip({
  selected = false,
  className,
  children,
  ...props
}: OptionChipProps) {
  return (
    <button
      type="button"
      className={cn(
        "cupertino-press inline-flex h-9 items-center gap-2 rounded-full px-4 text-[13.5px] font-normal transition-colors",
        selected
          ? "border-2 border-[#0071E3] bg-[#F0F7FF] font-semibold text-[#0066CC]"
          : "border border-[#E0E0E0] bg-white text-[#333333] hover:border-[#0066CC] hover:text-[#1D1D1F]",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
