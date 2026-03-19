"use client"
import { useState, useEffect, useRef, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { HashIcon, StarIcon, UsersIcon, MoreIcon, PaperclipIcon, SmileIcon, SendIcon, MicIcon, VideoIcon, PhoneIcon } from "./icons"

const EMOJIS = ['😀','😂','🥰','😎','🤔','😴','🥳','😭','🔥','💪','👍','👎','❤️','💯','🎉','✅','⚠️','🚀','💻','📱']

const CHANNEL_DATA: Record<string, any[]> = {
  'umum': [],
  'acak': [],
  'pengumuman': [],
  'tim-internal': [],
  'rekayasa': [],
  'pemantauan-transaksi': [],
}

const WS_URL = 'ws://localhost:8002/ws/chat'

export function ChatArea({ channel = "umum", currentUser }: {
  channel?: string
  currentUser?: { name: string; avatar: string }
}) {
  const [messages, setMessages] = useState<any[]>(CHANNEL_DATA[channel] || [])
  const [input, setInput] = useState("")
  const [showEmoji, setShowEmoji] = useState(false)
  const [wsStatus, setWsStatus] = useState<'connecting'|'connected'|'disconnected'>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Reset messages saat channel berubah
  useEffect(() => {
    setMessages(CHANNEL_DATA[channel] || [])
    connectWS()
    return () => wsRef.current?.close()
  }, [channel])

  // Auto scroll ke bawah
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const connectWS = () => {
    wsRef.current?.close()
    setWsStatus('connecting')

    const ws = new WebSocket(`${WS_URL}/${channel}/`)
    wsRef.current = ws

    ws.onopen = () => {
      setWsStatus('connected')
      console.log(`WS connected: ${channel}`)
    }

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          id: data.id || Date.now().toString(),
          user: data.user,
          avatar: data.avatar,
          color: 'from-violet-500 to-purple-600',
          time: data.time,
          content: data.message,
          isNew: true
        }])
      }
    }

    ws.onerror = () => setWsStatus('disconnected')
    ws.onclose = () => setWsStatus('disconnected')
  }

  const send = () => {
    if (!input.trim()) return
    const now = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    const msgId = Date.now().toString()

    // Kirim via WebSocket kalau connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: input.trim(),
        user: currentUser?.name || 'Saya',
        avatar: currentUser?.avatar || 'S',
        id: msgId,
        time: now,
      }))
    } else {
      // Fallback - tampilkan langsung
      setMessages(prev => [...prev, {
        id: msgId,
        user: currentUser?.name || 'Saya',
        avatar: currentUser?.avatar || 'S',
        color: 'from-violet-500 to-purple-600',
        time: now,
        content: input.trim(),
      }])
    }
    setInput("")
  }

  const statusColor = {
    connected: 'text-green-400',
    connecting: 'text-yellow-400',
    disconnected: 'text-gray-500'
  }[wsStatus]

  const statusLabel = {
    connected: '● Live',
    connecting: '● Menghubungkan...',
    disconnected: '● Offline'
  }[wsStatus]

  return (
    <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-background flex-shrink-0">
        <div className="flex items-center gap-2">
          <HashIcon className="w-5 h-5 text-muted-foreground"/>
          <h2 className="font-semibold text-foreground">{channel}</h2>
          <StarIcon className="w-4 h-4 text-muted-foreground cursor-pointer"/>
          <span className={`text-xs ${statusColor} ml-1`}>{statusLabel}</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={connectWS} title="Reconnect" className="p-1.5 rounded text-muted-foreground hover:bg-accent">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
          </button>
          <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><PhoneIcon className="w-4 h-4"/></button>
          <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><VideoIcon className="w-4 h-4"/></button>
          <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><UsersIcon className="w-4 h-4"/></button>
          <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><MoreIcon className="w-4 h-4"/></button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="text-center py-6">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-3">
            <HashIcon className="w-6 h-6 text-white"/>
          </div>
          <h3 className="font-bold text-foreground">#{channel}</h3>
          <p className="text-muted-foreground text-sm mt-1">Awal dari channel #{channel}</p>
        </div>

        {messages.map((m, i) => (
          <div key={m.id || i} className={`flex items-start gap-3 ${m.isNew ? 'animate-pulse-once' : ''}`}>
            <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${m.color || 'from-gray-500 to-gray-600'} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
              {m.avatar}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="font-semibold text-foreground text-sm">{m.user}</span>
                <span className="text-xs text-muted-foreground">{m.time}</span>
              </div>
              <p className="text-sm text-foreground mt-0.5 break-words">{m.content}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef}/>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border flex-shrink-0 relative">
        {showEmoji && (
          <div className="absolute bottom-16 left-4 bg-[#1a1a1a] border border-border rounded-xl p-3 shadow-xl z-50">
            <div className="grid grid-cols-5 gap-1">
              {EMOJIS.map(e => (
                <button key={e} onClick={() => { setInput(prev => prev + e); setShowEmoji(false) }}
                  className="text-xl p-2 rounded-lg hover:bg-accent transition-colors">
                  {e}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 bg-accent rounded-xl px-4 py-2.5 border border-border">
          <button className="text-muted-foreground hover:text-foreground flex-shrink-0">
            <PaperclipIcon className="w-5 h-5"/>
          </button>
          <input
            type="text" value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder={`Pesan ke #${channel}`}
            className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground min-w-0"
          />
          <div className="flex items-center gap-1 flex-shrink-0">
            <button onClick={() => setShowEmoji(!showEmoji)}
              className="text-muted-foreground hover:text-foreground">
              <SmileIcon className="w-5 h-5"/>
            </button>
            <button className="text-muted-foreground hover:text-foreground">
              <MicIcon className="w-5 h-5"/>
            </button>
            <button onClick={send}
              className={`p-1.5 rounded-lg transition-colors ${input ? 'bg-white text-black' : 'text-muted-foreground'}`}>
              <SendIcon className="w-4 h-4"/>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
