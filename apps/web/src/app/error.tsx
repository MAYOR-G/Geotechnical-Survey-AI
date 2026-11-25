"use client";

import * as React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { UtilityCard } from "@/components/ui/UtilityCard";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-[calc(100vh-44px)] items-center justify-center bg-[#F5F5F7] px-4">
      <UtilityCard className="max-w-[460px] text-center">
        <AlertTriangle className="mx-auto size-8 text-[#945800]" />
        <h2 className="mt-3 text-[21px] font-semibold text-[#1D1D1F]">
          Studio Render Interrupted
        </h2>
        <p className="mt-2 text-[14px] text-[#7A7A7A]">
          {error.message || "An unexpected client error occurred."}
        </p>
        <div className="mt-5 flex justify-center">
          <Button onClick={reset}>
            <RotateCcw className="size-4" />
            <span>Retry Render</span>
          </Button>
        </div>
      </UtilityCard>
    </main>
  );
}
