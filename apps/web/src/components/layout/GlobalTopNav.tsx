"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Command,
  Menu,
  Plus,
  Search,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BrandMark } from "@/components/prestigeui/prestige-brand";
import { API_BASE_URL } from "@/lib/constants";
import { apiClient } from "@/lib/api-client";

export function GlobalTopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [apiHealthy, setApiHealthy] = React.useState<boolean | null>(null);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [quickSearchOpen, setQuickSearchOpen] = React.useState(false);
  const [quickQuery, setQuickQuery] = React.useState("");

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: apiClient.listProjects,
    enabled: pathname !== "/login",
  });

  const studioHref = projects[0]
    ? `/projects/${projects[0].id}/studio`
    : "/projects/new";

  const navItems = React.useMemo(
    () => [
      {
        href: "/dashboard",
        label: "Projects",
        match: (p: string) => p === "/dashboard" || p === "/projects/new",
      },
      {
        href: studioHref,
        label: "Document Studio",
        match: (p: string) => p.includes("/studio"),
      },
      {
        href: "/vault",
        label: "Knowledge Vault",
        match: (p: string) => p === "/vault",
      },
      {
        href: "/research",
        label: "Research Assistant",
        match: (p: string) => p === "/research",
      },
      {
        href: "/settings",
        label: "Defaults & Branding",
        match: (p: string) => p === "/settings",
      },
    ],
    [studioHref],
  );

  React.useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
        if (active) setApiHealthy(res.ok);
      } catch {
        if (active) setApiHealthy(false);
      }
    };
    void checkHealth();
    const id = window.setInterval(() => void checkHealth(), 30000);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, []);

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setQuickSearchOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (pathname === "/login") return null;

  return (
    <>
      <header className="sticky top-0 z-50 h-[44px] w-full bg-[#000000] text-white">
        <div className="mx-auto flex h-full max-w-[1440px] items-center justify-between gap-4 px-5 sm:px-8">
          <div className="flex items-center gap-7 min-w-0">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 shrink-0 text-[13px] font-semibold tracking-[-0.01em] text-white hover:opacity-90"
            >
              <BrandMark className="size-5" />
              <span className="hidden sm:inline">Geotechnical Survey AI</span>
            </Link>

            <nav className="hidden lg:flex items-center gap-6" aria-label="Global Navigation">
              {navItems.map((item) => {
                const isActive = item.match(pathname);
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    className={cn(
                      "text-[12px] tracking-[-0.12px] transition-colors",
                      isActive
                        ? "font-semibold text-white"
                        : "font-normal text-[#CCCCCC] hover:text-white",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() => setQuickSearchOpen(true)}
              className="cupertino-press hidden sm:inline-flex h-7 items-center gap-1.5 rounded-full bg-white/[0.1] px-2.5 text-[12px] text-[#CCCCCC] hover:bg-white/[0.16] hover:text-white"
            >
              <Search className="size-3" strokeWidth={1.5} />
              <kbd className="inline-flex items-center gap-0.5 font-mono text-[10.5px] text-white">
                <Command className="size-2.5" />K
              </kbd>
            </button>

            <div
              className="hidden md:inline-flex items-center gap-1.5 text-[11.5px] text-[#CCCCCC]"
              title={
                apiHealthy
                  ? "Document & multi-agent engine online"
                  : "Document engine offline"
              }
            >
              <span
                className={cn(
                  "size-1.5 rounded-full",
                  apiHealthy === null
                    ? "bg-[#7A7A7A]"
                    : apiHealthy
                      ? "bg-[#30D158]"
                      : "bg-[#FF453A]",
                )}
              />
              <span>
                {apiHealthy ? "Engine online" : apiHealthy === false ? "Offline" : "Connecting"}
              </span>
            </div>

            <Link
              href="/projects/new"
              className="cupertino-press hidden sm:inline-flex h-7 items-center gap-1 rounded-full bg-[#0066CC] px-3 text-[12px] font-normal text-white hover:bg-[#0071E3]"
            >
              <Plus className="size-3.5" strokeWidth={1.75} />
              <span>New Report</span>
            </Link>

            <button
              type="button"
              onClick={() => setMobileOpen((v) => !v)}
              className="lg:hidden inline-flex size-8 items-center justify-center rounded-full text-white hover:bg-white/10"
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? <X className="size-4" /> : <Menu className="size-4" />}
            </button>
          </div>
        </div>

        {mobileOpen ? (
          <div className="border-t border-[#38383A] bg-[#000000] px-5 py-3 lg:hidden">
            <nav className="flex flex-col gap-1">
              {navItems.map((item) => {
                const isActive = item.match(pathname);
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex h-9 items-center rounded-[8px] px-3 text-[13.5px]",
                      isActive
                        ? "bg-white/15 font-semibold text-white"
                        : "text-[#CCCCCC] hover:text-white",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <Link
                href="/projects/new"
                onClick={() => setMobileOpen(false)}
                className="mt-2 flex h-9 items-center justify-center gap-1.5 rounded-full bg-[#0066CC] text-[13.5px] text-white"
              >
                <Plus className="size-4" />
                <span>New Report</span>
              </Link>
            </nav>
          </div>
        ) : null}
      </header>

      {quickSearchOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-[#1D1D1F]/48 pt-24 backdrop-blur-[8px]"
          onClick={() => setQuickSearchOpen(false)}
        >
          <div
            className="w-[92vw] max-w-[560px] rounded-[18px] border border-[#E0E0E0] bg-white p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2.5 border-b border-[#E0E0E0] pb-3">
              <Search className="size-4 text-[#7A7A7A]" strokeWidth={1.5} />
              <input
                autoFocus
                type="text"
                value={quickQuery}
                onChange={(e) => setQuickQuery(e.target.value)}
                placeholder="Jump to project, vault, or research..."
                className="w-full text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setQuickSearchOpen(false)}
                className="rounded-[5px] bg-[#F5F5F7] px-2 py-0.5 font-mono text-[11px] text-[#7A7A7A]"
              >
                ESC
              </button>
            </div>
            <div className="mt-3 max-h-[320px] space-y-1 overflow-y-auto">
              {[
                ...navItems.map((n) => ({ href: n.href, label: n.label })),
                { href: "/projects/new", label: "Start New Geotechnical Report" },
                ...projects.map((p) => ({
                  href: `/projects/${p.id}/studio`,
                  label: p.title,
                })),
              ]
                .filter((i) =>
                  i.label.toLowerCase().includes(quickQuery.toLowerCase()),
                )
                .map((item) => (
                  <button
                    key={`${item.href}-${item.label}`}
                    type="button"
                    onClick={() => {
                      setQuickSearchOpen(false);
                      setQuickQuery("");
                      router.push(item.href);
                    }}
                    className="flex h-10 w-full items-center justify-between gap-3 rounded-[8px] px-3 text-left text-[14px] text-[#1D1D1F] hover:bg-[#F5F5F7]"
                  >
                    <span className="truncate">{item.label}</span>
                    <span className="shrink-0 font-mono text-[12px] text-[#7A7A7A]">
                      {item.href}
                    </span>
                  </button>
                ))}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
