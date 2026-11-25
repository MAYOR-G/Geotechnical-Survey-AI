"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Lock } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/Button";
import { UtilityCard } from "@/components/ui/UtilityCard";
import { BrandMark } from "@/components/prestigeui/prestige-brand";

export default function LoginPage() {
  const router = useRouter();
  const [passcode, setPasscode] = React.useState("");
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await apiClient.unlockPasscode(passcode);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Invalid workspace passcode.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F5F5F7] px-4">
      <UtilityCard className="w-full max-w-[420px] p-8">
        <div className="flex items-center gap-3">
          <BrandMark className="size-8" />
          <span className="text-[13px] font-semibold text-[#7A7A7A]">
            Private Geotechnical Studio
          </span>
        </div>

        <h1 className="mt-5 text-[34px] font-semibold tracking-[-0.025em] leading-tight text-[#1D1D1F]">
          Studio Access
        </h1>
        <p className="mt-2 text-[14px] text-[#7A7A7A]">
          Enter your workspace passcode to unlock client reports, coordinate
          spreadsheets, and the Knowledge Vault.
        </p>

        <form onSubmit={handleUnlock} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="passcode"
              className="mb-1.5 block text-[13.5px] font-semibold text-[#1D1D1F]"
            >
              Workspace Passcode
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-[#7A7A7A]" />
              <input
                id="passcode"
                type="password"
                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                placeholder="Enter passcode..."
                className="h-11 w-full rounded-full border border-[#E0E0E0] bg-white pl-10 pr-4 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
                required
              />
            </div>
            {error ? (
              <p className="mt-1.5 text-[13px] text-[#C91919]">{error}</p>
            ) : null}
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-[15px]"
          >
            {loading ? "Verifying..." : "Unlock Workspace"}
          </Button>
        </form>
      </UtilityCard>
    </main>
  );
}
