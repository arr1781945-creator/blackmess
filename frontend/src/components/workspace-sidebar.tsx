"use client"

"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  HomeIcon,
  MessageIcon,
  BellIcon,
  MoreIcon,
  BookmarkIcon,
  FileIcon,
  AppsIcon,
} from "./icons"

const workspaces = [
  { id: 1, name: "BlackMess", initial: "B", color: "bg-emerald-600" },
  { id: 2, name: "Tim Internal", initial: "D", color: "bg-blue-600" },
  { id: 3, name: "Pemantauan", initial: "M", color: "bg-orange-600" },
]

export function WorkspaceSidebar({ activePage, onPageChange, currentUser, onLogout }: { activePage: string, onPageChange: (page: string) => void, currentUser?: {name:string,avatar:string}, onLogout?: () => void }) {
  const [activeWorkspace, setActiveWorkspace] = useState(1)

  return (
    <div className="flex flex-col w-[70px] bg-[#0d0d0d] border-r border-border items-center py-3 gap-2">
      {/* Workspaces */}
      <div className="flex flex-col gap-2 pb-3 border-b border-border">
        {workspaces.map((workspace) => (
          <button
            key={workspace.id}
            onClick={() => setActiveWorkspace(workspace.id)}
            className={cn(
              "w-9 h-9 rounded-lg flex items-center justify-center text-sm font-semibold transition-all",
              workspace.color,
              activeWorkspace === workspace.id
                ? "ring-2 ring-white ring-offset-2 ring-offset-[#0d0d0d]"
                : "opacity-70 hover:opacity-100"
            )}
          >
            {workspace.initial}
          </button>
        ))}
        <button className="w-9 h-9 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition-colors border border-dashed border-border">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </div>

      {/* Main Nav */}
      <div className="flex flex-col gap-1 flex-1 pt-2">
        <NavButton icon={HomeIcon} label="Beranda" active={activePage === "home"} onClick={() => onPageChange("home")} />
        <NavButton icon={MessageIcon} label="Pesan" badge={3} active={activePage === "dms"} onClick={() => onPageChange("dms")} />
        <NavButton icon={BellIcon} label="Aktivitas" active={activePage === "activity"} onClick={() => onPageChange("activity")} />
        <NavButton icon={BookmarkIcon} label="Tersimpan" active={activePage === "saved"} onClick={() => onPageChange("saved")} />
        <NavButton icon={FileIcon} label="Berkas" active={activePage === "files"} onClick={() => onPageChange("files")} />
        <NavButton icon={AppsIcon} label="Aplikasi" active={activePage === "apps"} onClick={() => onPageChange("apps")} />
        <NavButton icon={MoreIcon} label="Lagi" active={activePage === "more"} onClick={() => onPageChange("more")} />
      </div>

      {/* Profile */}
      <div className="pt-2 border-t border-border">
        <button className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-semibold text-white">
          J
        </button>
      </div>
    </div>
  )
}

function NavButton({
  icon: Icon,
  label,
  active,
  badge,
  onClick,
}: {
  icon: React.FC<{ className?: string }>
  label: string
  active?: boolean
  badge?: number
  onClick?: () => void
}) {
  return (
    <button
      suppressHydrationWarning
      onClick={onClick}
      className={cn(
        "w-10 h-10 rounded-lg flex flex-col items-center justify-center gap-0.5 transition-colors relative",
        active
          ? "bg-accent text-foreground"
          : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
      )}
      title={label}
    >
      <Icon className="w-5 h-5" />
      <span className="text-[9px]" suppressHydrationWarning>{label}</span>
      {badge && (
        <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-[10px] font-medium flex items-center justify-center text-white">
          {badge}
        </span>
      )}
    </button>
  )
}
