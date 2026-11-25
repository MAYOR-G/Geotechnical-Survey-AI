"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "primary"
    | "secondary-pill"
    | "pearl"
    | "dark-utility"
    | "destructive"
    | "icon-circular";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
      primary:
        "rounded-full bg-[#0066CC] text-white hover:bg-[#0071E3] disabled:bg-[#E0E0E0] disabled:text-[#7A7A7A]",
      "secondary-pill":
        "rounded-full border border-[#0066CC] bg-transparent text-[#0066CC] hover:bg-[#0066CC]/[0.08] disabled:border-[#E0E0E0] disabled:text-[#7A7A7A]",
      pearl:
        "rounded-[11px] border-[2px] border-[#F0F0F0] bg-[#FAFAFC] text-[#333333] hover:border-[#E0E0E0]",
      "dark-utility":
        "rounded-[8px] bg-[#1D1D1F] text-white hover:opacity-90 disabled:bg-[#E0E0E0] disabled:text-[#7A7A7A]",
      destructive:
        "rounded-full border border-[#F5B3B3] bg-[#FFF2F2] text-[#C91919] hover:bg-[#FFE5E5]",
      "icon-circular":
        "size-10 rounded-full bg-[#D2D2D7]/65 text-[#1D1D1F] backdrop-blur-md hover:bg-[#D2D2D7]",
    };

    const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
      sm: variant === "icon-circular" ? "size-9" : "h-9 px-4 text-[13.5px]",
      md: variant === "icon-circular" ? "size-10" : "h-10 px-5 text-[14.5px]",
      lg: variant === "icon-circular" ? "size-11" : "h-11 px-6 text-[16px]",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "cupertino-press inline-flex items-center justify-center gap-2 font-normal focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0071E3] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:transform-none whitespace-nowrap",
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
