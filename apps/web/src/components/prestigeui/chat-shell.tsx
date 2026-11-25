"use client";

import * as React from "react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import {
  MoreHorizontal,
  PanelLeft,
  Pencil,
  Pin,
  PinOff,
  Search,
  SquarePen,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface ShellChat {
  id: string;
  title: string;
  pinned?: boolean;
  updatedAt: number;
  subtitle?: string;
}

interface ChatShellProps {
  brand?: React.ReactNode;
  user?: { name: string; email: string; plan?: string };
  chats: ShellChat[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onRename?: (id: string, title: string) => void;
  onPin?: (id: string, pinned: boolean) => void;
  onDelete?: (id: string) => void;
  headerRight?: React.ReactNode;
  compactHeader?: boolean;
  defaultCollapsed?: boolean;
  borderless?: boolean;
  className?: string;
  children: React.ReactNode;
}

interface ChatGroup {
  label: string;
  items: ShellChat[];
}

function groupChatsByRecency(chats: ShellChat[]): ChatGroup[] {
  const now = new Date();
  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  ).getTime();
  const dayMs = 86_400_000;

  const pinned: ShellChat[] = [];
  const today: ShellChat[] = [];
  const yesterday: ShellChat[] = [];
  const prev7: ShellChat[] = [];
  const prev30: ShellChat[] = [];
  const older: ShellChat[] = [];

  for (const chat of chats) {
    if (chat.pinned) {
      pinned.push(chat);
      continue;
    }
    const ts = chat.updatedAt;
    if (ts >= startOfToday) {
      today.push(chat);
    } else if (ts >= startOfToday - dayMs) {
      yesterday.push(chat);
    } else if (ts >= startOfToday - 7 * dayMs) {
      prev7.push(chat);
    } else if (ts >= startOfToday - 30 * dayMs) {
      prev30.push(chat);
    } else {
      older.push(chat);
    }
  }

  return [
    { label: "Pinned", items: pinned },
    { label: "Today", items: today },
    { label: "Yesterday", items: yesterday },
    { label: "Previous 7 days", items: prev7 },
    { label: "Previous 30 days", items: prev30 },
    { label: "Older", items: older },
  ].filter((g) => g.items.length > 0);
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "GS";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function ChatShell({
  brand,
  user,
  chats,
  activeId,
  onSelect,
  onNewChat,
  onRename,
  onPin,
  onDelete,
  headerRight,
  compactHeader = false,
  defaultCollapsed = false,
  borderless = false,
  className,
  children,
}: ChatShellProps) {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);
  const [query, setQuery] = React.useState("");
  const [renamingId, setRenamingId] = React.useState<string | null>(null);
  const [renameDraft, setRenameDraft] = React.useState("");

