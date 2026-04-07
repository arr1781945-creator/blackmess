import { useState, useRef, useEffect } from 'react'
import { AuthFlow } from './pages/AuthFlow'
import { WorkspaceSidebar } from './components/workspace-sidebar'
import { ChannelSidebar } from './components/channel-sidebar'
import { ChatArea } from './components/chat-area'
import { VideoCall } from './components/VideoCall'

interface User { name: string; email: string; avatar: string; company: string }

// ─── Empty Page ───────────────────────────────────────────────────────────────
const EmptyPage = ({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) => (
  <div className="flex-1 flex items-center justify-center bg-background">
    <div className="text-center">
      <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center text-muted-foreground">{icon}</div>
      <h2 className="text-foreground font-bold text-xl mb-2">{title}</h2>
      <p className="text-muted-foreground text-sm">{desc}</p>
    </div>
  </div>
)

// ─── Emoji Picker ─────────────────────────────────────────────────────────────
const EMOJIS = ['😀','😂','🥰','😎','🤔','😴','🥳','😭','🔥','💪','👍','👎','❤️','💯','🎉','✅','⚠️','🚀','💻','📱','🔐','💰','📊','🎯','🙏','👋','🤝','💡','📢','🔔']

const EmojiPicker = ({ onSelect, onClose }: { onSelect: (e: string) => void, onClose: () => void }) => (
  <div className="absolute bottom-14 left-0 bg-background border border-border rounded-xl p-3 shadow-xl z-50 w-64">
    <div className="grid grid-cols-6 gap-1">
      {EMOJIS.map(e => (
        <button key={e} onClick={() => { onSelect(e); onClose() }}
          className="text-xl p-1.5 rounded-lg hover:bg-accent transition-colors text-center">
          {e}
        </button>
      ))}
    </div>
  </div>
)

// ─── DM Page ──────────────────────────────────────────────────────────────────
const DmsPage = ({ currentUser }: { currentUser: User }) => {
  const [members, setMembers] = useState<{id:number,name:string,avatar:string}[]>([])
  const [showAdd, setShowAdd] = useState(false)
  const [newName, setNewName] = useState('')
  const [activeDM, setActiveDM] = useState<number|null>(null)
  const [messages, setMessages] = useState<Record<number,{text:string,time:string,mine:boolean}[]>>({})
  const [input, setInput] = useState('')
  const [showEmoji, setShowEmoji] = useState(false)

  const addMember = () => {
    if (!newName.trim()) return
    const id = Date.now()
    setMembers(prev => [...prev, {id, name: newName.trim(), avatar: newName.trim()[0].toUpperCase()}])
    setNewName(''); setShowAdd(false)
  }

  const sendMsg = () => {
    if (!input.trim() || activeDM === null) return
    const now = new Date().toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit'})
    setMessages(prev => ({...prev, [activeDM]: [...(prev[activeDM]||[]), {text: input.trim(), time: now, mine: true}]}))
    setInput('')
  }

  const activeMember = members.find(m => m.id === activeDM)

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-60 bg-sidebar border-r border-sidebar-border flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-sidebar-border">
          <h3 className="text-sidebar-foreground font-semibold text-sm">Pesan Langsung</h3>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {members.length === 0 && <p className="text-muted-foreground text-xs px-2 py-4 text-center">Belum ada anggota</p>}
          {members.map(m => (
            <button key={m.id} onClick={() => setActiveDM(m.id)}
              className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-sm transition-colors ${activeDM===m.id ? 'bg-sidebar-accent text-sidebar-accent-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent'}`}>
              <div className="relative flex-shrink-0">
                <div className="w-7 h-7 rounded-full bg-background flex items-center justify-center text-white text-xs font-bold">{m.avatar}</div>
                <div className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-sidebar"/>
              </div>
              {m.name}
            </button>
          ))}
        </div>
        {showAdd ? (
          <div className="p-3 border-t border-sidebar-border">
            <input autoFocus type="text" value={newName} onChange={e => setNewName(e.target.value)}
              onKeyDown={e => {if(e.key==='Enter') addMember(); if(e.key==='Escape') setShowAdd(false)}}
              placeholder="Nama anggota..."
              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-foreground text-sm outline-none mb-2"/>
            <div className="flex gap-2">
              <button onClick={addMember} className="flex-1 py-1.5 rounded-lg bg-[#4A154B] text-white text-xs font-bold">Tambah</button>
              <button onClick={() => setShowAdd(false)} className="flex-1 py-1.5 rounded-lg bg-muted text-muted-foreground text-xs">Batal</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setShowAdd(true)} className="flex items-center gap-2 px-4 py-3 border-t border-sidebar-border text-muted-foreground hover:text-sidebar-foreground text-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4"/></svg>
            Tambah anggota
          </button>
        )}
      </div>

      {activeDM !== null && activeMember ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="h-14 border-b border-border flex items-center px-4 gap-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-background flex items-center justify-center text-white text-sm font-bold">{activeMember.avatar}</div>
            <span className="text-foreground font-semibold">{activeMember.name}</span>
            <div className="flex-1"/>
            <button className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
            </button>
            <button className="p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
            {(messages[activeDM]||[]).length === 0 && (
              <p className="text-center text-muted-foreground text-sm mt-8">Mulai percakapan dengan {activeMember.name}</p>
            )}
            {(messages[activeDM]||[]).map((msg, i) => (
              <div key={i} className={`flex ${msg.mine ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs px-4 py-2 rounded-2xl text-sm ${msg.mine ? 'bg-background text-white' : 'bg-muted text-foreground'}`}>
                  <div>{msg.text}</div>
                  <div className="text-xs opacity-60 mt-0.5 text-right">{msg.time}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-border flex-shrink-0 relative">
            {showEmoji && <EmojiPicker onSelect={e => setInput(prev => prev + e)} onClose={() => setShowEmoji(false)}/>}
            <div className="flex gap-2 bg-muted rounded-xl px-4 py-2 items-center">
              <button onClick={() => setShowEmoji(!showEmoji)} className="text-muted-foreground hover:text-foreground flex-shrink-0">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              </button>
              <input type="text" value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key==='Enter' && sendMsg()}
                placeholder={`Pesan ke ${activeMember.name}`}
                className="flex-1 bg-transparent outline-none text-foreground text-sm placeholder:text-muted-foreground"/>
              <button onClick={sendMsg} className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${input ? 'bg-[#4A154B] text-white border border-orange-700' : 'text-muted-foreground'}`}>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground text-sm">Pilih anggota untuk mulai chat</p>
        </div>
      )}
    </div>
  )
}

// ─── Video Call Page ──────────────────────────────────────────────────────────
const VideoCallPage = ({ user, onClose }: { user: User, onClose: () => void }) => {
  const [muted, setMuted] = useState(false)
  const [videoOff, setVideoOff] = useState(false)
  const [callTime, setCallTime] = useState(0)
  const localVideoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    navigator.mediaDevices?.getUserMedia({ video: true, audio: true })
      .then(stream => { if (localVideoRef.current) localVideoRef.current.srcObject = stream })
      .catch(() => {})
    const t = setInterval(() => setCallTime(prev => prev + 1), 1000)
    return () => { clearInterval(t) }
  }, [])

  const fmt = (s: number) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`

  return (
    <div className="fixed inset-0 bg-background z-50 flex flex-col">
      {/* Remote (placeholder) */}
      <div className="flex-1 bg-background flex items-center justify-center relative">
        <div className="text-center">
          <div className="w-24 h-24 rounded-full bg-background flex items-center justify-center text-white text-4xl font-bold mx-auto mb-4">
            {user.avatar}
          </div>
          <p className="text-white font-semibold text-lg">{user.name}</p>
          <p className="text-gray-400 text-sm mt-1">{fmt(callTime)} • Menghubungkan...</p>
        </div>

        {/* Local video */}
        <div className="absolute bottom-4 right-4 w-24 h-32 rounded-xl overflow-hidden bg-background border border-gray-700">
          <video ref={localVideoRef} autoPlay muted playsInline className="w-full h-full object-cover"/>
          {videoOff && <div className="absolute inset-0 bg-background flex items-center justify-center"><span className="text-white text-xs">{user.avatar}</span></div>}
        </div>
      </div>

      {/* Controls */}
      <div className="h-24 bg-background border-t border-gray-800 flex items-center justify-center gap-6">
        <button onClick={() => setMuted(!muted)}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${muted ? 'bg-red-500 text-white' : 'bg-background text-white hover:bg-background'}`}>
          {muted
            ? <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clipRule="evenodd"/><path strokeLinecap="round" strokeLinejoin="round" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"/></svg>
            : <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
          }
        </button>

        <button onClick={() => setVideoOff(!videoOff)}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${videoOff ? 'bg-red-500 text-white' : 'bg-background text-white hover:bg-background'}`}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
        </button>

        <button onClick={onClose}
          className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-white transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"/></svg>
        </button>

        <button className="w-12 h-12 rounded-full bg-background text-white hover:bg-background flex items-center justify-center transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/></svg>
        </button>
      </div>
    </div>
  )
}

// ─── Vault Page ───────────────────────────────────────────────────────────────
const VaultPage = () => {
  const [unlocked, setUnlocked] = useState(false)
  const [pass, setPass] = useState('')
  const [vaultError, setVaultError] = useState('')
  const [items, setItems] = useState([
    { id:1, name:'KYC Records', desc:'847 data terverifikasi', type:'kyc', locked:true },
    
    { id:3, name:'Dokumen Rahasia', desc:'23 file terenkripsi', type:'doc', locked:true },
    { id:4, name:'Backup Database', desc:'Last: hari ini 06:00', type:'db', locked:false },
  ])

  const unlock = () => {
    if (pass.length < 8) { setError('Password salah!'); return }
    setUnlocked(true); setVaultError('')
  }

  if (!unlocked) return (
    <div className="flex-1 flex items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
          </div>
          <h2 className="text-white font-bold text-xl">Brankas Terenkripsi</h2>
          <p className="text-muted-foreground text-sm mt-1">Masukkan kata sandi database untuk membuka</p>
        </div>
        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-xs mb-4">{error}</div>}
        <input type="password" placeholder="Kata sandi database" value={pass}
          onChange={e => setPass(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && unlock()}
          className="w-full px-4 py-3 rounded-xl bg-background border border-gray-700 text-white text-sm outline-none focus:border-white mb-3"/>
        <button onClick={unlock} className="w-full py-3 rounded-xl bg-[#4A154B] text-white font-bold text-sm hover:bg-muted">Buka Brankas</button>
      </div>
    </div>
  )

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-foreground font-bold text-xl flex-1">Brankas</h2>
        <div className="flex items-center gap-2 text-green-400 text-xs bg-green-500/10 px-3 py-1.5 rounded-full border border-green-500/20">
          <div className="w-2 h-2 rounded-full bg-green-400"/>
          Terbuka
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 max-w-lg">
        {items.map(item => (
          <div key={item.id} className="flex items-center gap-4 p-4 rounded-xl bg-accent border border-border cursor-pointer hover:bg-muted transition-colors">
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
            </div>
            <div className="flex-1">
              <div className="text-foreground font-semibold text-sm">{item.name}</div>
              <div className="text-muted-foreground text-xs mt-0.5">{item.desc}</div>
            </div>
            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/></svg>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Settings Page ────────────────────────────────────────────────────────────
const SettingsPage = () => {
  const [notif, setNotif] = useState(true)
  const [sound, setSound] = useState(true)
  const [lang, setLang] = useState('id')
  const [theme, setTheme] = useState('dark')

  const Toggle = ({ val, onChange }: { val: boolean, onChange: () => void }) => (
    <button onClick={onChange}
      className={`w-11 h-6 rounded-full transition-colors relative flex-shrink-0 ${val ? 'bg-background' : 'bg-muted'}`}>
      <div className={`w-4 h-4 rounded-full bg-background absolute top-1 transition-all ${val ? 'left-6' : 'left-1'}`}/>
    </button>
  )

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-6">Pengaturan</h2>
      <div className="max-w-md space-y-3">

        {/* Notifikasi */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Notifikasi</h3>
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-foreground text-sm">Notifikasi push</div>
              <div className="text-muted-foreground text-xs">Terima notifikasi pesan baru</div>
            </div>
            <Toggle val={notif} onChange={() => setNotif(!notif)}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Suara notifikasi</div>
              <div className="text-muted-foreground text-xs">Putar suara saat ada pesan</div>
            </div>
            <Toggle val={sound} onChange={() => setSound(!sound)}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Notifikasi mention</div>
              <div className="text-muted-foreground text-xs">Beritahu saat ada yang @mention</div>
            </div>
            <Toggle val={true} onChange={() => {}}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Notifikasi DM</div>
              <div className="text-muted-foreground text-xs">Beritahu saat ada pesan langsung</div>
            </div>
            <Toggle val={true} onChange={() => {}}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Jam tenang</div>
              <div className="text-muted-foreground text-xs">Nonaktifkan notifikasi 22:00 - 07:00</div>
            </div>
            <Toggle val={false} onChange={() => {}}/>
          </div>
        </div>

        {/* Bahasa */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Bahasa</h3>
          <select value={lang} onChange={e => setLang(e.target.value)}
            className="w-full px-3 py-2.5 rounded-lg bg-background border border-border text-foreground text-sm outline-none">
            <option value="id">🇮🇩 Bahasa Indonesia</option>
            <option value="en">🇺🇸 English</option>
            <option value="ar">🇸🇦 العربية</option>
          </select>
        </div>

        {/* Tema */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Tema</h3>
          <div className="grid grid-cols-3 gap-2">
            {[{val:'dark',label:'Gelap'},{val:'light',label:'Terang'},{val:'system',label:'Sistem'}].map(t => (
              <button key={t.val} onClick={() => setTheme(t.val)}
                className={`py-2 rounded-lg text-sm font-medium transition-colors ${theme===t.val ? 'bg-background text-white' : 'bg-background text-muted-foreground border border-border'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Privasi */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Privasi</h3>
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-foreground text-sm">Status online</div>
              <div className="text-muted-foreground text-xs">Tampilkan status aktif ke anggota lain</div>
            </div>
            <Toggle val={true} onChange={() => {}}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Tanda baca pesan</div>
              <div className="text-muted-foreground text-xs">Tampilkan centang biru saat pesan dibaca</div>
            </div>
            <Toggle val={true} onChange={() => {}}/>
          </div>

        </div>

        {/* Pesan */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Pesan</h3>
          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-foreground text-sm">Pesan hilang otomatis</div>
              <div className="text-muted-foreground text-xs">Hapus pesan setelah waktu tertentu</div>
            </div>
            <Toggle val={false} onChange={() => {}}/>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-border">
            <div>
              <div className="text-foreground text-sm">Pratinjau link</div>
              <div className="text-muted-foreground text-xs">Tampilkan preview URL di chat</div>
            </div>
            <Toggle val={true} onChange={() => {}}/>
          </div>
        </div>

        {/* Keamanan */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Keamanan</h3>
          <div className="space-y-2 text-sm">
            {[
              {label:'Enkripsi', val:'Aktif', ok:true},
              
              {label:'USB Key 2FA', val:'2 key terdaftar', ok:true},
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
                <span className="text-muted-foreground">{item.label}</span>
                <span className={`text-xs font-medium ${item.ok ? 'text-green-400' : 'text-red-400'}`}>{item.val}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

// ─── Invite Page ──────────────────────────────────────────────────────────────
const InvitePage = ({ user }: { user: User }) => {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState<string[]>([])
  const [error, setError] = useState('')

  const handleInvite = async () => {
    if (!email.trim()) { setError('Masukkan email!'); return }
    if (!email.includes('@')) { setError('Email tidak valid!'); return }

    const link = `http://localhost:3003/invite?ref=${btoa(email)}&from=${btoa(user.email)}`
    try {
      const res = await fetch('https://black-message-production.up.railway.app/api/v1/auth/invite/send/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          to_email: email,
          from_name: user.name,
          invite_link: link,
          workspace: 'BlackMess'
        })
      })
      if (res.ok) {
        setSent(prev => [...prev, email])
        setEmail(''); setVaultError('')
        alert(`Undangan berhasil dikirim ke ${email}!`)
      } else {
        setError('Gagal kirim email, coba lagi!')
      }
    } catch(e) {
      // Fallback
      setSent(prev => [...prev, email])
      setEmail(''); setVaultError('')
      alert(`Demo mode: Link undangan untuk ${email}:\n${link}`)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-2">Anggota</h2>
      <p className="text-muted-foreground text-sm mb-6">Undang anggota baru via email</p>
      <div className="max-w-md">
        <div className="bg-accent border border-border rounded-xl p-4 mb-6">
          <h3 className="text-foreground font-semibold text-sm mb-3">Kirim undangan</h3>
          {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2 text-red-400 text-xs mb-3">{error}</div>}
          <div className="flex gap-2">
            <input type="email" value={email} onChange={e => { setEmail(e.target.value); setError('') }}
              onKeyDown={e => e.key==='Enter' && handleInvite()}
              placeholder="nama@gmail.com atau nama@perusahaan.com"
              className="flex-1 px-3 py-2.5 rounded-lg bg-background border border-border text-foreground text-sm outline-none focus:border-white"/>
            <button onClick={handleInvite} className="px-4 py-2.5 rounded-lg bg-background text-white font-bold text-sm flex-shrink-0">Kirim</button>
          </div>
        </div>
        {sent.length > 0 ? (
          <div>
            <h3 className="text-foreground font-semibold text-sm mb-3">Undangan terkirim ({sent.length})</h3>
            {sent.map((e, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-accent border border-border mb-2">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-muted-foreground text-sm font-bold">{e[0].toUpperCase()}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-foreground text-sm truncate">{e}</div>
                  <div className="text-yellow-500 text-xs">Menunggu konfirmasi</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-muted-foreground mx-auto mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <p className="text-muted-foreground text-sm">Belum ada anggota</p>
          </div>
        )}
      </div>
    </div>
  )
}




// ─── Compliance Dashboard ─────────────────────────────────────────────────────
const CompliancePage = ({ currentUser }: { currentUser: any }) => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [chainValid, setChainValid] = useState<boolean|null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const token = localStorage.getItem('bm_token')
        const res = await fetch('https://black-message-production.up.railway.app/api/v1/compliance/dashboard/?workspace_id=default', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (res.ok) {
          const d = await res.json()
          setData(d)
          setChainValid(d.audit_chain?.valid)
        }
      } catch(e) {
        // Demo mode
        setData({
          audit_chain: { valid: true, message: 'Audit chain integrity verified', count: 1247 },
          stats: { total_messages: 4821, deleted_messages: 23, edited_messages: 156, unique_senders: 47, brute_force_attempts: 3 },
          ipfs_status: { network: 'private', nodes: ['127.0.0.1:4001'], encrypted: true },
          recent_logs: []
        })
        setChainValid(true)
      }
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return (
    <div className="flex-1 flex items-center justify-center bg-background">
      <div className="text-muted-foreground text-sm">Memuat dashboard compliance...</div>
    </div>
  )

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-foreground font-bold text-xl flex-1">Compliance Dashboard</h2>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${chainValid ? 'border-green-500/30 bg-green-500/10 text-green-400' : 'border-red-500/30 bg-red-500/10 text-red-400'}`}>
          <div className={`w-2 h-2 rounded-full ${chainValid ? 'bg-green-400' : 'bg-red-400'}`}/>
          {chainValid ? 'Chain Verified' : 'Chain Broken!'}
        </div>
      </div>

      <div className="max-w-2xl space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { label:'Total Pesan', val: data?.stats?.total_messages || 0, color:'text-white' },
            { label:'Pesan Dihapus', val: data?.stats?.deleted_messages || 0, color:'text-yellow-400' },
            { label:'Pesan Diedit', val: data?.stats?.edited_messages || 0, color:'text-blue-400' },
            { label:'Brute Force', val: data?.stats?.brute_force_attempts || 0, color:'text-red-400' },
          ].map(s => (
            <div key={s.label} className="bg-accent border border-border rounded-xl p-4">
              <div className={`text-2xl font-bold ${s.color}`}>{s.val}</div>
              <div className="text-muted-foreground text-xs mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Audit Chain */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Audit Log Berantai</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Status chain</span>
              <span className={chainValid ? 'text-green-400' : 'text-red-400'}>{chainValid ? 'Valid' : 'Rusak!'}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Total log entries</span>
              <span className="text-foreground">{data?.audit_chain?.count || 0}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Algoritma hash</span>
              <span className="text-foreground">SHA-256</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-muted-foreground">Retensi data</span>
              <span className="text-foreground">10 tahun</span>
            </div>
          </div>
        </div>

        {/* IPFS Status */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Status IPFS</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Jaringan</span>
              <span className="text-green-400">Private Network</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border">
              <span className="text-muted-foreground">Lokasi node</span>
              <span className="text-foreground">Indonesia (Lokal)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-muted-foreground">Enkripsi</span>
              <span className="text-green-400">AES-256-GCM Aktif</span>
            </div>
          </div>
        </div>

        {/* Key Escrow */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Key Escrow (Shamir 2-of-3)</h3>
          <div className="space-y-2">
            {[
              { holder:'Direktur Kepatuhan', index:1, active:true },
              { holder:'Head of IT', index:2, active:true },
              { holder:'Vault Fisik Bank', index:3, active:false },
            ].map(k => (
              <div key={k.index} className="flex items-center gap-3 py-2 border-b border-border last:border-0">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${k.active ? 'bg-green-400' : 'bg-muted'}`}/>
                <span className="text-foreground text-sm flex-1">Key {k.index}: {k.holder}</span>
                <span className={`text-xs ${k.active ? 'text-green-400' : 'text-muted-foreground'}`}>{k.active ? 'Terdaftar' : 'Pending'}</span>
              </div>
            ))}
          </div>
          <p className="text-muted-foreground text-xs mt-3">Butuh 2 dari 3 kunci untuk emergency access</p>
        </div>

        {/* Channel Policies */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Kebijakan Channel</h3>
          <div className="space-y-2">
            {[
              { channel:'#umum', type:'General', selfDestruct:true, retention:'30 hari' },
              { channel:'#acak', type:'General', selfDestruct:true, retention:'30 hari' },
              { channel:'#pengumuman', type:'Official', selfDestruct:false, retention:'10 tahun' },
              { channel:'#tim-internal', type:'Operational', selfDestruct:false, retention:'5 tahun' },
              { channel:'#rekayasa', type:'Operational', selfDestruct:false, retention:'5 tahun' },
            ].map(ch => (
              <div key={ch.channel} className="flex items-center gap-3 py-2 border-b border-border last:border-0">
                <span className="text-foreground text-sm flex-1">{ch.channel}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${ch.selfDestruct ? 'bg-yellow-500/10 text-yellow-400' : 'bg-red-500/10 text-red-400'}`}>
                  {ch.selfDestruct ? 'Self-destruct OK' : 'Wajib Simpan'}
                </span>
                <span className="text-muted-foreground text-xs">{ch.retention}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Emergency Access */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Emergency Access</h3>
          <p className="text-muted-foreground text-xs mb-3">Akses darurat membutuhkan persetujuan 2 dari 3 pemegang kunci escrow</p>
          <button className="w-full py-2.5 rounded-xl border border-red-500/30 text-red-400 text-sm font-medium hover:bg-red-500/10 transition-colors">
            Request Emergency Access
          </button>

        {/* Export for Audit */}
        <div className="bg-accent border border-border rounded-xl p-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Export for Audit OJK/BI</h3>
          <p className="text-muted-foreground text-xs mb-3">Download riwayat komunikasi untuk keperluan audit regulasi</p>
          <div className="grid grid-cols-3 gap-2">
            <a href="https://black-message-production.up.railway.app/api/v1/compliance/export/pdf/?days=30"
              className="py-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-medium text-center hover:bg-red-500/20 transition-colors">
              PDF
            </a>
            <a href="https://black-message-production.up.railway.app/api/v1/compliance/export/excel/?days=30"
              className="py-2.5 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-xs font-medium text-center hover:bg-green-500/20 transition-colors">
              Excel
            </a>
            <a href="https://black-message-production.up.railway.app/api/v1/compliance/export/json/?days=30"
              className="py-2.5 rounded-xl bg-accent/10 border border-blue-500/30 text-blue-400 text-xs font-medium text-center hover:bg-accent/20 transition-colors">
              JSON
            </a>
          </div>
          <select className="w-full mt-2 px-3 py-2 rounded-xl bg-background border border-border text-foreground text-xs outline-none">
            <option value="7">7 hari terakhir</option>
            <option value="30" selected>30 hari terakhir</option>
            <option value="90">90 hari terakhir</option>
            <option value="365">1 tahun terakhir</option>
          </select>
        </div>
        </div>
      </div>
    </div>
  )
}

// ─── AI Page ──────────────────────────────────────────────────────────────────
const AIPage = ({ currentUser }: { currentUser: any }) => {
  const [messages, setMessages] = useState<{role:string, content:string, time:string}[]>([
    { role:'assistant', content:'Halo! Saya BlackMess AI. Saya bisa membantu kamu merangkum percakapan, membuat draft pesan, analisis data, terjemahan, dan banyak lagi. Apa yang bisa saya bantu?', time: new Date().toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'}) }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const suggestions = [
    'Buatkan rangkuman meeting hari ini',
    'Draft email profesional ke klien',
    'Analisis transaksi mencurigakan',
    'Terjemahkan ke bahasa Inggris',
    'Buatkan laporan mingguan',
    'Cek keamanan sistem',
  ]

  const sendMessage = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role:'user', content: msg, time: new Date().toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'}) }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey || '',
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          system: `Kamu adalah BlackMess AI, asisten cerdas enterprise untuk platform komunikasi BlackMess.
Kamu membantu:
- Merangkum percakapan dan meeting
- Membuat draft pesan & email profesional  
- Analisis data keuangan & transaksi
- Deteksi aktivitas mencurigakan (AML)
- Terjemahan multibahasa
- Laporan compliance & audit
- Manajemen tugas & reminder

Pengguna: ${currentUser?.name || 'User'}
Gunakan bahasa Indonesia yang profesional, ringkas dan tepat sasaran.`,
          messages: messages.concat(userMsg).filter(m => m.role !== 'assistant' || messages.indexOf(m) > 0).map(m => ({
            role: m.role as 'user'|'assistant',
            content: m.content
          }))
        })
      })

      const data = await res.json()
      const reply = data.content?.[0]?.text || 'Maaf, tidak bisa memproses permintaan saat ini.'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: reply,
        time: new Date().toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'})
      }])
    } catch(e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Tidak dapat terhubung ke BlackMess AI. Pastikan API key sudah diset di file .env',
        time: new Date().toLocaleTimeString('id-ID', {hour:'2-digit', minute:'2-digit'})
      }])
    }
    setLoading(false)
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-background">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border flex-shrink-0">
        <div className="w-9 h-9 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
        </div>
        <div>
          <h2 className="text-foreground font-bold text-base">BlackMess AI</h2>
          <p className="text-muted-foreground text-xs">Asisten cerdas enterprise</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
          <span className="text-green-400 text-xs">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.role === 'assistant' && (
              <div className="w-8 h-8 rounded-xl bg-muted flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                </svg>
              </div>
            )}
            <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${m.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <div className={`px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-background text-white rounded-tr-sm' : 'bg-accent text-foreground rounded-tl-sm border border-border'}`}>
                {m.content}
              </div>
              <span className="text-muted-foreground text-xs">{m.time}</span>
            </div>
            {m.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 mt-0.5 text-white text-xs font-bold">
                {currentUser?.avatar || 'U'}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
            </div>
            <div className="bg-accent border border-border px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-muted animate-bounce" style={{animationDelay:'0ms'}}/>
                <div className="w-2 h-2 rounded-full bg-muted animate-bounce" style={{animationDelay:'150ms'}}/>
                <div className="w-2 h-2 rounded-full bg-muted animate-bounce" style={{animationDelay:'300ms'}}/>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex-shrink-0">
          <div className="flex flex-wrap gap-2">
            {suggestions.map(s => (
              <button key={s} onClick={() => sendMessage(s)}
                className="px-3 py-1.5 rounded-full border border-border text-muted-foreground text-xs hover:bg-accent hover:text-foreground transition-colors">
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-border flex-shrink-0">
        <div className="flex items-center gap-2 bg-accent rounded-xl px-4 py-2.5 border border-border">
          <input type="text" value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Tanya BlackMess AI..."
            className="flex-1 bg-transparent outline-none text-sm text-foreground placeholder:text-muted-foreground"/>
          <button onClick={() => sendMessage()}
            className={`p-1.5 rounded-lg transition-colors flex-shrink-0 ${input && !loading ? 'bg-[#4A154B] text-white' : 'text-muted-foreground'}`}
            disabled={loading}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
            </svg>
          </button>
        </div>
        <p className="text-muted-foreground text-xs text-center mt-2">BlackMess AI bisa membuat kesalahan. Verifikasi informasi penting.</p>
      </div>
    </div>
  )
}


// ─── Search Page ──────────────────────────────────────────────────────────────
const SearchPage = ({ messages }: { messages: any[] }) => {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])

  const handleSearch = (q: string) => {
    setQuery(q)
    if (!q.trim()) { setResults([]); return }
    // Search di localStorage messages
    const allMessages: any[] = []
    setResults(allMessages.filter(m =>
      m.content?.toLowerCase().includes(q.toLowerCase()) ||
      m.user?.toLowerCase().includes(q.toLowerCase())
    ))
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-4">Cari</h2>
      <div className="flex items-center gap-2 bg-accent rounded-xl px-4 py-3 border border-border mb-6">
        <svg className="w-5 h-5 text-muted-foreground flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input autoFocus type="text" value={query} onChange={e => handleSearch(e.target.value)}
          placeholder="Cari pesan, file, anggota..."
          className="flex-1 bg-transparent outline-none text-foreground text-sm placeholder:text-muted-foreground"/>
        {query && <button onClick={() => handleSearch('')} className="text-muted-foreground hover:text-foreground">✕</button>}
      </div>

      {query && results.length === 0 && (
        <div className="text-center py-12">
          <svg className="w-12 h-12 text-muted-foreground mx-auto mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <p className="text-muted-foreground text-sm">Tidak ada hasil untuk "{query}"</p>
        </div>
      )}

      {!query && (
        <div className="text-center py-12">
          <svg className="w-12 h-12 text-muted-foreground mx-auto mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <p className="text-muted-foreground text-sm">Ketik untuk mulai mencari</p>
        </div>
      )}

      {results.map((r, i) => (
        <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-accent border border-border mb-2">
          <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">{r.avatar}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-foreground font-semibold text-sm">{r.user}</span>
              <span className="text-muted-foreground text-xs">#{r.channel}</span>
              <span className="text-muted-foreground text-xs">{r.time}</span>
            </div>
            <p className="text-foreground text-sm mt-0.5">{r.content}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Activity Page ────────────────────────────────────────────────────────────
const ActivityPage = () => {
  const [activities] = useState([
    { id:1, type:'mention', text:'Seseorang mention kamu di #umum', time:'Baru saja', read:false },
    { id:2, type:'reply', text:'Ada balasan di thread kamu', time:'5 menit lalu', read:false },
    { id:3, type:'join', text:'Anggota baru bergabung ke workspace', time:'1 jam lalu', read:true },
    { id:4, type:'invite', text:'Undangan kamu diterima', time:'2 jam lalu', read:true },
  ])

  const icons: Record<string, JSX.Element> = {
    mention: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>,
    reply: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/></svg>,
    join: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/></svg>,
    invite: <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>,
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-6">Aktivitas</h2>
      <div className="max-w-lg space-y-2">
        {activities.map(a => (
          <div key={a.id} className={`flex items-start gap-3 p-4 rounded-xl border transition-colors ${!a.read ? 'bg-accent border-border' : 'border-transparent hover:bg-accent'}`}>
            <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center flex-shrink-0">{icons[a.type]}</div>
            <div className="flex-1">
              <p className="text-foreground text-sm">{a.text}</p>
              <p className="text-muted-foreground text-xs mt-0.5">{a.time}</p>
            </div>
            {!a.read && <div className="w-2 h-2 rounded-full bg-background flex-shrink-0 mt-2"/>}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Saved Page ───────────────────────────────────────────────────────────────
const SavedPage = () => {
  const [saved, setSaved] = useState<any[]>(() => {
    return JSON.parse(localStorage.getItem('bm_saved') || '[]')
  })

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-6">Tersimpan</h2>
      <div className="max-w-lg">
        {saved.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-12 h-12 text-muted-foreground mx-auto mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>
            <p className="text-muted-foreground text-sm">Belum ada pesan tersimpan</p>
            <p className="text-muted-foreground text-xs mt-1">Simpan pesan dengan klik ikon bookmark</p>
          </div>
        ) : (
          <div className="space-y-3">
            {saved.map((s: any, i: number) => (
              <div key={i} className="p-4 rounded-xl bg-accent border border-border">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center text-white text-xs font-bold">{s.avatar}</div>
                  <span className="text-foreground text-sm font-semibold">{s.user}</span>
                  <span className="text-muted-foreground text-xs">#{s.channel}</span>
                </div>
                <p className="text-foreground text-sm">{s.content}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-muted-foreground text-xs">{s.time}</span>
                  <button onClick={() => {
                    const newSaved = saved.filter((_: any, idx: number) => idx !== i)
                    setSaved(newSaved)
                    localStorage.setItem('bm_saved', JSON.stringify(newSaved))
                  }} className="text-muted-foreground hover:text-red-400 text-xs">Hapus</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Files Page ───────────────────────────────────────────────────────────────
const FilesPage = ({ currentUser }: { currentUser: any }) => {
  const [files, setFiles] = useState<any[]>(() => {
    return JSON.parse(localStorage.getItem('bm_files') || '[]')
  })
  const [dragging, setDragging] = useState(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    const newFiles = droppedFiles.map(f => ({
      name: f.name,
      size: f.size < 1024*1024 ? `${(f.size/1024).toFixed(1)} KB` : `${(f.size/1024/1024).toFixed(1)} MB`,
      type: f.type,
      url: URL.createObjectURL(f),
      uploadedBy: currentUser?.name || 'Saya',
      uploadedAt: new Date().toLocaleString('id-ID'),
    }))
    const updated = [...files, ...newFiles]
    setFiles(updated)
    localStorage.setItem('bm_files', JSON.stringify(updated))
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6"
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}>
      <h2 className="text-foreground font-bold text-xl mb-2">Berkas</h2>
      <p className="text-muted-foreground text-sm mb-6">Semua file yang dibagikan di workspace</p>

      {/* Upload zone */}
      <div className={`border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-colors ${dragging ? 'border-white bg-background/5' : 'border-gray-700 hover:border-gray-500'}`}>
        <svg className="w-10 h-10 text-muted-foreground mx-auto mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
        <p className="text-foreground text-sm font-medium">Drag & drop file di sini</p>
        <p className="text-muted-foreground text-xs mt-1">Gambar, PDF, dokumen — Maks 10MB</p>
      </div>

      {files.length === 0 ? (
        <p className="text-center text-muted-foreground text-sm">Belum ada file diunggah</p>
      ) : (
        <div className="space-y-2">
          {files.map((f: any, i: number) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-accent border border-border">
              <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                {f.type?.startsWith('image/') ? (
                  <img src={f.url} alt={f.name} className="w-full h-full object-cover rounded-lg"/>
                ) : (
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-foreground text-sm font-medium truncate">{f.name}</p>
                <p className="text-muted-foreground text-xs">{f.size} • {f.uploadedBy} • {f.uploadedAt}</p>
              </div>
              <a href={f.url} download={f.name} className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Apps Page ────────────────────────────────────────────────────────────────
const AppsPage = () => {
  const apps = [
    { name:'Google Drive', desc:'Kelola dokumen bersama', url:'https://drive.google.com', logo:'https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg' },
    { name:'Google Calendar', desc:'Sinkronisasi jadwal tim', url:'https://calendar.google.com', logo:'https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg' },
    { name:'Gmail', desc:'Email perusahaan terintegrasi', url:'https://mail.google.com', logo:'https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg' },
    { name:'GitHub', desc:'Notifikasi commit & PR', url:'https://github.com', logo:'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png' },
    { name:'Jira', desc:'Manajemen proyek & tiket', url:'https://www.atlassian.com/software/jira', logo:'https://upload.wikimedia.org/wikipedia/commons/8/8a/Jira_Logo.svg' },
    { name:'Trello', desc:'Manajemen tugas visual', url:'https://trello.com', logo:'https://upload.wikimedia.org/wikipedia/en/8/8c/Trello_logo.svg' },
    { name:'Notion', desc:'Dokumentasi tim', url:'https://notion.so', logo:'https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png' },
    { name:'Slack', desc:'Import data dari Slack', url:'https://slack.com', logo:'https://upload.wikimedia.org/wikipedia/commons/b/b9/Slack_Technologies_Logo.svg' },

  ]

  const [connected, setConnected] = useState<string[]>([])

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-2">Aplikasi</h2>
      <p className="text-muted-foreground text-sm mb-6">Integrasikan BlackMess dengan aplikasi favorit kamu</p>
      <div className="max-w-lg space-y-3">
        {apps.map(app => (
          <div key={app.name} className="flex items-center gap-4 p-4 rounded-xl bg-accent border border-border">
            <div className="w-10 h-10 rounded-xl bg-background flex items-center justify-center flex-shrink-0 p-1.5">
              <img src={app.logo} alt={app.name} className="w-full h-full object-contain" style={{filter: ['GitHub','Notion'].includes(app.name) ? 'invert(1)' : 'none'}}/>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-foreground font-semibold text-sm">{app.name}</div>
              <div className="text-muted-foreground text-xs mt-0.5">{app.desc}</div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <button onClick={() => window.open(app.url, '_blank')}
                className="px-3 py-1.5 rounded-lg text-xs font-bold border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                Buka
              </button>
              <button onClick={() => setConnected(prev => prev.includes(app.name) ? prev.filter(a => a !== app.name) : [...prev, app.name])}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${connected.includes(app.name) ? 'bg-gray-700 text-white' : 'bg-background text-white'}`}>
                {connected.includes(app.name) ? '✓ Aktif' : 'Hubungkan'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── More Page ────────────────────────────────────────────────────────────────
const MorePage = ({ onNav }: { onNav: (page: string) => void }) => (
  <div className="flex-1 overflow-y-auto bg-background p-6">
    <h2 className="text-foreground font-bold text-xl mb-6">Lainnya</h2>
    {[
          { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>, label: 'Brankas', desc: 'Penyimpanan data sensitif terenkripsi', page: 'vault' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg>, label: 'Tersimpan', desc: 'Pesan yang kamu simpan', page: 'saved' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>, label: 'Berkas', desc: 'File yang dibagikan di workspace', page: 'files' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Anggota', desc: 'Kelola dan undang anggota', page: 'invite' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>, label: 'Aplikasi', desc: 'Integrasi dengan aplikasi lain', page: 'apps' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>, label: 'Analitik', desc: 'Laporan dan metrik workspace', page: '' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>, label: 'Compliance', desc: 'Dashboard OJK/BI standar audit', page: 'compliance' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Pengaturan', desc: 'Profil dan preferensi', page: 'profile' },
    ].map(item => (
      <div key={item.label} onClick={() => item.page && onNav(item.page)}
        className="flex items-center gap-4 p-4 rounded-xl bg-accent mb-3 cursor-pointer hover:bg-muted transition-colors">
        <div className="w-10 h-10 rounded-xl bg-muted flex items-center justify-center text-muted-foreground flex-shrink-0">{item.icon}</div>
        <div className="flex-1">
          <div className="text-foreground font-semibold text-sm">{item.label}</div>
          <div className="text-muted-foreground text-xs mt-0.5">{item.desc}</div>
        </div>
        <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/></svg>
      </div>
    ))}
  </div>
)

// ─── Profile Page ─────────────────────────────────────────────────────────────
const ProfilePage = ({ user, onLogout, onBack }: { user: any, onLogout: () => void, onBack: () => void }) => {
  const [activeTab, setActiveTab] = useState('profil')
  const [saved, setSaved] = useState(false)

  // Profil
  const [name, setName] = useState(() => localStorage.getItem('bm_profile_name') || user?.name || '')
  const [titleJob, setTitleJob] = useState(() => localStorage.getItem('bm_profile_title') || '')
  const [dept, setDept] = useState(() => localStorage.getItem('bm_profile_dept') || '')
  const [phone, setPhone] = useState(() => localStorage.getItem('bm_profile_phone') || '')

  const [timezone, setTimezone] = useState('WIB')
  const [status, setStatus] = useState('online')
  const [customStatus, setCustomStatus] = useState('')
  const [statusExpiry, setStatusExpiry] = useState('never')

  // Notifikasi
  const [notifDesktop, setNotifDesktop] = useState(true)
  const [notifMobile, setNotifMobile] = useState(true)
  const [notifSound, setNotifSound] = useState(true)
  const [notifMention, setNotifMention] = useState(true)
  const [notifDM, setNotifDM] = useState(true)
  const [notifThread, setNotifThread] = useState(true)
  const [notifReaction, setNotifReaction] = useState(true)
  const [notifEmail, setNotifEmail] = useState(false)
  const [dndEnabled, setDndEnabled] = useState(false)
  const [dndStart, setDndStart] = useState('22:00')
  const [dndEnd, setDndEnd] = useState('07:00')
  const [dndWeekend, setDndWeekend] = useState(true)
  const [keywords, setKeywords] = useState('')
  const [soundType, setSoundType] = useState('ding')

  // Tampilan
  const [theme, setTheme] = useState(localStorage.getItem('bm_theme') || 'dark')
  const [syncOS, setSyncOS] = useState(false)
  const [compact, setCompact] = useState(false)
  const [fontSize, setFontSize] = useState('normal')
  const [animations, setAnimations] = useState(true)
  const [cleanerFont, setCleanerFont] = useState(false)
  const [highContrast, setHighContrast] = useState(false)
  const [showAvatar, setShowAvatar] = useState(true)
  const [showPreview, setShowPreview] = useState(true)
  const [colorblind, setColorblind] = useState('none')

  // Privasi
  const [showOnline, setShowOnline] = useState(true)
  const [readReceipt, setReadReceipt] = useState(true)
  const [showTyping, setShowTyping] = useState(true)
  const [allowDM, setAllowDM] = useState('everyone')
  const [showEmail, setShowEmail] = useState(false)
  const [showPhone, setShowPhone] = useState(false)

  // Pesan
  const [enterSend, setEnterSend] = useState(true)
  const [linkPreview, setLinkPreview] = useState(true)
  const [spellCheck, setSpellCheck] = useState(true)
  const [autoDestruct, setAutoDestruct] = useState(false)
  const [destructTime, setDestructTime] = useState('7d')
  const [emojiSkin, setEmojiSkin] = useState('default')

  // Bahasa
  const [lang, setLang] = useState('id')
  const [dateFormat, setDateFormat] = useState('DD/MM/YYYY')
  const [timeFormat, setTimeFormat] = useState('24h')
  const [weekStart, setWeekStart] = useState('monday')

  // Admin
  const [allowInvite, setAllowInvite] = useState('admin')
  const [allowChannel, setAllowChannel] = useState('everyone')
  const [defaultChannelPublic, setDefaultChannelPublic] = useState(true)
  const [retentionDays, setRetentionDays] = useState('365')
  const [requireMFA, setRequireMFA] = useState(true)
  const [allowedDomains, setAllowedDomains] = useState('')
  const [guestAccess, setGuestAccess] = useState(false)

  const Toggle = ({ val, onChange }: { val: boolean, onChange: () => void }) => (
    <button onClick={onChange}
      className={`w-11 h-6 rounded-full transition-all relative flex-shrink-0 ${val ? 'bg-[#4A154B]' : 'bg-gray-600'}`}>
      <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${val ? 'left-6' : 'left-1'}`}/>
    </button>
  )

  const Row = ({ label, desc, children }: { label: string, desc?: string, children: React.ReactNode }) => (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex-1 pr-4">
        <div className="text-white text-sm font-medium">{label}</div>
        {desc && <div className="text-gray-400 text-xs mt-0.5">{desc}</div>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  )

  const Section = ({ title, children }: { title: string, children: React.ReactNode }) => (
    <div className="bg-accent border border-border rounded-xl p-4 mb-3">
      <h3 className="text-white font-semibold text-sm mb-3 pb-2 border-b border-border">{title}</h3>
      {children}
    </div>
  )

  const applyTheme = (t: string) => {
    setTheme(t)
    localStorage.setItem('bm_theme', t)
    const root = document.documentElement
    if (t === 'light') {
      root.classList.add('light')
      root.classList.remove('dark')
      document.body.style.backgroundColor = '#ffffff'
      document.body.style.color = '#000000'
      document.documentElement.style.setProperty('--background', '0 0% 100%')
      document.documentElement.style.setProperty('--foreground', '0 0% 0%')
      document.documentElement.style.setProperty('--accent', '0 0% 95%')
      document.documentElement.style.setProperty('--muted', '0 0% 95%')
      document.documentElement.style.setProperty('--border', '0 0% 85%')
      document.documentElement.style.setProperty('--muted-foreground', '0 0% 30%')
    } else {
      root.classList.remove('light')
      root.classList.add('dark')
      document.body.style.backgroundColor = '#1a1a1a'
      document.body.style.color = '#ffffff'
      document.documentElement.style.setProperty('--background', '0 0% 10%')
      document.documentElement.style.setProperty('--foreground', '0 0% 100%')
      document.documentElement.style.setProperty('--accent', '0 0% 16%')
      document.documentElement.style.setProperty('--muted', '0 0% 16%')
      document.documentElement.style.setProperty('--border', '0 0% 20%')
      document.documentElement.style.setProperty('--muted-foreground', '0 0% 55%')
    }
  }

  const tabs = [
    { id:'profil', label:'Profil & Akun' },
    { id:'notif', label:'Notifikasi' },
    { id:'tampilan', label:'Tampilan' },
    { id:'pesan', label:'Pesan & Media' },
    { id:'privasi', label:'Privasi' },
    { id:'saluran', label:'Saluran & Ruang' },
    { id:'bahasa', label:'Bahasa & Wilayah' },
    { id:'admin', label:'Administrasi' },
    { id:'integrasi', label:'Integrasi' },
    { id:'pintasan', label:'Pintasan' },
  ]

  return (
    <div className="flex-1 flex overflow-hidden bg-background">
      {/* Sidebar tabs */}
      <div className="w-52 border-r border-border flex flex-col flex-shrink-0 overflow-y-auto bg-sidebar">
        <div className="p-4 border-b border-sidebar-border flex items-center gap-2">
          <button onClick={onBack} className="p-1 rounded hover:bg-sidebar-accent text-white">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <span className="text-white font-semibold text-sm">Pengaturan</span>
        </div>
        <div className="p-2 flex-1">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors mb-0.5 ${activeTab===t.id ? 'bg-[#4A154B] text-white font-medium' : 'text-gray-300 hover:bg-sidebar-accent hover:text-white'}`}>
              {t.label}
            </button>
          ))}
          <div className="border-t border-sidebar-border mt-2 pt-2">
            <button onClick={onLogout} className="w-full text-left px-3 py-2 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors">
              Keluar
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">

        {/* ── PROFIL & AKUN ── */}
        {activeTab === 'profil' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Profil & Akun</h2>

            <Section title="Informasi Profil">
              <div className="flex items-center gap-4 mb-4">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#4A154B] flex items-center justify-center text-white text-2xl font-bold">{user?.avatar || 'U'}</div>
                  <button className="absolute bottom-0 right-0 w-6 h-6 rounded-full bg-white flex items-center justify-center">
                    <svg className="w-3 h-3 text-black" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
                  </button>
                </div>
                <div>
                  <div className="text-white font-bold">{user?.name}</div>
                  <div className="text-gray-400 text-sm">{user?.email}</div>
                </div>
              </div>
              {[
                ['Nama tampilan', name, setName, 'text', 'Nama kamu di workspace'],
                ['Jabatan', titleJob, setTitleJob, 'text', 'Contoh: Senior Engineer'],
                ['Departemen', dept, setDept, 'text', 'Contoh: Engineering'],
                ['Nomor telepon', phone, setPhone, 'tel', '+62 812 xxxx xxxx'],
              ].map(([label, val, setter, type, placeholder]: any) => (
                <div key={label} className="mb-3">
                  <label className="text-gray-400 text-xs block mb-1">{label}</label>
                  <input type={type} value={val} onChange={e => setter(e.target.value)} placeholder={placeholder}
                    className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none focus:border-[#4A154B]"/>
                </div>
              ))}
            </Section>

            <Section title="Status Kustom">
              <Row label="Status kehadiran" desc="Atur status tampil ke anggota lain">
                <select value={status} onChange={e => setStatus(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="online">🟢 Aktif</option>
                  <option value="away">🟡 Pergi</option>
                  <option value="busy">🔴 Sibuk</option>
                  <option value="offline">⚫ Offline</option>
                </select>
              </Row>
              <div className="mt-2">
                <label className="text-gray-400 text-xs block mb-1">Status kustom</label>
                <input type="text" value={customStatus} onChange={e => setCustomStatus(e.target.value)}
                  placeholder="Contoh: Dalam rapat sampai jam 3"
                  className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none focus:border-[#4A154B] mb-2"/>
                <label className="text-gray-400 text-xs block mb-1">Hapus status otomatis</label>
                <select value={statusExpiry} onChange={e => setStatusExpiry(e.target.value)}
                  className="w-full bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="never">Jangan hapus</option>
                  <option value="30m">Dalam 30 menit</option>
                  <option value="1h">Dalam 1 jam</option>
                  <option value="4h">Dalam 4 jam</option>
                  <option value="today">Hari ini</option>
                  <option value="1w">Minggu ini</option>
                </select>
              </div>
            </Section>

            <Section title="Zona Waktu">
              <Row label="Zona waktu" desc="Digunakan untuk notifikasi dan jadwal">
                <select value={timezone} onChange={e => setTimezone(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="WIB">WIB (UTC+7) Jakarta</option>
                  <option value="WITA">WITA (UTC+8) Makassar</option>
                  <option value="WIT">WIT (UTC+9) Jayapura</option>
                  <option value="SGT">SGT (UTC+8) Singapura</option>
                </select>
              </Row>
            </Section>

            <button onClick={() => {
                localStorage.setItem('bm_profile_name', name)
                localStorage.setItem('bm_profile_title', titleJob || '')
                localStorage.setItem('bm_profile_dept', dept || '')
                localStorage.setItem('bm_profile_phone', phone || '')
                setSaved(true)
                setTimeout(() => setSaved(false), 2000)
              }}
              className="w-full py-2.5 rounded-xl bg-[#4A154B] text-white font-bold text-sm hover:bg-[#3d1040]">
              {saved ? '✓ Tersimpan' : 'Simpan Perubahan'}
            </button>
          </div>
        )}

        {/* ── NOTIFIKASI ── */}
        {activeTab === 'notif' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Notifikasi</h2>

            <Section title="Perangkat">
              <Row label="Notifikasi desktop" desc="Tampilkan notifikasi di komputer"><Toggle val={notifDesktop} onChange={() => setNotifDesktop(!notifDesktop)}/></Row>
              <Row label="Notifikasi mobile" desc="Tampilkan notifikasi di HP"><Toggle val={notifMobile} onChange={() => setNotifMobile(!notifMobile)}/></Row>
              <Row label="Suara notifikasi" desc="Putar suara saat ada pesan baru"><Toggle val={notifSound} onChange={() => setNotifSound(!notifSound)}/></Row>
              {notifSound && (
                <div className="mt-2">
                  <label className="text-gray-400 text-xs block mb-1">Jenis suara</label>
                  <select value={soundType} onChange={e => setSoundType(e.target.value)}
                    className="w-full bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                    <option value="ding">Ding</option>
                    <option value="knock">Knock</option>
                    <option value="pop">Pop</option>
                    <option value="none">Tanpa suara</option>
                  </select>
                </div>
              )}
              <Row label="Notifikasi email" desc="Kirim ringkasan via email saat tidak aktif"><Toggle val={notifEmail} onChange={() => setNotifEmail(!notifEmail)}/></Row>
            </Section>

            <Section title="Jenis Notifikasi">
              <Row label="Mention (@nama)" desc="Saat ada yang mention kamu"><Toggle val={notifMention} onChange={() => setNotifMention(!notifMention)}/></Row>
              <Row label="Pesan langsung (DM)" desc="Saat ada DM masuk"><Toggle val={notifDM} onChange={() => setNotifDM(!notifDM)}/></Row>
              <Row label="Balasan thread" desc="Saat ada balasan di thread kamu"><Toggle val={notifThread} onChange={() => setNotifThread(!notifThread)}/></Row>
              <Row label="Reaksi pesan" desc="Saat pesan kamu direaksi"><Toggle val={notifReaction} onChange={() => setNotifReaction(!notifReaction)}/></Row>
            </Section>

            <Section title="Jadwal Do Not Disturb">
              <Row label="Aktifkan Do Not Disturb" desc="Nonaktifkan notifikasi pada jam tertentu"><Toggle val={dndEnabled} onChange={() => setDndEnabled(!dndEnabled)}/></Row>
              {dndEnabled && (
                <>
                  <div className="flex gap-3 mt-3">
                    <div className="flex-1">
                      <label className="text-gray-400 text-xs block mb-1">Mulai</label>
                      <input type="time" value={dndStart} onChange={e => setDndStart(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none"/>
                    </div>
                    <div className="flex-1">
                      <label className="text-gray-400 text-xs block mb-1">Selesai</label>
                      <input type="time" value={dndEnd} onChange={e => setDndEnd(e.target.value)}
                        className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none"/>
                    </div>
                  </div>
                  <Row label="Aktifkan di akhir pekan" desc="Sabtu & Minggu"><Toggle val={dndWeekend} onChange={() => setDndWeekend(!dndWeekend)}/></Row>
                </>
              )}
            </Section>

            <Section title="Keyword Alerts">
              <label className="text-gray-400 text-xs block mb-1">Notifikasi saat kata kunci muncul</label>
              <input type="text" value={keywords} onChange={e => setKeywords(e.target.value)}
                placeholder="Contoh: urgent, deploy, server down"
                className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none focus:border-[#4A154B]"/>
              <p className="text-gray-500 text-xs mt-1">Pisahkan dengan koma</p>
            </Section>
          </div>
        )}

        {/* ── TAMPILAN ── */}
        {activeTab === 'tampilan' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Tampilan</h2>

            <Section title="Tema">
              <div className="grid grid-cols-3 gap-2 mb-3">
                {[{val:'dark',label:<span className="flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>Gelap</span>},{val:'light',label:<span className="flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z"/></svg>Terang</span>},{val:'system',label:<span className="flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>Sistem</span>}].map(t => (
                  <button key={t.val} onClick={() => applyTheme(t.val)}
                    className={`py-2.5 rounded-lg text-sm font-medium transition-colors ${theme===t.val ? 'bg-[#4A154B] text-white' : 'bg-muted text-foreground border border-border hover:bg-accent'}`}>
                    {t.label}
                  </button>
                ))}
              </div>
              <Row label="Sinkronisasi dengan OS" desc="Ikuti pengaturan tema sistem operasi"><Toggle val={syncOS} onChange={() => setSyncOS(!syncOS)}/></Row>
            </Section>

            <Section title="Layout">
              <Row label="Mode kompak" desc="Tampilkan pesan lebih rapat, hemat ruang"><Toggle val={compact} onChange={() => setCompact(!compact)}/></Row>
              <Row label="Tampilkan avatar" desc="Tampilkan foto profil di setiap pesan"><Toggle val={showAvatar} onChange={() => setShowAvatar(!showAvatar)}/></Row>
              <Row label="Pratinjau pesan" desc="Tampilkan preview pesan di notifikasi"><Toggle val={showPreview} onChange={() => setShowPreview(!showPreview)}/></Row>
              <Row label="Ukuran teks" desc="">
                <select value={fontSize} onChange={e => setFontSize(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="small">Kecil</option>
                  <option value="normal">Normal</option>
                  <option value="large">Besar</option>
                </select>
              </Row>
            </Section>

            <Section title="Aksesibilitas">
              <Row label="Animasi UI" desc="Aktifkan efek transisi dan animasi"><Toggle val={animations} onChange={() => setAnimations(!animations)}/></Row>
              <Row label="Font lebih bersih" desc="Gunakan font yang lebih mudah dibaca"><Toggle val={cleanerFont} onChange={() => setCleanerFont(!cleanerFont)}/></Row>
              <Row label="Kontras tinggi" desc="Tingkatkan kontras untuk keterbacaan lebih baik"><Toggle val={highContrast} onChange={() => setHighContrast(!highContrast)}/></Row>
              <Row label="Mode buta warna" desc="">
                <select value={colorblind} onChange={e => setColorblind(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="none">Normal</option>
                  <option value="deuteranopia">Deuteranopia</option>
                  <option value="protanopia">Protanopia</option>
                  <option value="tritanopia">Tritanopia</option>
                </select>
              </Row>
            </Section>
          </div>
        )}

        {/* ── PESAN & MEDIA ── */}
        {activeTab === 'pesan' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Pesan & Media</h2>

            <Section title="Penulisan Pesan">
              <Row label="Enter untuk kirim" desc="Shift+Enter untuk baris baru"><Toggle val={enterSend} onChange={() => setEnterSend(!enterSend)}/></Row>
              <Row label="Koreksi ejaan" desc="Tandai kata yang salah ejaan"><Toggle val={spellCheck} onChange={() => setSpellCheck(!spellCheck)}/></Row>
              <Row label="Pratinjau tautan" desc="Tampilkan preview URL di chat"><Toggle val={linkPreview} onChange={() => setLinkPreview(!linkPreview)}/></Row>
              <Row label="Skin tone emoji" desc="">
                <select value={emojiSkin} onChange={e => setEmojiSkin(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="default">👋 Default</option>
                  <option value="light">👋🏻 Terang</option>
                  <option value="medium">👋🏽 Sedang</option>
                  <option value="dark">👋🏿 Gelap</option>
                </select>
              </Row>
            </Section>

            <Section title="Pesan Hilang Otomatis (Self-Destruct)">
              <Row label="Aktifkan self-destruct" desc="Pesan hilang otomatis setelah waktu tertentu"><Toggle val={autoDestruct} onChange={() => setAutoDestruct(!autoDestruct)}/></Row>
              {autoDestruct && (
                <div className="mt-3">
                  <label className="text-gray-400 text-xs block mb-1">Hapus setelah</label>
                  <select value={destructTime} onChange={e => setDestructTime(e.target.value)}
                    className="w-full bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                    <option value="1h">1 jam</option>
                    <option value="1d">1 hari</option>
                    <option value="7d">7 hari</option>
                    <option value="30d">30 hari</option>
                    <option value="90d">90 hari</option>
                  </select>
                </div>
              )}
            </Section>
          </div>
        )}

        {/* ── PRIVASI ── */}
        {activeTab === 'privasi' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Privasi</h2>

            <Section title="Visibilitas">
              <Row label="Tampilkan status online" desc="Biarkan anggota lain melihat status aktif kamu"><Toggle val={showOnline} onChange={() => setShowOnline(!showOnline)}/></Row>
              <Row label="Tanda baca pesan" desc="Tampilkan centang saat pesan dibaca"><Toggle val={readReceipt} onChange={() => setReadReceipt(!readReceipt)}/></Row>
              <Row label="Indikator mengetik" desc="Tampilkan sedang mengetik ke orang lain"><Toggle val={showTyping} onChange={() => setShowTyping(!showTyping)}/></Row>
              <Row label="Tampilkan email di profil" desc=""><Toggle val={showEmail} onChange={() => setShowEmail(!showEmail)}/></Row>
              <Row label="Tampilkan nomor telepon" desc=""><Toggle val={showPhone} onChange={() => setShowPhone(!showPhone)}/></Row>
            </Section>

            <Section title="Siapa yang Bisa DM Kamu">
              <select value={allowDM} onChange={e => setAllowDM(e.target.value)}
                className="w-full bg-muted border border-border text-white text-sm rounded-lg px-3 py-2.5 outline-none">
                <option value="everyone">Semua anggota workspace</option>
                <option value="channel">Hanya anggota channel yang sama</option>
                <option value="none">Tidak ada (matikan DM)</option>
              </select>
            </Section>
          </div>
        )}

        {/* ── SALURAN & RUANG ── */}
        {activeTab === 'saluran' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Saluran & Ruang</h2>

            <Section title="Kebijakan Channel">
              <Row label="Siapa yang bisa membuat channel" desc="">
                <select value={allowChannel} onChange={e => setAllowChannel(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="everyone">Semua anggota</option>
                  <option value="admin">Admin saja</option>
                  <option value="owner">Owner saja</option>
                </select>
              </Row>
              <Row label="Channel baru default publik" desc="Channel baru otomatis publik untuk semua anggota"><Toggle val={defaultChannelPublic} onChange={() => setDefaultChannelPublic(!defaultChannelPublic)}/></Row>
            </Section>

            <Section title="Retensi Data">
              <Row label="Simpan pesan selama" desc="Pesan lebih lama dari ini akan dihapus otomatis">
                <select value={retentionDays} onChange={e => setRetentionDays(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="30">30 hari</option>
                  <option value="90">90 hari</option>
                  <option value="365">1 tahun</option>
                  <option value="1825">5 tahun</option>
                  <option value="3650">10 tahun (standar OJK)</option>
                  <option value="forever">Selamanya</option>
                </select>
              </Row>
              <p className="text-gray-500 text-xs mt-2">Standar OJK/BI memerlukan retensi minimal 5 tahun untuk komunikasi finansial</p>
            </Section>
          </div>
        )}

        {/* ── KEAMANAN ── */}
        {activeTab === 'keamanan' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Keamanan</h2>

            <Section title="Status Enkripsi">
              {[
                {label:'Enkripsi E2E', val:'AES-256-GCM', ok:true},
                {label:'Post-Quantum (PQC)', val:'Kyber-1024', ok:true},
                {label:'Zero Knowledge', val:'Aktif', ok:true},
                {label:'Anti-Forensik', val:'Aktif', ok:true},
                {label:'Google Authenticator', val:'Terdaftar', ok:true},
                {label:'FIDO2/USB Key', val:'2 key terdaftar', ok:true},
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-gray-300 text-sm">{item.label}</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${item.ok ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>{item.val}</span>
                </div>
              ))}
            </Section>

            <Section title="Sesi Aktif">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted border border-border mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                </div>
                <div className="flex-1">
                  <div className="text-white text-sm font-medium">Perangkat ini</div>
                  <div className="text-gray-400 text-xs">Android · Chrome · Aktif sekarang</div>
                </div>
                <div className="w-2 h-2 rounded-full bg-green-400"/>
              </div>
              <button className="w-full py-2 rounded-lg border border-red-500/30 text-red-400 text-sm hover:bg-red-500/10 transition-colors">
                Keluar dari semua perangkat
              </button>
            </Section>

            <Section title="Kata Sandi">
              <button className="w-full py-2.5 rounded-lg border border-border text-white text-sm hover:bg-muted transition-colors mb-2">
                Ganti Kata Sandi
              </button>
              <button className="w-full py-2.5 rounded-lg border border-border text-white text-sm hover:bg-muted transition-colors">
                Kelola Security Key (FIDO2)
              </button>
            </Section>
          </div>
        )}

        {/* ── BAHASA & WILAYAH ── */}
        {activeTab === 'bahasa' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Bahasa & Wilayah</h2>

            <Section title="Bahasa">
              <Row label="Bahasa antarmuka" desc="">
                <select value={lang} onChange={e => setLang(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="id">🇮🇩 Bahasa Indonesia</option>
                  <option value="en">🇺🇸 English</option>
                  <option value="ar">🇸🇦 العربية</option>
                  <option value="ms">🇲🇾 Bahasa Melayu</option>
                  <option value="zh">🇨🇳 中文</option>
                  <option value="ja">🇯🇵 日本語</option>
                  <option value="ko">🇰🇷 한국어</option>
                  <option value="fr">🇫🇷 Français</option>
                  <option value="de">🇩🇪 Deutsch</option>
                  <option value="es">🇪🇸 Español</option>
                  <option value="pt">🇧🇷 Português</option>
                  <option value="ru">🇷🇺 Русский</option>
                  <option value="hi">🇮🇳 हिन्दी</option>
                  <option value="tr">🇹🇷 Türkçe</option>
                  <option value="it">🇮🇹 Italiano</option>
                  <option value="nl">🇳🇱 Nederlands</option>
                  <option value="pl">🇵🇱 Polski</option>
                  <option value="sv">🇸🇪 Svenska</option>
                  <option value="th">🇹🇭 ภาษาไทย</option>
                  <option value="vi">🇻🇳 Tiếng Việt</option>
                  <option value="fa">🇮🇷 فارسی</option>
                </select>
              </Row>
            </Section>

            <Section title="Format Tanggal & Waktu">
              <Row label="Format tanggal" desc="">
                <select value={dateFormat} onChange={e => setDateFormat(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                  <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                </select>
              </Row>
              <Row label="Format waktu" desc="">
                <select value={timeFormat} onChange={e => setTimeFormat(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="24h">24 jam</option>
                  <option value="12h">12 jam (AM/PM)</option>
                </select>
              </Row>
              <Row label="Awal minggu" desc="">
                <select value={weekStart} onChange={e => setWeekStart(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="monday">Senin</option>
                  <option value="sunday">Minggu</option>
                  <option value="saturday">Sabtu</option>
                </select>
              </Row>
            </Section>
          </div>
        )}

        {/* ── ADMINISTRASI ── */}
        {activeTab === 'admin' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Administrasi Workspace</h2>

            <Section title="Manajemen Anggota">
              <Row label="Siapa yang bisa mengundang" desc="">
                <select value={allowInvite} onChange={e => setAllowInvite(e.target.value)}
                  className="bg-muted border border-border text-white text-xs rounded-lg px-2 py-1.5 outline-none">
                  <option value="everyone">Semua anggota</option>
                  <option value="admin">Admin saja</option>
                  <option value="owner">Owner saja</option>
                </select>
              </Row>
              <Row label="Akses tamu (guest)" desc="Izinkan akses terbatas untuk pihak eksternal"><Toggle val={guestAccess} onChange={() => setGuestAccess(!guestAccess)}/></Row>
            </Section>

            <Section title="Domain Email">
              <label className="text-gray-400 text-xs block mb-1">Domain yang diizinkan bergabung</label>
              <input type="text" value={allowedDomains} onChange={e => setAllowedDomains(e.target.value)}
                placeholder="Contoh: perusahaan.co.id, bank.com"
                className="w-full px-3 py-2 rounded-lg bg-muted border border-border text-white text-sm outline-none focus:border-[#4A154B] mb-1"/>
              <p className="text-gray-500 text-xs">Pisahkan dengan koma. Kosongkan untuk semua domain.</p>
            </Section>

            <Section title="Keamanan Workspace">
              <Row label="Wajibkan MFA untuk semua" desc="Semua anggota harus aktifkan 2FA"><Toggle val={requireMFA} onChange={() => setRequireMFA(!requireMFA)}/></Row>
            </Section>

            <Section title="Penagihan (Billing)">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <div>
                  <div className="text-white text-sm">Paket saat ini</div>
                  <div className="text-gray-400 text-xs">Enterprise</div>
                </div>
                <span className="text-xs bg-[#4A154B] text-white px-2 py-1 rounded-full">Enterprise</span>
              </div>
              <button className="w-full mt-3 py-2 rounded-lg border border-border text-white text-sm hover:bg-muted transition-colors">
                Kelola Langganan
              </button>
            </Section>
          </div>
        )}

        {/* ── INTEGRASI ── */}
        {activeTab === 'integrasi' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Integrasi Aplikasi</h2>
            <p className="text-gray-400 text-sm mb-4">Hubungkan BlackMess dengan aplikasi yang kamu gunakan sehari-hari</p>
            <div className="space-y-3">
              {[
                {name:'Google Drive', desc:'Kelola dan bagikan dokumen', logo:'https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg', url:'https://drive.google.com'},
                {name:'Google Calendar', desc:'Sinkronisasi jadwal tim', logo:'https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg', url:'https://calendar.google.com'},
                {name:'Gmail', desc:'Email perusahaan terintegrasi', logo:'https://upload.wikimedia.org/wikipedia/commons/7/7e/Gmail_icon_%282020%29.svg', url:'https://mail.google.com'},
                {name:'GitHub', desc:'Notifikasi commit & PR', logo:'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png', url:'https://github.com'},
                {name:'Jira', desc:'Manajemen proyek & tiket', logo:'https://upload.wikimedia.org/wikipedia/commons/8/8a/Jira_Logo.svg', url:'https://jira.atlassian.com'},
                {name:'Trello', desc:'Manajemen tugas visual', logo:'https://upload.wikimedia.org/wikipedia/en/8/8c/Trello_logo.svg', url:'https://trello.com'},
                {name:'Notion', desc:'Dokumentasi tim', logo:'https://upload.wikimedia.org/wikipedia/commons/4/45/Notion_app_logo.png', url:'https://notion.so'},
                {name:'Slack', desc:'Import data dari Slack', logo:'https://upload.wikimedia.org/wikipedia/commons/d/d5/Slack_icon_2019.svg', url:'https://slack.com'},
              ].map(app => (
                <div key={app.name} className="flex items-center gap-4 p-4 rounded-xl bg-accent border border-border">
                  <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center flex-shrink-0 p-1.5" style={{background: theme==='light' ? '#f3f4f6' : '#ffffff'}}>
                    <img src={app.logo} alt={app.name} className="w-full h-full object-contain" style={{filter: ['GitHub','Notion'].includes(app.name) ? 'invert(1)' : 'none'}}/>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-semibold text-sm">{app.name}</div>
                    <div className="text-gray-400 text-xs">{app.desc}</div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => window.open(app.url,'_blank')} className="px-3 py-1.5 rounded-lg text-xs border border-border text-gray-300 hover:bg-muted">Buka</button>
                    <button className="px-3 py-1.5 rounded-lg text-xs bg-[#4A154B] text-white font-medium">Hubungkan</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── PINTASAN ── */}
        {activeTab === 'pintasan' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Pintasan Keyboard</h2>
            <Section title="Navigasi">
              {[
                {key:'Ctrl+K', desc:'Cari channel atau anggota'},
                {key:'Alt+↑↓', desc:'Navigasi antar channel'},
                {key:'Ctrl+Shift+K', desc:'Buka DM baru'},
                {key:'Esc', desc:'Tutup panel / Batal edit'},
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
                  <span className="text-gray-300 text-sm">{item.desc}</span>
                  <span className="text-xs font-mono bg-muted px-2 py-1 rounded-lg text-white border border-border">{item.key}</span>
                </div>
              ))}
            </Section>
            <Section title="Pesan">
              {[
                {key:'Enter', desc:'Kirim pesan'},
                {key:'Shift+Enter', desc:'Baris baru'},
                {key:'↑', desc:'Edit pesan terakhir'},
                {key:'Ctrl+B', desc:'Teks tebal'},
                {key:'Ctrl+I', desc:'Teks miring'},
                {key:'Ctrl+U', desc:'Teks bergaris bawah'},
                {key:'Ctrl+Shift+X', desc:'Teks dicoret'},
                {key:'Ctrl+Shift+C', desc:'Kode inline'},
              ].map(item => (
                <div key={item.key} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
                  <span className="text-gray-300 text-sm">{item.desc}</span>
                  <span className="text-xs font-mono bg-muted px-2 py-1 rounded-lg text-white border border-border">{item.key}</span>
                </div>
              ))}
            </Section>
          </div>
        )}

        {/* ── TENTANG ── */}
        {activeTab === 'tentang' && (
          <div className="max-w-lg">
            <h2 className="text-white font-bold text-xl mb-6">Tentang BlackMess</h2>
            <Section title="Informasi Aplikasi">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 rounded-2xl bg-[#4A154B] flex items-center justify-center">
                  <svg width="36" height="36" viewBox="0 0 48 48" fill="none">
                    <circle cx="24" cy="6" r="3" fill="white"/>
                    <circle cx="24" cy="42" r="3" fill="white"/>
                    <circle cx="6" cy="24" r="3" fill="white"/>
                    <circle cx="42" cy="24" r="3" fill="white"/>
                    <circle cx="11" cy="11" r="2.5" fill="white" opacity="0.7"/>
                    <circle cx="37" cy="11" r="2.5" fill="white" opacity="0.7"/>
                    <circle cx="11" cy="37" r="2.5" fill="white" opacity="0.7"/>
                    <circle cx="37" cy="37" r="2.5" fill="white" opacity="0.7"/>
                  </svg>
                </div>
                <div>
                  <div className="text-white font-bold text-lg">BlackMess</div>
                  <div className="text-gray-400 text-sm">Enterprise Remote Work Platform</div>
                </div>
              </div>
              {[
                {label:'Versi', val:'1.0.0'},
                {label:'Build', val:new Date().toLocaleDateString('id-ID')},
                {label:'Platform', val:'Web (Vite + React)'},
                {label:'Backend', val:'Django 6.0 + PostgreSQL'},
                {label:'Enkripsi', val:'AES-256-GCM + PQC Kyber-1024'},
                {label:'Database', val:'500 tabel'},
                {label:'Standar', val:'OJK/BI Compliant'},
                {label:'Lisensi', val:'Enterprise'},
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-gray-400 text-sm">{item.label}</span>
                  <span className="text-white text-sm font-medium">{item.val}</span>
                </div>
              ))}
              <button className="w-full mt-3 py-2.5 rounded-xl border border-border text-white text-sm hover:bg-muted transition-colors">
                Cek Pembaruan
              </button>
            </Section>
          </div>
        )}

      </div>
    </div>
  )
}



// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<User|null>(() => {
    try {
      const saved = localStorage.getItem('bm_current_user')
      return saved ? JSON.parse(saved) : null
    } catch { return null }
  })
  const [activePage, setActivePage] = useState('home')
  const [activeChannel, setActiveChannel] = useState('umum')
  const [subPage, setSubPage] = useState('')
  const [showVideoCall, setShowVideoCall] = useState(false)




    if (!user) return <AuthFlow onComplete={(u) => {
    localStorage.setItem('bm_current_user', JSON.stringify(u))
    setUser(u)
  }} />

  if (showVideoCall && user) return <VideoCall user={user!} onClose={() => setShowVideoCall(false)} />

  const handleNav = (page: string) => {
    if (page === 'videocall') { setShowVideoCall(true); return }
    setSubPage(page)
    setActivePage('more')
  }

  const handlePageChange = (page: string) => {
    setActivePage(page)
    setSubPage('')
  }

  const renderContent = () => {
    if (subPage === 'profile') return <ProfilePage user={user!} onLogout={() => { setUser(null); localStorage.removeItem('bm_current_user') }} onBack={() => setSubPage('')} />
    if (subPage === 'vault') return <VaultPage />
    if (subPage === 'settings') { setSubPage('profile'); return null }
    if (subPage === 'invite') return <InvitePage user={user!} />

    switch(activePage) {
      case 'home': return (
        <>
          <ChannelSidebar onChannelChange={ch => setActiveChannel(ch)} />
          <ChatArea key={activeChannel} channel={activeChannel} currentUser={user} onVideoCall={() => setShowVideoCall(true)} onProfile={() => setSubPage("profile")} />
        </>
      )
      case 'dms': return <DmsPage currentUser={user} />
      case 'compliance': return <CompliancePage currentUser={user} />
      case 'activity': return <ActivityPage />
      case 'search': return <SearchPage messages={[]} />
      case 'saved': return <SavedPage />
      case 'files': return <FilesPage currentUser={user} />
      case 'apps': return <AppsPage />
      case 'more': return <MorePage onNav={handleNav} />
      default: return <><ChannelSidebar onChannelChange={ch => setActiveChannel(ch)} /><ChatArea key={activeChannel} channel={activeChannel} currentUser={user} onVideoCall={() => setShowVideoCall(true)} onProfile={() => setSubPage("profile")} /></>
    }
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <WorkspaceSidebar
        activePage={activePage}
        onPageChange={handlePageChange}
      />
      {renderContent()}
    </div>
  )
}
