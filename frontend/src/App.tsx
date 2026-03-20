import { useAuth, useUser, SignIn, SignUp } from '@clerk/react'
import { useState, useRef, useEffect } from 'react'
import { AuthFlow } from './pages/AuthFlow'
import { WorkspaceSidebar } from './components/workspace-sidebar'
import { ChannelSidebar } from './components/channel-sidebar'
import { ChatArea } from './components/chat-area'

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
  <div className="absolute bottom-14 left-0 bg-[#1a1a1a] border border-border rounded-xl p-3 shadow-xl z-50 w-64">
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
                <div className="w-7 h-7 rounded-full bg-[#222222] flex items-center justify-center text-white text-xs font-bold">{m.avatar}</div>
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
              <button onClick={addMember} className="flex-1 py-1.5 rounded-lg bg-white text-black text-xs font-bold">Tambah</button>
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
            <div className="w-8 h-8 rounded-full bg-[#222222] flex items-center justify-center text-white text-sm font-bold">{activeMember.avatar}</div>
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
                <div className={`max-w-xs px-4 py-2 rounded-2xl text-sm ${msg.mine ? 'bg-white text-white' : 'bg-muted text-foreground'}`}>
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
              <button onClick={sendMsg} className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${input ? 'bg-white text-black' : 'text-muted-foreground'}`}>
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
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Remote (placeholder) */}
      <div className="flex-1 bg-[#111] flex items-center justify-center relative">
        <div className="text-center">
          <div className="w-24 h-24 rounded-full bg-[#222222] flex items-center justify-center text-white text-4xl font-bold mx-auto mb-4">
            {user.avatar}
          </div>
          <p className="text-white font-semibold text-lg">{user.name}</p>
          <p className="text-gray-400 text-sm mt-1">{fmt(callTime)} • Menghubungkan...</p>
        </div>

        {/* Local video */}
        <div className="absolute bottom-4 right-4 w-24 h-32 rounded-xl overflow-hidden bg-[#222] border border-gray-700">
          <video ref={localVideoRef} autoPlay muted playsInline className="w-full h-full object-cover"/>
          {videoOff && <div className="absolute inset-0 bg-[#222] flex items-center justify-center"><span className="text-white text-xs">{user.avatar}</span></div>}
        </div>
      </div>

      {/* Controls */}
      <div className="h-24 bg-[#0a0a0a] border-t border-gray-800 flex items-center justify-center gap-6">
        <button onClick={() => setMuted(!muted)}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${muted ? 'bg-red-500 text-white' : 'bg-[#222] text-white hover:bg-[#333]'}`}>
          {muted
            ? <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" clipRule="evenodd"/><path strokeLinecap="round" strokeLinejoin="round" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"/></svg>
            : <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"/></svg>
          }
        </button>

        <button onClick={() => setVideoOff(!videoOff)}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${videoOff ? 'bg-red-500 text-white' : 'bg-[#222] text-white hover:bg-[#333]'}`}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
        </button>

        <button onClick={onClose}
          className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-white transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z"/></svg>
        </button>

        <button className="w-12 h-12 rounded-full bg-[#222] text-white hover:bg-[#333] flex items-center justify-center transition-colors">
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
  const [error, setError] = useState('')
  const [items, setItems] = useState([
    { id:1, name:'KYC Records', desc:'847 data terverifikasi', type:'kyc', locked:true },
    
    { id:3, name:'Dokumen Rahasia', desc:'23 file terenkripsi', type:'doc', locked:true },
    { id:4, name:'Backup Database', desc:'Last: hari ini 06:00', type:'db', locked:false },
  ])

  const unlock = () => {
    if (pass.length < 8) { setError('Password salah!'); return }
    setUnlocked(true); setError('')
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
          className="w-full px-4 py-3 rounded-xl bg-[#111] border border-gray-700 text-white text-sm outline-none focus:border-white mb-3"/>
        <button onClick={unlock} className="w-full py-3 rounded-xl bg-white text-black font-bold text-sm hover:bg-gray-100">Buka Brankas</button>
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
      className={`w-11 h-6 rounded-full transition-colors relative flex-shrink-0 ${val ? 'bg-white' : 'bg-gray-700'}`}>
      <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${val ? 'left-6' : 'left-1'}`}/>
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
                className={`py-2 rounded-lg text-sm font-medium transition-colors ${theme===t.val ? 'bg-white text-black' : 'bg-background text-muted-foreground border border-border'}`}>
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
    const personal = ['gmail.com','yahoo.com','hotmail.com','outlook.com']
    if (personal.includes(email.split('@')[1])) { setError('Gunakan email perusahaan!'); return }
    const link = `http://localhost:3003/invite?ref=${btoa(email)}&from=${btoa(user.email)}`
    try {
      const res = await fetch('http://localhost:8002/api/v1/auth/invite/send/', {
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
        setEmail(''); setError('')
        alert(`Undangan berhasil dikirim ke ${email}!`)
      } else {
        setError('Gagal kirim email, coba lagi!')
      }
    } catch(e) {
      // Fallback
      setSent(prev => [...prev, email])
      setEmail(''); setError('')
      alert(`Demo mode: Link undangan untuk ${email}:\n${link}`)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-2">Anggota</h2>
      <p className="text-muted-foreground text-sm mb-6">Undang anggota baru via email perusahaan</p>
      <div className="max-w-md">
        <div className="bg-accent border border-border rounded-xl p-4 mb-6">
          <h3 className="text-foreground font-semibold text-sm mb-3">Kirim undangan</h3>
          {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2 text-red-400 text-xs mb-3">{error}</div>}
          <div className="flex gap-2">
            <input type="email" value={email} onChange={e => { setEmail(e.target.value); setError('') }}
              onKeyDown={e => e.key==='Enter' && handleInvite()}
              placeholder="nama@perusahaan.com"
              className="flex-1 px-3 py-2.5 rounded-lg bg-background border border-border text-foreground text-sm outline-none focus:border-white"/>
            <button onClick={handleInvite} className="px-4 py-2.5 rounded-lg bg-white text-black font-bold text-sm flex-shrink-0">Kirim</button>
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


// ─── Activity Page ────────────────────────────────────────────────────────────
const ActivityPage = () => {
  const [activities] = useState([
    { id:1, type:'mention', text:'Seseorang mention kamu di #umum', time:'Baru saja', read:false },
    { id:2, type:'reply', text:'Ada balasan di thread kamu', time:'5 menit lalu', read:false },
    { id:3, type:'join', text:'Anggota baru bergabung ke workspace', time:'1 jam lalu', read:true },
    { id:4, type:'invite', text:'Undangan kamu diterima', time:'2 jam lalu', read:true },
  ])

  const icons: Record<string, string> = {
    mention: '@', reply: '↩', join: '👤', invite: '✉️'
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <h2 className="text-foreground font-bold text-xl mb-6">Aktivitas</h2>
      <div className="max-w-lg space-y-2">
        {activities.map(a => (
          <div key={a.id} className={`flex items-start gap-3 p-4 rounded-xl border transition-colors ${!a.read ? 'bg-accent border-border' : 'border-transparent hover:bg-accent'}`}>
            <div className="w-9 h-9 rounded-full bg-gray-800 flex items-center justify-center text-sm flex-shrink-0">{icons[a.type]}</div>
            <div className="flex-1">
              <p className="text-foreground text-sm">{a.text}</p>
              <p className="text-muted-foreground text-xs mt-0.5">{a.time}</p>
            </div>
            {!a.read && <div className="w-2 h-2 rounded-full bg-white flex-shrink-0 mt-2"/>}
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
                  <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-white text-xs font-bold">{s.avatar}</div>
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
      <div className={`border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-colors ${dragging ? 'border-white bg-white/5' : 'border-gray-700 hover:border-gray-500'}`}>
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
              <div className="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0">
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
            <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center flex-shrink-0 p-1.5">
              <img src={app.logo} alt={app.name} className="w-full h-full object-contain"/>
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
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${connected.includes(app.name) ? 'bg-gray-700 text-white' : 'bg-white text-black'}`}>
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
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>, label: 'Video Call', desc: 'Panggilan video terenkripsi', page: 'videocall' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Anggota', desc: 'Undang anggota workspace', page: 'invite' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Pengaturan', desc: 'Notifikasi, bahasa, tema, keamanan', page: 'settings' },
      { icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>, label: 'Analitik', desc: 'Laporan dan metrik workspace', page: '' },
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
const ProfilePage = ({ user, onLogout, onBack }: { user: User, onLogout: () => void, onBack: () => void }) => {
  const [name, setName] = useState(user.name)
  const [saved, setSaved] = useState(false)
  const [status, setStatus] = useState<'online'|'away'|'busy'|'offline'>('online')

  const statusConfig = {
    online: { color: 'bg-green-400', label: 'Aktif' },
    away: { color: 'bg-yellow-400', label: 'Pergi' },
    busy: { color: 'bg-red-400', label: 'Sibuk' },
    offline: { color: 'bg-gray-500', label: 'Offline' },
  }

  return (
    <div className="flex-1 overflow-y-auto bg-background p-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-accent text-muted-foreground">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <h2 className="text-foreground font-bold text-xl">Profil</h2>
      </div>
      <div className="max-w-md">
        <div className="flex items-center gap-4 mb-6 p-4 rounded-xl bg-accent border border-border">
          <div className="w-16 h-16 rounded-full bg-[#222222] flex items-center justify-center text-white text-2xl font-bold">{user.avatar}</div>
          <div>
            <div className="text-foreground font-bold text-lg">{user.name}</div>
            <div className="text-muted-foreground text-sm">{user.email}</div>
            <div className="flex items-center gap-1 mt-1">
              <div className={`w-2 h-2 rounded-full ${statusConfig[status].color}`}/>
              <span className="text-xs text-muted-foreground">{statusConfig[status].label}</span>
            </div>
          </div>
        </div>
        {/* Status otomatis */}
        <div className="bg-accent border border-border rounded-xl p-4 mb-4">
          <h3 className="text-foreground font-semibold text-sm mb-3">Status</h3>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-background border border-border">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse flex-shrink-0"/>
            <div>
              <div className="text-foreground text-sm font-medium">Aktif</div>
              <div className="text-muted-foreground text-xs">Status diatur otomatis berdasarkan aktivitas</div>
            </div>
          </div>
          <p className="text-muted-foreground text-xs mt-2">• Aktif saat menggunakan aplikasi<br/>• Pergi setelah 5 menit tidak aktif<br/>• Offline saat aplikasi ditutup</p>
        </div>

        <div className="flex flex-col gap-4 mb-6">
          <div>
            <label className="text-sm font-medium text-muted-foreground block mb-1.5">Nama tampilan</label>
            <input type="text" value={name} onChange={e => { setName(e.target.value); setSaved(false) }}
              className="w-full px-3 py-2.5 rounded-lg bg-accent border border-border text-foreground text-sm outline-none focus:border-white"/>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground block mb-1.5">Email</label>
            <input type="text" value={user.email} disabled
              className="w-full px-3 py-2.5 rounded-lg bg-muted border border-border text-muted-foreground text-sm cursor-not-allowed"/>
          </div>
          <button onClick={() => setSaved(true)}
            className="w-full py-2.5 rounded-lg bg-white text-black font-bold text-sm hover:bg-gray-100">
            {saved ? '✓ Tersimpan' : 'Simpan perubahan'}
          </button>
        </div>
        <div className="border-t border-border pt-4">
          <button onClick={onLogout}
            className="w-full py-2.5 rounded-lg border border-red-500/30 text-red-400 font-semibold text-sm hover:bg-red-500/10">
            Keluar dari akun
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<User|null>(null)
  const [activePage, setActivePage] = useState('home')
  const [activeChannel, setActiveChannel] = useState('umum')
  const [subPage, setSubPage] = useState('')
  const [showVideoCall, setShowVideoCall] = useState(false)

  if (!user) return <AuthFlow onComplete={setUser} />

  if (showVideoCall) return <VideoCall user={user} onClose={() => setShowVideoCall(false)} />

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
    if (subPage === 'profile') return <ProfilePage user={user} onLogout={() => setUser(null)} onBack={() => setSubPage('')} />
    if (subPage === 'vault') return <VaultPage />
    if (subPage === 'settings') return <SettingsPage />
    if (subPage === 'invite') return <InvitePage user={user} />

    switch(activePage) {
      case 'home': return (
        <>
          <ChannelSidebar onChannelChange={ch => setActiveChannel(ch)} />
          <ChatArea key={activeChannel} channel={activeChannel} currentUser={user} onVideoCall={() => setShowVideoCall(true)} onProfile={() => setSubPage("profile")} />
        </>
      )
      case 'dms': return <DmsPage currentUser={user} />
      case 'activity': return <ActivityPage />
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
        currentUser={user}
        onLogout={() => setUser(null)}
        onProfile={() => setSubPage('profile')}
      />
      {renderContent()}
    </div>
  )
}