  const groups = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = q
      ? chats.filter((c) => c.title.toLowerCase().includes(q))
      : chats;
    const sorted = [...list].sort((a, b) => b.updatedAt - a.updatedAt);
    return groupChatsByRecency(sorted);
  }, [chats, query]);

  const activeChatTitle =
    chats.find((c) => c.id === activeId)?.title || "New research thread";

  const commitRename = (id: string) => {
    const trimmed = renameDraft.trim();
    if (trimmed && onRename) onRename(id, trimmed);
    setRenamingId(null);
  };

  return (
    <div
      className={cn(
        "flex w-full overflow-hidden bg-white",
        borderless ? "" : "rounded-[18px] border border-[#E0E0E0]",
        className,
      )}
    >
      {!collapsed ? (
        <aside className="flex w-[252px] shrink-0 flex-col border-r border-[#E0E0E0] bg-[#F5F5F7]">
          <div
            className={cn(
              "flex shrink-0 items-center justify-between px-3.5",
              compactHeader ? "h-10 border-b border-[#E0E0E0]" : "h-12",
            )}
          >
            <div className="truncate text-[13.5px] font-semibold tracking-[-0.01em] text-[#1D1D1F]">
              {brand ?? "Geotechnical Survey AI"}
            </div>
            <button
              type="button"
              onClick={() => setCollapsed(true)}
              className="cupertino-press inline-flex size-7 items-center justify-center rounded-[6px] text-[#7A7A7A] hover:bg-black/5 hover:text-[#1D1D1F]"
              aria-label="Collapse thread sidebar"
            >
              <PanelLeft className="size-4" strokeWidth={1.5} />
            </button>
          </div>

          <div className="space-y-1 px-2.5 pb-2 pt-0.5">
            <button
              type="button"
              onClick={onNewChat}
              className="cupertino-press flex h-8 w-full items-center gap-2 rounded-[8px] px-2.5 text-[13px] font-normal text-[#1D1D1F] transition-colors hover:bg-white"
            >
              <SquarePen className="size-3.5 text-[#0066CC]" strokeWidth={1.6} />
              <span>New thread</span>
            </button>

            <div className="relative flex items-center">
              <Search
                className="pointer-events-none absolute left-2.5 size-3.5 text-[#7A7A7A]"
                strokeWidth={1.5}
              />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search threads..."
                className="h-8 w-full rounded-[8px] bg-white pl-8 pr-2.5 text-[12.5px] text-[#1D1D1F] placeholder:text-[#7A7A7A] border border-[#E0E0E0] focus:border-[#0066CC] focus:outline-none"
              />
            </div>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto px-2 py-2">
            {groups.length === 0 ? (
              <div className="px-2.5 py-6 text-center text-[12px] text-[#7A7A7A]">
                {query ? "No matching threads" : "No saved threads yet"}
              </div>
            ) : (
              groups.map((group) => (
                <div key={group.label} className="space-y-0.5">
                  <div className="px-2.5 pb-1 text-[11px] font-semibold text-[#7A7A7A]">
                    {group.label}
                  </div>
                  {group.items.map((chat) => {
                    const isActive = chat.id === activeId;
                    const isRenaming = renamingId === chat.id;
                    return (
                      <div
                        key={chat.id}
                        className={cn(
                          "group flex h-8 items-center justify-between gap-1 rounded-[8px] px-2.5 transition-colors",
                          isActive
                            ? "bg-white font-semibold text-[#1D1D1F] border border-[#E0E0E0]"
                            : "text-[#333333] hover:bg-white/70",
                        )}
                      >
                        {isRenaming ? (
                          <input
                            autoFocus
                            value={renameDraft}
                            onChange={(e) => setRenameDraft(e.target.value)}
                            onBlur={() => commitRename(chat.id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") commitRename(chat.id);
                              if (e.key === "Escape") setRenamingId(null);
                            }}
                            className="h-6 w-full rounded-[5px] border border-[#0066CC] bg-white px-2 text-[12.5px] text-[#1D1D1F] focus:outline-none"
                          />
                        ) : (
                          <button
                            type="button"
                            onClick={() => onSelect(chat.id)}
                            className="min-w-0 flex-1 truncate text-left text-[13px]"
                          >
                            <span>{chat.title}</span>
                          </button>
                        )}

                        {(onRename || onPin || onDelete) && !isRenaming ? (
                          <DropdownMenu.Root>
                            <DropdownMenu.Trigger asChild>
                              <button
                                type="button"
                                className={cn(
                                  "inline-flex size-6 shrink-0 items-center justify-center rounded-[6px] text-[#7A7A7A] transition-opacity hover:bg-[#F5F5F7] hover:text-[#1D1D1F]",
                                  isActive
                                    ? "opacity-100"
                                    : "opacity-0 group-hover:opacity-100 focus:opacity-100",
                                )}
                                aria-label="Thread options"
                              >
                                <MoreHorizontal className="size-3.5" strokeWidth={1.75} />
                              </button>
                            </DropdownMenu.Trigger>
                            <DropdownMenu.Portal>
                              <DropdownMenu.Content
                                align="end"
                                sideOffset={4}
                                className="z-50 w-40 rounded-[12px] border border-[#E0E0E0] bg-white p-1"
                              >
                                {onPin ? (
                                  <DropdownMenu.Item
                                    onSelect={() =>
                                      onPin(chat.id, !chat.pinned)
                                    }
                                    className="flex h-8 cursor-pointer items-center gap-2 rounded-[6px] px-2.5 text-[13px] text-[#1D1D1F] outline-none hover:bg-[#F5F5F7]"
                                  >
                                    {chat.pinned ? (
                                      <PinOff className="size-3.5" />
                                    ) : (
                                      <Pin className="size-3.5" />
                                    )}
                                    <span>{chat.pinned ? "Unpin" : "Pin"}</span>
                                  </DropdownMenu.Item>
                                ) : null}
                                {onRename ? (
                                  <DropdownMenu.Item
                                    onSelect={() => {
                                      setRenamingId(chat.id);
                                      setRenameDraft(chat.title);
                                    }}
                                    className="flex h-8 cursor-pointer items-center gap-2 rounded-[6px] px-2.5 text-[13px] text-[#1D1D1F] outline-none hover:bg-[#F5F5F7]"
                                  >
                                    <Pencil className="size-3.5" />
                                    <span>Rename</span>
                                  </DropdownMenu.Item>
                                ) : null}
                                {onDelete ? (
                                  <DropdownMenu.Item
                                    onSelect={() => onDelete(chat.id)}
                                    className="flex h-8 cursor-pointer items-center gap-2 rounded-[6px] px-2.5 text-[13px] text-[#C91919] outline-none hover:bg-[#FFF2F2]"
                                  >
                                    <Trash2 className="size-3.5" />
                                    <span>Delete</span>
                                  </DropdownMenu.Item>
                                ) : null}
                              </DropdownMenu.Content>
                            </DropdownMenu.Portal>
                          </DropdownMenu.Root>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>

          {user && user.name ? (
            <div className="flex shrink-0 items-center gap-2.5 border-t border-[#E0E0E0] px-3 py-2.5">
              <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-[#1D1D1F] text-[11px] font-semibold text-white">
                {getInitials(user.name)}
              </div>
              <div className="min-w-0">
                <div className="truncate text-[12.5px] font-semibold leading-tight text-[#1D1D1F]">
                  {user.name}
                </div>
                {user.plan || user.email ? (
                  <div className="truncate text-[11px] leading-tight text-[#7A7A7A]">
                    {user.plan || user.email}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </aside>
      ) : null}

      <div className="relative flex min-w-0 flex-1 flex-col bg-white">
        <div
          className={cn(
            "flex shrink-0 items-center justify-between gap-3 bg-white",
            compactHeader
              ? "h-10 border-b border-[#F0F0F0] px-3.5"
              : "h-11 px-4 sm:px-6",
          )}
        >
          <div className="flex min-w-0 items-center gap-2">
            {collapsed ? (
              <>
                <button
                  type="button"
                  onClick={() => setCollapsed(false)}
                  className="cupertino-press inline-flex size-7 items-center justify-center rounded-[6px] text-[#7A7A7A] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"
                  aria-label="Open thread sidebar"
                  title={`Open threads (${chats.length})`}
                >
                  <PanelLeft className="size-4" strokeWidth={1.5} />
                </button>
                <button
                  type="button"
                  onClick={onNewChat}
                  className="cupertino-press inline-flex size-7 items-center justify-center rounded-[6px] text-[#7A7A7A] hover:bg-[#F5F5F7] hover:text-[#1D1D1F]"
                  aria-label="New thread"
                  title="New thread"
                >
                  <SquarePen className="size-3.5" strokeWidth={1.5} />
                </button>
              </>
            ) : null}
            <span className="truncate text-[13px] font-normal text-[#7A7A7A]">
              {activeChatTitle}
            </span>
          </div>

          {headerRight ? (
            <div className="flex shrink-0 items-center gap-2">{headerRight}</div>
          ) : null}
        </div>

        <div className="min-h-0 flex-1">{children}</div>
      </div>
    </div>
  );
}
