"use client";

import * as React from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchPillInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string;
  onChange: (value: string) => void;
}

export function SearchPillInput({
  value,
  onChange,
  placeholder = "Search projects, client, or ref code...",
  className,
  ...props
}: SearchPillInputProps) {
  return (
    <div className={cn("relative w-full", className)}>
      <Search
        className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#7A7A7A]"
        strokeWidth={1.5}
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-11 w-full rounded-full border border-[#E0E0E0] bg-white pl-10 pr-9 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
        {...props}
      />
      {value ? (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-[#7A7A7A] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"
          aria-label="Clear search"
        >
          <X className="size-3.5" strokeWidth={1.5} />
        </button>
      ) : null}
    </div>
  );
}
