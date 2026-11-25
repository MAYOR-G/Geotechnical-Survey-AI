import * as React from "react";
import { cn } from "@/lib/utils";

export function UtilityCard({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[18px] border border-[#E0E0E0] bg-white p-6",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
