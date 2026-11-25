import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { GlobalTopNav } from "@/components/layout/GlobalTopNav";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "600", "700"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Geotechnical Survey AI — Engineering Documentation Studio",
  description:
    "AI Engineering Documentation & Technical Report Studio for offshore and oil & gas geotechnical survey teams.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[#F5F5F7] font-sans text-[#1D1D1F] antialiased">
        <Providers>
          <GlobalTopNav />
          {children}
        </Providers>
      </body>
    </html>
  );
}
