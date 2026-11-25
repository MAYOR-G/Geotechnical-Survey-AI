"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Loader2, Shield, Upload } from "lucide-react";
import { apiClient, resolveBackendUrl } from "@/lib/api-client";
import { FrostedSubNav } from "@/components/layout/FrostedSubNav";
import { Button } from "@/components/ui/Button";
import { UtilityCard } from "@/components/ui/UtilityCard";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: apiClient.getSettings,
  });

  const [contractorName, setContractorName] = React.useState("");
  const [authorName, setAuthorName] = React.useState("");
  const [authorEmail, setAuthorEmail] = React.useState("");
  const [authorDesignation, setAuthorDesignation] = React.useState("");
  const [passcodeGate, setPasscodeGate] = React.useState(false);

  const [saving, setSaving] = React.useState(false);
  const [savedBanner, setSavedBanner] = React.useState(false);
  const [uploadError, setUploadError] = React.useState("");

  const logoInputRef = React.useRef<HTMLInputElement>(null);
  const sigInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (!settings) return;
    setContractorName(settings.default_contractor_name);
    setAuthorName(settings.author_name);
    setAuthorEmail(settings.author_email);
    setAuthorDesignation(settings.author_designation);
    setPasscodeGate(settings.enable_passcode_gate);
  }, [settings]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError("");
    setSaving(true);
    try {
      await apiClient.updateSettings({
        default_contractor_name: contractorName,
        author_name: authorName,
        author_email: authorEmail,
        author_designation: authorDesignation,
        enable_passcode_gate: passcodeGate,
      });
      await queryClient.invalidateQueries({ queryKey: ["workspace-settings"] });
      setSavedBanner(true);
      window.setTimeout(() => setSavedBanner(false), 2500);
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to save defaults.",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleUploadAsset = async (
    files: FileList | null,
    kind: "logo" | "signature",
  ) => {
    if (!files || !files[0]) return;
    setUploadError("");
    try {
      await apiClient.uploadBrandingAsset(files[0], kind);
      await queryClient.invalidateQueries({ queryKey: ["workspace-settings"] });
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to upload branding asset.",
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-44px)] items-center justify-center bg-[#F5F5F7]">
        <Loader2 className="size-5 animate-spin text-[#0066CC]" />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-44px)] bg-[#F5F5F7] pb-16">
      <FrostedSubNav
        title="Defaults & Branding"
        subtitle="Corporate header logo, author identity, and digital signature"
      />

      <main className="mx-auto max-w-[680px] px-5 py-12">
        <form onSubmit={handleSave}>
          <UtilityCard className="space-y-6 p-8">
            <div>
              <h2 className="text-[24px] font-semibold tracking-[-0.02em] text-[#1D1D1F]">
                Default Contractor &amp; Author Identity
              </h2>
              <p className="mt-1 text-[14px] text-[#7A7A7A]">
                Automatically populates A4 report cover pages, running headers, and authorization sign-off tables.
              </p>
            </div>

            {uploadError ? (
              <div className="rounded-[12px] border border-[#F5B3B3] bg-[#FFF2F2] px-4 py-3 text-[13.5px] text-[#C91919]">
                {uploadError}
              </div>
            ) : null}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                  Primary contractor / consultancy name
                </label>
                <input
                  type="text"
                  value={contractorName}
                  onChange={(e) => setContractorName(e.target.value)}
                  placeholder="e.g., GEMS Global Resources / Oshone Geosurveys Limited"
                  className="h-11 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3.5 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                  Author name
                </label>
                <input
                  type="text"
                  value={authorName}
                  onChange={(e) => setAuthorName(e.target.value)}
                  placeholder="e.g., Lead Reporting Engineer"
                  className="h-11 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3.5 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                  Author designation
                </label>
                <input
                  type="text"
                  value={authorDesignation}
                  onChange={(e) => setAuthorDesignation(e.target.value)}
                  placeholder="e.g., Principal Geotechnical Engineer"
                  className="h-11 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3.5 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="mb-1.5 block text-[14px] font-semibold text-[#1D1D1F]">
                  Author email
                </label>
                <input
                  type="email"
                  value={authorEmail}
                  onChange={(e) => setAuthorEmail(e.target.value)}
                  placeholder="engineer@company.com"
                  className="h-11 w-full rounded-[8px] border border-[#E0E0E0] bg-white px-3.5 text-[15px] text-[#1D1D1F] placeholder:text-[#7A7A7A] focus:border-[#0071E3] focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 pt-1 sm:grid-cols-2">
              <div className="rounded-[18px] border border-[#E0E0E0] bg-[#FAFAFC] p-4">
                <div className="text-[13.5px] font-semibold text-[#1D1D1F]">
                  Corporate header logo
                </div>
                <div className="mt-3 flex h-16 items-center justify-center rounded-[8px] border border-[#E0E0E0] bg-white p-2">
                  {settings?.default_contractor_logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={resolveBackendUrl(settings.default_contractor_logo_url)}
                      alt="Contractor Logo"
                      className="h-11 w-auto object-contain"
                    />
                  ) : (
                    <span className="text-[12px] text-[#7A7A7A]">No logo uploaded</span>
                  )}
                </div>
                <input
                  ref={logoInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/svg+xml,image/webp"
                  onChange={(e) => void handleUploadAsset(e.target.files, "logo")}
                  className="hidden"
                />
                <Button
                  type="button"
                  variant="secondary-pill"
                  size="sm"
                  className="mt-3 w-full"
                  onClick={() => logoInputRef.current?.click()}
                >
                  <Upload className="size-4" strokeWidth={1.5} />
                  <span>Upload logo</span>
                </Button>
              </div>

              <div className="rounded-[18px] border border-[#E0E0E0] bg-[#FAFAFC] p-4">
                <div className="text-[13.5px] font-semibold text-[#1D1D1F]">
                  Author digital signature
                </div>
                <div className="mt-3 flex h-16 items-center justify-center rounded-[8px] border border-[#E0E0E0] bg-white p-2">
                  {settings?.author_signature_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={resolveBackendUrl(settings.author_signature_url)}
                      alt="Author Signature"
                      className="h-11 w-auto object-contain"
                    />
                  ) : (
                    <span className="text-[12px] text-[#7A7A7A]">No signature uploaded</span>
                  )}
                </div>
                <input
                  ref={sigInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(e) =>
                    void handleUploadAsset(e.target.files, "signature")
                  }
                  className="hidden"
                />
                <Button
                  type="button"
                  variant="secondary-pill"
                  size="sm"
                  className="mt-3 w-full"
                  onClick={() => sigInputRef.current?.click()}
                >
                  <Upload className="size-4" strokeWidth={1.5} />
                  <span>Upload signature</span>
                </Button>
              </div>
            </div>

            <div className="flex items-center justify-between rounded-[14px] border border-[#E0E0E0] bg-[#FAFAFC] px-4 py-3.5">
              <div className="flex items-center gap-3">
                <Shield className="size-4 text-[#0066CC]" strokeWidth={1.5} />
                <div>
                  <div className="text-[13.5px] font-semibold text-[#1D1D1F]">
                    Workspace passcode gate
                  </div>
                  <div className="text-[12px] text-[#7A7A7A]">
                    Require passcode authentication at /login when deployed remotely.
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={passcodeGate}
                onChange={(e) => setPasscodeGate(e.target.checked)}
                className="size-4 accent-[#0066CC]"
              />
            </div>

            <div className="flex items-center justify-end gap-3 border-t border-[#F0F0F0] pt-4">
              {savedBanner ? (
                <span className="inline-flex items-center gap-1 text-[13.5px] text-[#106831]">
                  <Check className="size-4" /> Defaults saved
                </span>
              ) : null}
              <Button type="submit" disabled={saving}>
                {saving ? <Loader2 className="size-4 animate-spin" /> : null}
                <span>Save defaults</span>
              </Button>
            </div>
          </UtilityCard>
        </form>
      </main>
    </div>
  );
}
