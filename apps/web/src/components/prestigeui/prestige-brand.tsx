import * as React from "react";
import { cn } from "@/lib/utils";

export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("size-6 shrink-0", className)}
      aria-hidden="true"
    >
      <rect width="28" height="28" rx="7" fill="#1D1D1F" />
      <path
        d="M6.5 17.5C9.5 15.2 12.2 18.8 15 16.5C17.8 14.2 19.6 16.8 21.5 15.5"
        stroke="#2997FF"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M6.5 21C9.5 18.8 12.2 22.1 15 19.8C17.8 17.6 19.6 20 21.5 18.8"
        stroke="#FFFFFF"
        strokeOpacity="0.65"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M14 5.5V15.5M14 5.5L11.2 8.4M14 5.5L16.8 8.4"
        stroke="#FFFFFF"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** 8-ray sparkle glyph used next to model names in Prestige UI composer and responses. */
export function SparkleMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("size-3.5 shrink-0", className)}
      aria-hidden="true"
    >
      <path
        d="M8 1.5V14.5M1.5 8H14.5M3.4 3.4L12.6 12.6M12.6 3.4L3.4 12.6"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}
