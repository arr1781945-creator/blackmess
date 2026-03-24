"use client"

"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  HashIcon,
  ChevronDownIcon,
  PlusIcon,
  SearchIcon,
  LockIcon,
} from "./icons"

const channels = [
  { id: 1, name: "umum", private: false },
  { id: 2, name: "acak", private: false },
  { id: 3, name: "pengumuman", private: true },
  { id: 4, name: "tim-internal", private: false },
  { id: 5, name: "rekayasa", private: false },
]

const directMessages: any[] = []

export function ChannelSidebar({ onChannelChange }: { onChannelChange?: (channel: string) => void }) {
  const [activeChannel, setActiveChannel] = useState(1)
  const [activeDM, setActiveDM] = useState<number | null>(null)
  const [channelsExpanded, setChannelsExpanded] = useState(true)
  const [dmsExpanded, setDmsExpanded] = useState(true)

  const handleChannelClick = (id: number) => {
    setActiveChannel(id)
    setActiveDM(null)
    const ch = channels.find(c => c.id === id)
    if (ch) onChannelChange?.(ch.name)
  }

  const handleDMClick = (id: number) => {
    setActiveDM(id)
    setActiveChannel(0)
  }

  return (
    <div className="flex flex-col w-[260px] bg-sidebar border-r border-sidebar-border">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-foreground">Acme Inc</h2>
          <ChevronDownIcon className="w-4 h-4 text-muted-foreground" />
        </div>
        <button className="w-8 h-8 rounded-md flex items-center justify-center hover:bg-accent transition-colors text-muted-foreground hover:text-foreground">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
        </button>
      </div>

      {/* Search */}
      <div className="px-3 py-2">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/50 text-muted-foreground">
          <SearchIcon className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent text-sm flex-1 outline-none placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {/* Channels Section */}
        <div className="mb-4">
          <button
            onClick={() => setChannelsExpanded(!channelsExpanded)}
            className="flex items-center gap-1 px-2 py-1 w-full text-left text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronDownIcon
              className={cn(
                "w-3 h-3 transition-transform",
                !channelsExpanded && "-rotate-90"
              )}
            />
            <span className="font-medium">Channels</span>
          </button>
          {channelsExpanded && (
            <div className="mt-1 space-y-0.5">
              {channels.map((channel) => (
                <button
                  key={channel.id}
                  onClick={() => handleChannelClick(channel.id)}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 w-full rounded-md text-sm transition-colors",
                    activeChannel === channel.id
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  )}
                >
                  {channel.private ? (
                    <LockIcon className="w-4 h-4 shrink-0" />
                  ) : (
                    <HashIcon className="w-4 h-4 shrink-0" />
                  )}
                  <span className="truncate">{channel.name}</span>
                </button>
              ))}
              <button className="flex items-center gap-2 px-2 py-1.5 w-full rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors">
                <PlusIcon className="w-4 h-4" />
                <span>Add channels</span>
              </button>
            </div>
          )}
        </div>

        {/* Direct Messages Section */}
        <div>
          <button
            onClick={() => setDmsExpanded(!dmsExpanded)}
            className="flex items-center gap-1 px-2 py-1 w-full text-left text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronDownIcon
              className={cn(
                "w-3 h-3 transition-transform",
                !dmsExpanded && "-rotate-90"
              )}
            />
            <span className="font-medium">Direct Messages</span>
          </button>
          {dmsExpanded && (
            <div className="mt-1 space-y-0.5">
              {directMessages.map((dm) => (
                <button
                  key={dm.id}
                  onClick={() => handleDMClick(dm.id)}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 w-full rounded-md text-sm transition-colors",
                    activeDM === dm.id
                      ? "bg-accent text-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  )}
                >
                  <div className="relative">
                    <div className="w-5 h-5 rounded-sm bg-gradient-to-br from-gray-600 to-gray-700 flex items-center justify-center text-[10px] font-medium text-white">
                      {dm.avatar}
                    </div>
                    <span
                      className={cn(
                        "absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-sidebar",
                        dm.status === "online" && "bg-green-500",
                        dm.status === "offline" && "bg-muted",
                        dm.status === "away" && "bg-yellow-500",
                        dm.status === "dnd" && "bg-red-500"
                      )}
                    />
                  </div>
                  <span className="truncate">{dm.name}</span>
                </button>
              ))}
              <button className="flex items-center gap-2 px-2 py-1.5 w-full rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors">
                <PlusIcon className="w-4 h-4" />
                <span>Add teammates</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
