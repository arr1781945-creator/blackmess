import { useState, useEffect, useRef, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { HashIcon, StarIcon, UsersIcon, MoreIcon, PaperclipIcon, SmileIcon, SendIcon, MicIcon, VideoIcon, PhoneIcon } from "./icons"

const EMOJIS = ['😀','😂','🥰','😎','🤔','😴','🥳','😭','🔥','💪','👍','👎','❤️','💯','🎉','✅','⚠️','🚀','💻','📱']
const REACTIONS = ['👍','❤️','😂','😮','😢','🔥']
import { createWebSocket, fetchMessages, API_URL, WS_URL, getToken } from '../lib/api'


export function ChatArea({ channel = "umum", currentUser, onVideoCall, onProfile }: {
  channel?: string
  currentUser?: { name: string; avatar: string }
  onVideoCall?: () => void
  onProfile?: () => void
}) {
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState("")
  const [showEmoji, setShowEmoji] = useState(false)
  const [wsStatus, setWsStatus] = useState<'connecting'|'connected'|'disconnected'>('disconnected')
  const [activeThread, setActiveThread] = useState<any | null>(null)
  const [threadInput, setThreadInput] = useState("")
  const [editingId, setEditingId] = useState<string|null>(null)
  const [editText, setEditText] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [showSearch, setShowSearch] = useState(false)
  const [pinnedMessages, setPinnedMessages] = useState<string[]>([])
  const [showReaction, setShowReaction] = useState<string|null>(null)
  const [mentionQuery, setMentionQuery] = useState("")
  const [showMention, setShowMention] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // Load messages dari backend
    fetchMessages(channel).then(msgs => {
      if (Array.isArray(msgs)) {
        setMessages(msgs.map((m: any) => ({
          id: m.id,
          user: m.sender_name || m.sender || 'Unknown',
          avatar: (m.sender_name || 'U')[0].toUpperCase(),
          color: 'from-gray-700 to-gray-800',
          time: new Date(m.created_at).toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'}),
          content: m.content || m.message || '',
          replies: [], reactions: {}, pinned: false,
        })))
      }
    })
    connectWS()
    setActiveThread(null)
    setShowSearch(false)
    setSearchQuery("")
    return () => wsRef.current?.close()
  }, [channel])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const connectWS = () => {
    wsRef.current?.close()
    setWsStatus('connecting')
    const ws = new WebSocket(`${WS_URL}/${channel}/`)
    wsRef.current = ws
    ws.onopen = () => setWsStatus('connected')
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'message') {
        setMessages(prev => [...prev, {
          id: data.id || Date.now().toString(),
          user: data.user, avatar: data.avatar,
          color: 'from-gray-700 to-gray-800',
          time: data.time, content: data.message,
          replies: [], reactions: {}, pinned: false
        }])
      }
    }
    ws.onerror = () => setWsStatus('disconnected')
    ws.onclose = () => setWsStatus('disconnected')
  }

  const send = () => {
    if (!input.trim()) return
    const now = new Date().toLocaleTimeString('en-US', {hour:'numeric', minute:'2-digit'})
    const msgId = Date.now().toString()
    const newMsg = {
      id: msgId,
      user: currentUser?.name || 'Saya',
      avatar: currentUser?.avatar || 'S',
      color: 'from-gray-700 to-gray-800',
      time: now, content: input.trim(),
      replies: [], reactions: {}, pinned: false
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: input.trim(),
        user: currentUser?.name || 'Saya',
        avatar: currentUser?.avatar || 'S',
        id: msgId, time: now,
      }))
    } else {
      setMessages(prev => [...prev, newMsg])
    }
    setInput("")
  }

  const deleteMessage = (id: string) => {
    setMessages(prev => prev.filter(m => m.id !== id))
    if (activeThread?.id === id) setActiveThread(null)
  }

  const editMessage = (id: string) => {
    setMessages(prev => prev.map(m => m.id === id ? {...m, content: editText, edited: true} : m))
    if (activeThread?.id === id) setActiveThread((prev: any) => ({...prev, content: editText, edited: true}))
    setEditingId(null)
    setEditText("")
  }

  const pinMessage = (id: string) => {
    setMessages(prev => prev.map(m => m.id === id ? {...m, pinned: !m.pinned} : m))
    setPinnedMessages(prev => prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id])
  }

  const addReaction = (msgId: string, emoji: string) => {
    setMessages(prev => prev.map(m => {
      if (m.id !== msgId) return m
      const reactions = {...(m.reactions || {})}
      reactions[emoji] = (reactions[emoji] || 0) + 1
      return {...m, reactions}
    }))
    setShowReaction(null)
  }

  const sendReply = (msgId: string) => {
    if (!threadInput.trim()) return
    const now = new Date().toLocaleTimeString('en-US', {hour:'numeric', minute:'2-digit'})
    const reply = {
      id: `r${Date.now()}`,
      user: currentUser?.name || 'Saya',
      avatar: currentUser?.avatar || 'S',
      color: 'from-gray-700 to-gray-800',
      time: now, content: threadInput.trim()
    }
    setMessages(prev => prev.map(m => m.id === msgId ? {...m, replies: [...(m.replies||[]), reply]} : m))
    if (activeThread?.id === msgId) {
      setActiveThread((prev: any) => ({...prev, replies: [...(prev.replies||[]), reply]}))
    }
    setThreadInput("")
  }

  // Handle @mention
  const handleInput = (val: string) => {
    setInput(val)
    const lastWord = val.split(' ').pop() || ''
    if (lastWord.startsWith('@') && lastWord.length > 1) {
      setMentionQuery(lastWord.slice(1))
      setShowMention(true)
    } else {
      setShowMention(false)
    }
  }

  const insertMention = (name: string) => {
    const words = input.split(' ')
    words[words.length - 1] = `@${name} `
    setInput(words.join(' '))
    setShowMention(false)
    inputRef.current?.focus()
  }

  // File upload
  const onDrop = useCallback((files: File[]) => {
    files.forEach(file => {
      const url = URL.createObjectURL(file)
      const size = file.size < 1024*1024
        ? `${(file.size/1024).toFixed(1)} KB`
        : `${(file.size/1024/1024).toFixed(1)} MB`
      const now = new Date().toLocaleTimeString('en-US', {hour:'numeric', minute:'2-digit'})
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        user: currentUser?.name || 'Saya',
        avatar: currentUser?.avatar || 'S',
        color: 'from-gray-700 to-gray-800',
        time: now, content: '',
        file: { name: file.name, url, type: file.type, size },
        replies: [], reactions: {}, pinned: false
      }])
    })
  }, [currentUser])

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop, noClick: true,
    accept: { 'image/*': [], 'application/pdf': [], 'text/*': [] },
    maxSize: 10 * 1024 * 1024,
  })

  const filteredMessages = searchQuery
    ? messages.filter(m => m.content?.toLowerCase().includes(searchQuery.toLowerCase()) || m.user?.toLowerCase().includes(searchQuery.toLowerCase()))
    : messages

  const pinnedList = messages.filter(m => m.pinned)

  const statusColor = { connected:'text-green-400', connecting:'text-yellow-400', disconnected:'text-gray-500' }[wsStatus]
  const statusLabel = { connected:'● Live', connecting:'● Menghubungkan...', disconnected:'● Offline' }[wsStatus]

  return (
    <div {...getRootProps()} className="flex flex-1 min-w-0 h-full overflow-hidden relative">
      <input {...getInputProps()}/>

      {/* Drag overlay */}
      {isDragActive && (
        <div className="absolute inset-0 bg-black/80 z-50 flex items-center justify-center border-2 border-dashed border-white rounded-xl">
          <div className="text-center">
            <svg className="w-16 h-16 text-white mx-auto mb-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            <p className="text-white text-xl font-bold">Lepaskan file di sini!</p>
          </div>
        </div>
      )}

      {/* Main chat */}
      <div className={`flex flex-col ${activeThread ? 'w-3/5' : 'flex-1'} min-w-0 h-full`}>

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-background flex-shrink-0">
          <div className="flex items-center gap-2">
            <HashIcon className="w-5 h-5 text-muted-foreground"/>
            <h2 className="font-semibold text-foreground">{channel}</h2>
            <StarIcon className="w-4 h-4 text-muted-foreground cursor-pointer"/>
            <span className={`text-xs ${statusColor} ml-1`}>{statusLabel}</span>
          </div>
          <div className="flex items-center gap-1">
            {/* Search toggle */}
            <button onClick={() => setShowSearch(!showSearch)}
              className={`p-1.5 rounded text-muted-foreground hover:bg-accent ${showSearch ? 'bg-accent text-foreground' : ''}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </button>
            <button onClick={connectWS} className="p-1.5 rounded text-muted-foreground hover:bg-accent">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
            </button>
            <button onClick={onVideoCall} className="p-1.5 rounded text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"><PhoneIcon className="w-4 h-4"/></button>
            <button onClick={onVideoCall} className="p-1.5 rounded text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"><VideoIcon className="w-4 h-4"/></button>
            <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><UsersIcon className="w-4 h-4"/></button>
            <button className="p-1.5 rounded text-muted-foreground hover:bg-accent"><MoreIcon className="w-4 h-4"/></button>
            <button onClick={onProfile}
              className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white text-xs font-bold hover:opacity-80 transition-opacity flex-shrink-0 ml-1">
              {currentUser?.avatar || 'U'}
            </button>
          </div>
        </div>

        {/* Search bar */}
        {showSearch && (
          <div className="px-4 py-2 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-2 bg-accent rounded-lg px-3 py-2">
              <svg className="w-4 h-4 text-muted-foreground flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              <input autoFocus type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                placeholder="Cari pesan..."
                className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground"/>
              {searchQuery && <span className="text-xs text-muted-foreground">{filteredMessages.length} hasil</span>}
            </div>
          </div>
        )}

        {/* Pinned messages */}
        {pinnedList.length > 0 && (
          <div className="px-4 py-2 border-b border-border bg-accent/30 flex-shrink-0">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
              <span className="font-medium">{pinnedList.length} pesan disematkan</span>
              <span className="truncate flex-1">{pinnedList[pinnedList.length-1]?.content}</span>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1">
          <div className="text-center py-6">
            <div className="w-12 h-12 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-3">
              <HashIcon className="w-6 h-6 text-white"/>
            </div>
            <h3 className="font-bold text-foreground">#{channel}</h3>
            <p className="text-muted-foreground text-sm mt-1">Awal dari channel #{channel}</p>
          </div>

          {filteredMessages.map((m) => (
            <div key={m.id} className="group relative">
              <div className={`flex items-start gap-3 px-2 py-1.5 rounded-xl hover:bg-accent/30 transition-colors ${m.pinned ? 'bg-yellow-500/5 border-l-2 border-yellow-500/40' : ''}`}>
                <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">
                  {m.avatar}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="font-semibold text-foreground text-sm">{m.user}</span>
                    <span className="text-xs text-muted-foreground">{m.time}</span>
                    {m.edited && <span className="text-xs text-muted-foreground">(diedit)</span>}
                    {m.pinned && <span className="text-xs text-yellow-500">📌</span>}
                  </div>

                  {editingId === m.id ? (
                    <div className="mt-1">
                      <input type="text" value={editText} onChange={e => setEditText(e.target.value)}
                        onKeyDown={e => { if(e.key==='Enter') editMessage(m.id); if(e.key==='Escape') setEditingId(null) }}
                        className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-sm outline-none focus:border-white"
                        autoFocus/>
                      <div className="flex gap-2 mt-1">
                        <button onClick={() => editMessage(m.id)} className="text-xs text-white bg-gray-700 px-2 py-1 rounded">Simpan</button>
                        <button onClick={() => setEditingId(null)} className="text-xs text-muted-foreground">Batal</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {m.content && <p className="text-sm text-foreground mt-0.5 break-words">{m.content}</p>}
                      {m.file && (
                        <div className="mt-1.5 max-w-xs">
                          {m.file.type.startsWith('image/') ? (
                            <div className="rounded-xl overflow-hidden border border-border">
                              <img src={m.file.url} alt={m.file.name} className="max-w-full max-h-48 object-cover"/>
                              <div className="px-3 py-1.5 bg-accent flex items-center justify-between">
                                <span className="text-xs text-muted-foreground truncate">{m.file.name}</span>
                                <span className="text-xs text-muted-foreground ml-2">{m.file.size}</span>
                              </div>
                            </div>
                          ) : (
                            <a href={m.file.url} download={m.file.name}
                              className="flex items-center gap-3 p-3 rounded-xl bg-accent border border-border hover:bg-muted transition-colors">
                              <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-foreground text-sm font-medium truncate">{m.file.name}</div>
                                <div className="text-muted-foreground text-xs">{m.file.size}</div>
                              </div>
                            </a>
                          )}
                        </div>
                      )}
                    </>
                  )}

                  {/* Reactions display */}
                  {m.reactions && Object.keys(m.reactions).length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {Object.entries(m.reactions).map(([emoji, count]: any) => (
                        <button key={emoji} onClick={() => addReaction(m.id, emoji)}
                          className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-accent border border-border text-xs hover:bg-muted">
                          <span>{emoji}</span>
                          <span className="text-muted-foreground">{count}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Reply count */}
                  {m.replies?.length > 0 && (
                    <button onClick={() => setActiveThread(m)}
                      className="flex items-center gap-1.5 mt-1.5 text-xs text-white/60 hover:text-white font-medium">
                      <div className="flex -space-x-1">
                        {m.replies.slice(0,3).map((r: any, i: number) => (
                          <div key={i} className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center text-white text-[8px] font-bold border border-background">
                            {r.avatar[0]}
                          </div>
                        ))}
                      </div>
                      {m.replies.length} balasan
                    </button>
                  )}
                </div>

                {/* Action buttons hover */}
                <div className="hidden group-hover:flex items-center gap-1 flex-shrink-0 bg-background border border-border rounded-lg p-0.5">
                  {/* Reaction */}
                  <div className="relative">
                    <button onClick={() => setShowReaction(showReaction === m.id ? null : m.id)}
                      className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    </button>
                    {showReaction === m.id && (
                      <div className="absolute bottom-8 right-0 bg-background border border-border rounded-xl p-2 flex gap-1 z-50 shadow-lg">
                        {REACTIONS.map(e => (
                          <button key={e} onClick={() => addReaction(m.id, e)}
                            className="text-lg hover:scale-125 transition-transform p-1">
                            {e}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Reply */}
                  <button onClick={() => setActiveThread(m)}
                    className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>
                  </button>

                  {/* Pin */}
                  <button onClick={() => pinMessage(m.id)}
                    className={`p-1.5 rounded hover:bg-accent ${m.pinned ? 'text-yellow-500' : 'text-muted-foreground hover:text-foreground'}`}>
                    <svg className="w-3.5 h-3.5" fill={m.pinned ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
                  </button>

                  {/* Edit (only own messages) */}
                  {m.user === (currentUser?.name || 'Saya') && (
                    <button onClick={() => { setEditingId(m.id); setEditText(m.content) }}
                      className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                    </button>
                  )}

                  {/* Delete (only own messages) */}
                  {m.user === (currentUser?.name || 'Saya') && (
                    <button onClick={() => deleteMessage(m.id)}
                      className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-red-400">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={bottomRef}/>
        </div>

        {/* Input */}
        <div className="p-4 border-t border-border flex-shrink-0 relative">
          {/* Emoji picker */}
          {showEmoji && (
            <div className="absolute bottom-20 left-4 bg-background border border-border rounded-xl p-3 shadow-xl z-50">
              <div className="grid grid-cols-5 gap-1">
                {EMOJIS.map(e => (
                  <button key={e} onClick={() => { setInput(prev => prev + e); setShowEmoji(false) }}
                    className="text-xl p-2 rounded-lg hover:bg-accent">
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Mention picker */}
          {showMention && (
            <div className="absolute bottom-20 left-4 bg-background border border-border rounded-xl p-2 shadow-xl z-50 w-48">
              <p className="text-xs text-muted-foreground px-2 mb-1">Anggota</p>
              {['Akbar', 'Admin', 'Anggota'].filter(u => u.toLowerCase().includes(mentionQuery.toLowerCase())).map(u => (
                <button key={u} onClick={() => insertMention(u)}
                  className="flex items-center gap-2 w-full px-3 py-2 rounded-lg hover:bg-accent text-sm text-foreground">
                  <div className="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-white text-xs font-bold">{u[0]}</div>
                  {u}
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center gap-2 bg-accent rounded-xl px-4 py-2.5 border border-border">
            <button onClick={open} className="text-muted-foreground hover:text-foreground flex-shrink-0">
              <PaperclipIcon className="w-5 h-5"/>
            </button>
            <input ref={inputRef} type="text" value={input}
              onChange={e => handleInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              placeholder={`Pesan ke #${channel} — ketik @ untuk mention`}
              className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground min-w-0"/>
            <div className="flex items-center gap-1 flex-shrink-0">
              <button onClick={() => setShowEmoji(!showEmoji)} className="text-muted-foreground hover:text-foreground">
                <SmileIcon className="w-5 h-5"/>
              </button>
              <button className="text-muted-foreground hover:text-foreground"><MicIcon className="w-5 h-5"/></button>
              <button onClick={send} className={`p-1.5 rounded-lg transition-colors ${input ? 'bg-white text-black' : 'text-muted-foreground'}`}>
                <SendIcon className="w-4 h-4"/>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Thread Panel */}
      {activeThread && (
        <div className="w-2/5 flex flex-col border-l border-border bg-background flex-shrink-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
            <div>
              <h3 className="text-foreground font-semibold text-sm">Thread</h3>
              <p className="text-muted-foreground text-xs">#{channel}</p>
            </div>
            <button onClick={() => setActiveThread(null)} className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
          <div className="p-4 border-b border-border flex-shrink-0">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-gray-800 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">{activeThread.avatar}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-semibold text-foreground text-sm">{activeThread.user}</span>
                  <span className="text-xs text-muted-foreground">{activeThread.time}</span>
                </div>
                <p className="text-sm text-foreground mt-0.5">{activeThread.content}</p>
              </div>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeThread.replies?.length === 0 && (
              <p className="text-center text-muted-foreground text-sm py-4">Belum ada balasan</p>
            )}
            {activeThread.replies?.map((r: any) => (
              <div key={r.id} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">{r.avatar}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="font-semibold text-foreground text-sm">{r.user}</span>
                    <span className="text-xs text-muted-foreground">{r.time}</span>
                  </div>
                  <p className="text-sm text-foreground mt-0.5 break-words">{r.content}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-border flex-shrink-0">
            <div className="flex items-center gap-2 bg-accent rounded-xl px-3 py-2 border border-border">
              <input type="text" value={threadInput}
                onChange={e => setThreadInput(e.target.value)}
                onKeyDown={e => e.key==='Enter' && sendReply(activeThread.id)}
                placeholder="Balas thread..."
                className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground"/>
              <button onClick={() => sendReply(activeThread.id)}
                className={`p-1.5 rounded-lg flex-shrink-0 ${threadInput ? 'bg-white text-black' : 'text-muted-foreground'}`}>
                <SendIcon className="w-4 h-4"/>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
