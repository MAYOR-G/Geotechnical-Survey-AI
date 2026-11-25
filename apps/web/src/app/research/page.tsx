"use client";

import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { API_BASE_URL } from "@/lib/constants";
import {
  ChatShell,
  type ShellChat,
} from "@/components/prestigeui/chat-shell";
import {
  ChatConversation,
  type ChatMessage,
} from "@/components/prestigeui/chat-conversation";
import type { PromptMessage } from "@/components/prestigeui/prompt-input";
import { BrandMark } from "@/components/prestigeui/prestige-brand";
import type { AnswerSource } from "@/components/prestigeui/cited-answer";
import type { ReasoningStep } from "@/components/prestigeui/reasoning-steps";

export default function ResearchPage() {
  const queryClient = useQueryClient();
  const [activeThreadId, setActiveThreadId] = React.useState<string | undefined>(
    undefined,
  );
  const [insertedToast, setInsertedToast] = React.useState<string>("");
  const [pinnedMap, setPinnedMap] = React.useState<Record<string, boolean>>({});
  const [renamedMap, setRenamedMap] = React.useState<Record<string, string>>(
    {},
  );
  const hasAutoSelectedRef = React.useRef(false);
  const streamAbortRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    return () => {
      streamAbortRef.current?.abort();
    };
  }, []);

  const { data: threads = [] } = useQuery({
    queryKey: ["research-threads"],
    queryFn: apiClient.listResearchThreads,
  });

  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: apiClient.listProjects,
  });

  const { data: settings } = useQuery({
    queryKey: ["workspace-settings"],
    queryFn: apiClient.getSettings,
  });

  React.useEffect(() => {
    if (!hasAutoSelectedRef.current && threads.length > 0) {
      hasAutoSelectedRef.current = true;
      setActiveThreadId(threads[0].id);
    }
  }, [threads]);

  const shellChats: ShellChat[] = React.useMemo(
    () =>
      threads.map((t, idx) => ({
        id: t.id,
        title: renamedMap[t.id] ?? t.title,
        pinned: pinnedMap[t.id] ?? idx === 0,
        updatedAt: new Date(t.created_at).getTime() || Date.now(),
      })),
    [threads, renamedMap, pinnedMap],
  );

  const activeThread = threads.find((t) => t.id === activeThreadId);
  const [localPendingMessages, setLocalPendingMessages] = React.useState<
    ChatMessage[]
  >([]);

  const messages: ChatMessage[] = React.useMemo(() => {
    const base: ChatMessage[] = activeThreadId
      ? (activeThread?.messages_json || []).map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          sources: m.sources as AnswerSource[] | undefined,
          steps: m.steps as ReasoningStep[] | undefined,
          stepsStatus: "done",
          citedStatus: m.sources ? "done" : undefined,
          status: "done",
          createdAt: new Date(m.created_at).getTime() || Date.now(),
        }))
      : [];
    return [...base, ...localPendingMessages];
  }, [activeThreadId, activeThread, localPendingMessages]);

  const patchPendingAssistant = (
    assistantId: string,
    updater: (m: ChatMessage) => ChatMessage,
  ) => {
    setLocalPendingMessages((prev) =>
      prev.map((m) => (m.id === assistantId ? updater(m) : m)),
    );
  };

  const handleSubmit = async (
    message: PromptMessage,
    { signal }: { signal: AbortSignal },
  ) => {
    const stamp = Date.now();
    const assistantId = `a-${stamp}`;

    streamAbortRef.current?.abort();
    const controller = new AbortController();
    streamAbortRef.current = controller;
    signal.addEventListener("abort", () => controller.abort());

    setLocalPendingMessages([
      {
        id: `u-${stamp}`,
        role: "user",
        content: message.text,
        attachments: message.attachments,
        createdAt: stamp,
      },
      {
        id: assistantId,
        role: "assistant",
        content: "",
        status: "thinking",
        stepsStatus: "running",
        steps: [],
        sources: [],
        citedStatus: "searching",
        createdAt: stamp,
      },
    ]);

    try {
      const response = await fetch(`${API_BASE_URL}/research/query-stream`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: message.text,
          scope: "both",
          thread_id: activeThreadId ?? null,
          project_id: projects[0]?.id ?? null,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        let errDetail = `Research stream failed (${response.status})`;
        try {
          const errJson = await response.json();
          if (errJson?.error?.message) errDetail = errJson.error.message;
        } catch {
          // ignore
        }
        throw new Error(errDetail);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const rawEvent of events) {
          const lines = rawEvent.split("\n");
          let eventName = "message";
          let dataStr = "";
          for (const ln of lines) {
            if (ln.startsWith("event:")) eventName = ln.slice(6).trim();
            if (ln.startsWith("data:")) dataStr += ln.slice(5).trim();
          }
          if (!dataStr) continue;
          const payload = JSON.parse(dataStr);

          if (eventName === "reasoning_step") {
            patchPendingAssistant(assistantId, (m) => {
              const exists = (m.steps ?? []).some((s) => s.id === payload.id);
              if (!exists) {
                return {
                  ...m,
                  steps: [
                    ...(m.steps ?? []),
                    {
                      id: payload.id,
                      kind: payload.kind || "thought",
                      status: payload.status || "running",
                      title: payload.title,
                      detail: payload.detail,
                      duration: payload.duration,
                      output: payload.output,
                      results: payload.results,
                    },
                  ],
                };
              }
              return {
                ...m,
                steps: (m.steps ?? []).map((s) =>
                  s.id === payload.id
                    ? {
                        ...s,
                        status: payload.status || "done",
                        title: payload.title || s.title,
                        detail: payload.detail ?? s.detail,
                        duration: payload.duration ?? s.duration,
                        output: payload.output ?? s.output,
                        results: payload.results ?? s.results,
                      }
                    : s,
                ),
              };
            });
          } else if (eventName === "sources") {
            patchPendingAssistant(assistantId, (m) => ({
              ...m,
              sources: payload.sources as AnswerSource[],
              citedStatus: "streaming",
            }));
          } else if (eventName === "error") {
            throw new Error(
              payload.message || "Research failed. Check .env API credentials.",
            );
          } else if (eventName === "complete") {
            hasAutoSelectedRef.current = true;
            if (payload.thread?.id) {
              setActiveThreadId(payload.thread.id);
            }
            await queryClient.invalidateQueries({
              queryKey: ["research-threads"],
            });
            setLocalPendingMessages([]);
          }
        }
      }
    } catch (err) {
      if (controller.signal.aborted) {
        patchPendingAssistant(assistantId, (m) => ({
          ...m,
          status: "stopped",
          stepsStatus: "done",
        }));
        return;
      }
      const errMessage =
        err instanceof Error && err.message
          ? err.message
          : "Could not complete research query.";
      patchPendingAssistant(assistantId, (m) => ({
        ...m,
        status: "error",
        stepsStatus: "done",
        error: errMessage,
      }));
    }
  };

  const handleInsertIntoProject = async (
    content: string,
    sources: AnswerSource[],
    projectId?: string,
  ) => {
    const targetId = projectId || projects[0]?.id;
    if (!targetId) {
      setInsertedToast("Create a project first before sending findings.");
      window.setTimeout(() => setInsertedToast(""), 3200);
      return;
    }
    const proj = await apiClient.getProject(targetId);
    const ast = proj.document_ast_json;
    const targetSec = ast.sections?.[1] || ast.sections?.[0];
    if (!targetSec) {
      setInsertedToast(`Open ${proj.title} in Studio to draft sections first.`);
      window.setTimeout(() => setInsertedToast(""), 3200);
      return;
    }
    const refs = sources.map((s, i) => `[${i + 1}] ${s.title}`).join("; ");
    const addition = `<p><strong>Verified research note:</strong> ${content.replace(/\n+/g, " ")} <em>(Sources: ${refs})</em></p>`;
    await apiClient.updateDocumentAst(proj.id, {
      ...ast,
      sections: ast.sections.map((s) =>
        s.id === targetSec.id
          ? { ...s, html_content: `${s.html_content}${addition}` }
          : s,
      ),
    });
    await apiClient.compilePreview(proj.id).catch(() => undefined);
    setInsertedToast(`Sent cited note to ${proj.title}`);
    window.setTimeout(() => setInsertedToast(""), 3200);
  };

  const handleDeleteThread = async (id: string) => {
    await apiClient.deleteResearchThread(id);
    if (id === activeThreadId) {
      setActiveThreadId(undefined);
      setLocalPendingMessages([]);
    }
    await queryClient.invalidateQueries({ queryKey: ["research-threads"] });
  };

  return (
    <div className="h-[calc(100dvh-44px)] overflow-hidden bg-white">
      <ChatShell
        borderless
        className="h-full"
        brand={
          <span className="flex items-center gap-2">
            <BrandMark className="size-4" />
            <span>Research</span>
          </span>
        }
        user={
          settings?.author_name
            ? {
                name: settings.author_name,
                email: settings.author_email || settings.default_contractor_name || "",
                plan: settings.author_designation || "",
              }
            : undefined
        }
        chats={shellChats}
        activeId={activeThreadId}
        headerRight={
          insertedToast ? (
            <span className="rounded-full border border-[#A3E2B8] bg-[#F2FAF5] px-3 py-1 text-[12px] text-[#106831]">
              {insertedToast}
            </span>
          ) : null
        }
        onSelect={(id) => {
          setLocalPendingMessages([]);
          setActiveThreadId(id);
        }}
        onNewChat={() => {
          setLocalPendingMessages([]);
          setActiveThreadId(undefined);
        }}
        onPin={(id, pinned) =>
          setPinnedMap((prev) => ({ ...prev, [id]: pinned }))
        }
        onRename={(id, title) =>
          setRenamedMap((prev) => ({ ...prev, [id]: title }))
        }
        onDelete={(id) => void handleDeleteThread(id)}
      >
        <ChatConversation
          key={activeThreadId || "new-research"}
          className="h-full"
          maxWidthClass="max-w-[740px]"
          messages={messages}
          onSubmit={handleSubmit}
          onStop={() => streamAbortRef.current?.abort()}
          projects={projects.map((p) => ({ id: p.id, title: p.title }))}
          onInsertCitation={(content, sources, pid) =>
            void handleInsertIntoProject(content, sources, pid)
          }
          emptyTitle="Ask any geotechnical, geological, or standards question"
          placeholder="Ask about BS 1377, Eurocode 7, ISO 19901-8, ASTM F1962, regional geology, or your Vault reports..."
          quickPrompts={[
            "What are ISO 19901-8 requirements for downhole PCPT testing in soft marine clays?",
            "Explain BS 1377:1990 & ASTM C1580 procedures for sulphate and Atterberg limits",
            "Summarize Delft cavity expansion hydraulic fracture limits for HDD sand crossings",
          ]}
        />
      </ChatShell>
    </div>
  );
}
