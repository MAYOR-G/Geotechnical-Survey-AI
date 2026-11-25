import { create } from "zustand";

export type StudioLayoutMode = "split" | "editor_pdf" | "canvas" | "chat";
export type CanvasMode = "edit" | "preview";
export type StudioDrawer = "none" | "outline" | "qa_log" | "research";

interface StudioStoreState {
  layoutMode: StudioLayoutMode;
  canvasMode: CanvasMode;
  splitPercent: number;
  pdfZoom: number;
  activeDrawer: StudioDrawer;
  attachmentsModalOpen: boolean;
  placeholderModalTarget: {
    sectionId: string;
    placeholderId: string;
    figureNumber: string;
    prompt: string;
  } | null;
  setLayoutMode: (mode: StudioLayoutMode) => void;
  setCanvasMode: (mode: CanvasMode) => void;
  setSplitPercent: (pct: number) => void;
  setPdfZoom: (zoom: number) => void;
  setActiveDrawer: (drawer: StudioDrawer) => void;
  setAttachmentsModalOpen: (open: boolean) => void;
  setPlaceholderModalTarget: (
    target: StudioStoreState["placeholderModalTarget"],
  ) => void;
}

export const useStudioStore = create<StudioStoreState>((set) => ({
  layoutMode: "split",
  canvasMode: "preview",
  splitPercent: 45,
  pdfZoom: 100,
  activeDrawer: "none",
  attachmentsModalOpen: false,
  placeholderModalTarget: null,
  setLayoutMode: (layoutMode) => set({ layoutMode }),
  setCanvasMode: (canvasMode) => set({ canvasMode }),
  setSplitPercent: (splitPercent) =>
    set({ splitPercent: Math.min(70, Math.max(30, splitPercent)) }),
  setPdfZoom: (pdfZoom) => set({ pdfZoom: Math.min(160, Math.max(60, pdfZoom)) }),
  setActiveDrawer: (activeDrawer) => set({ activeDrawer }),
  setAttachmentsModalOpen: (attachmentsModalOpen) =>
    set({ attachmentsModalOpen }),
  setPlaceholderModalTarget: (placeholderModalTarget) =>
    set({ placeholderModalTarget }),
}));
