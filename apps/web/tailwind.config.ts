import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#FFFFFF",
        "canvas-parchment": "#F5F5F7",
        "surface-pearl": "#FAFAFC",
        "surface-black": "#000000",
        "surface-tile-1": "#272729",
        "surface-tile-2": "#2A2A2C",
        "surface-tile-3": "#252527",
        ink: "#1D1D1F",
        "ink-muted-80": "#333333",
        "ink-muted-48": "#7A7A7A",
        foreground: "#1D1D1F",
        "muted-foreground": "#7A7A7A",
        primary: {
          DEFAULT: "#0066CC",
          focus: "#0071E3",
          "on-dark": "#2997FF",
          tint: "rgba(0, 102, 204, 0.08)",
        },
        hairline: {
          DEFAULT: "#E0E0E0",
          soft: "#F0F0F0",
          "on-dark": "#38383A",
        },
        status: {
          "success-bg": "#F2FAF5",
          "success-border": "#A3E2B8",
          "success-text": "#106831",
          "warning-bg": "#FFF9EB",
          "warning-border": "#F5D07E",
          "warning-text": "#945800",
          "danger-bg": "#FFF2F2",
          "danger-border": "#F5B3B3",
          "danger-text": "#C91919",
          "info-bg": "#F0F7FF",
          "info-border": "#B8D9FF",
          "info-text": "#0066CC",
        },
      },
      fontFamily: {
        display: [
          "var(--font-sans)",
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "Inter",
          "system-ui",
          "sans-serif",
        ],
        sans: [
          "var(--font-sans)",
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Text",
          "Inter",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "var(--font-mono)",
          "SF Mono",
          "JetBrains Mono",
          "ui-monospace",
          "monospace",
        ],
      },
      borderRadius: {
        none: "0px",
        xs: "5px",
        sm: "8px",
        md: "11px",
        lg: "18px",
        pill: "9999px",
        full: "50%",
      },
      boxShadow: {
        artifact: "3px 5px 30px 0px rgba(0, 0, 0, 0.22)",
      },
      transitionTimingFunction: {
        cupertino: "cubic-bezier(0.25, 1, 0.5, 1)",
        sheet: "cubic-bezier(0.32, 0.72, 0, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
