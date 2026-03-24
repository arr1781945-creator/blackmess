import { useState } from 'react'

const CHANNELS = [
  { id: '1', name: 'umum', private: false, type: 'hash' },
  { id: '2', name: 'acak', private: false, type: 'hash' },
  { id: '3', name: 'meja-perdagangan', private: true, type: 'trading' },
  { id: '4', name: 'kehadiran', private: false, type: 'hash' },
  { id: '5', name: 'operasi-brankas', private: true, type: 'vault' },
]

const CHANNEL_CONTENT: Record<string, any> = {
  'umum': {
    type: 'announcements',
    items: [
      { id: 1, user: 'Admin', avatar: 'AD', msg: '📢 Selamat datang di BlackMess! Platform kerja remote enterprise.', time: '09:00', pinned: true },
      { id: 2, user: 'Admin', avatar: 'AD', msg: '📢 Maintenance server dijadwalkan Sabtu 00:00 - 02:00 WIB.', time: '08:30', pinned: true },
      { id: 3, user: 'Admin', avatar: 'AD', msg: '📢 Update fitur baru: E2EE messaging sekarang aktif untuk semua channel.', time: '08:00', pinned: false },
    ]
  },
  'acak': {
    type: 'random',
    items: [
      { id: 1, user: 'Dimas A.', avatar: 'DA', msg: 'Ada yang mau lunch bareng jam 12? 🍜', time: '10:01', pinned: false },
      { id: 2, user: 'Putri N.', avatar: 'PN', msg: 'Happy Monday semua! Semangat kerjanya 💪', time: '09:55', pinned: false },
      { id: 3, user: 'Reza F.', avatar: 'RF', msg: 'Weekend kemarin hiking ke Bromo, keren banget!', time: '09:30', pinned: false },
      { id: 4, user: 'Toni S.', avatar: 'TS', msg: 'Coffee run anyone? Gw mau ke bawah nih', time: '09:10', pinned: false },
    ]
  },
  'meja-perdagangan': {
    type: 'trading',
    stats: [
      { label: 'Sesi Aktif', value: '2,847', change: '+12%', color: '#6366f1' },
      { label: 'Pesan Hari Ini', value: '18,294', change: '+8%', color: '#8b5cf6' },
      { label: 'Transaksi', value: 'Rp 4.2M', change: '+23%', color: '#06b6d4' },
      { label: 'Skor Keamanan', value: '98.5%', change: '+0.3%', color: '#10b981' },
    ],
    items: [
      { id: 1, user: 'Trader-1', avatar: 'T1', msg: 'SWIFT Transfer JPMorgan — Rp 500M executed', time: '09:50', pinned: false },
      { id: 2, user: 'Trader-2', avatar: 'T2', msg: 'FX Trade USD/IDR — buy 2M at 15,750', time: '09:35', pinned: false },
      { id: 3, user: 'Risk', avatar: 'RK', msg: 'VaR limit 80% — monitor closely', time: '09:00', pinned: false },
    ]
  },
  'kehadiran': {
    type: 'attendance',
    members: [
      { name: 'Akbar', avatar: 'AK', status: 'online', role: 'CEO & Developer', checkin: '07:30', mood: '💪' },
      { name: 'Ahmad R.', avatar: 'AR', status: 'online', role: 'Compliance Officer', checkin: '08:00', mood: '😊' },
      { name: 'Sarah K.', avatar: 'SK', status: 'online', role: 'Trading Analyst', checkin: '08:15', mood: '🔥' },
      { name: 'Budi S.', avatar: 'BS', status: 'away', role: 'KYC Specialist', checkin: '08:30', mood: '😴' },
      { name: 'Linda M.', avatar: 'LM', status: 'online', role: 'AML Officer', checkin: '08:45', mood: '💻' },
    ]
  },
  'operasi-brankas': {
    type: 'vault',
    items: [
      { id: 1, name: 'KYC Records', desc: '847 data terverifikasi', icon: 'kyc', locked: true },
      { id: 2, name: 'Kunci PQC', desc: 'Kyber-1024 + ML-DSA-65 aktif', icon: 'key', locked: true },
      { id: 3, name: 'Dokumen Rahasia', desc: '23 file terenkripsi AES-256', icon: 'doc', locked: true },
      { id: 4, name: 'Backup Database', desc: 'Last backup: hari ini 06:00', icon: 'db', locked: true },
    ]
  },
}



// SVG Icons
const HomeIcon = () => (
  <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
  </svg>
)

const MessageIcon = () => (
  <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
  </svg>
)

const SearchIcon = () => (
  <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
  </svg>
)

const MoreIcon = () => (
  <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
  </svg>
)

const HashIcon = () => (
  <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/>
  </svg>
)

const LockIcon = () => (
  <svg width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
  </svg>
)

const SendIcon = () => (
  <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
  </svg>
)

export default function Dashboard({ token, onLogout }: { token: string, onLogout: () => void }) {
  const [activePage, setActivePage] = useState<'home'|'messages'|'search'|'more'>('home')
  const [activeChannel, setActiveChannel] = useState('general')
  const [message, setMessage] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const navItems = [
    { id: 'home', label: 'Home', icon: <HomeIcon/> },
    { id: 'messages', label: 'Pesan', icon: <MessageIcon/> },
    { id: 'search', label: 'Cari', icon: <SearchIcon/> },
    { id: 'more', label: 'Lainnya', icon: <MoreIcon/> },
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#000000', fontFamily:'Inter,system-ui,sans-serif', color:'white' }}>

      {/* TOPBAR */}
      <div style={{ height:52, background:'#000000', borderBottom:'1px solid rgba(255,255,255,0.08)', display:'flex', alignItems:'center', padding:'0 16px', gap:12, flexShrink:0 }}>
        {/* Toggle sidebar */}
        <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{ background:'none', border:'none', color:'rgba(255,255,255,0.5)', cursor:'pointer', padding:4, display:'flex' }}>
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h7"/>
          </svg>
        </button>

        {/* Logo */}
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ width:28, height:28, borderRadius:8, background:'#ffffff', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
            <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
              <ellipse cx="16" cy="16" rx="14" ry="5.5" stroke="#f97316" strokeWidth="2" opacity="0.5"/>
              <ellipse cx="16" cy="16" rx="10" ry="3.5" stroke="#fbbf24" strokeWidth="2.5" opacity="0.8"/>
              <ellipse cx="16" cy="16" rx="6.5" ry="2" stroke="#fde68a" strokeWidth="2.5"/>
              <circle cx="16" cy="16" r="4.5" fill="#000000"/>
              <circle cx="16" cy="16" r="3.5" fill="#050508"/>
            </svg>
          </div>
          <span style={{ color:'white', fontWeight:700, fontSize:15 }}>BlackMess</span>
        </div>

        <div style={{ flex:1 }}/>

        {/* Search bar */}
        <div style={{ display:'flex', alignItems:'center', gap:8, background:'rgba(255,255,255,0.06)', borderRadius:8, padding:'6px 12px', border:'1px solid rgba(255,255,255,0.08)' }}>
          <svg width="13" height="13" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <span style={{ color:'rgba(255,255,255,0.3)', fontSize:12 }}>Cari...</span>
        </div>

        {/* E2EE badge */}
        <div style={{ display:'flex', alignItems:'center', gap:5, background:'rgba(34,197,94,0.08)', borderRadius:20, padding:'4px 10px', border:'1px solid rgba(34,197,94,0.2)' }}>
          <div style={{ width:6, height:6, borderRadius:'50%', background:'#22c55e' }}/>
          <span style={{ color:'#22c55e', fontSize:10, fontWeight:500 }}>E2EE</span>
        </div>

        {/* Profile button pojok kanan atas */}
        <button onClick={onLogout} style={{ width:34, height:34, borderRadius:'50%', background:'#222222', border:'2px solid rgba(99,102,241,0.5)', cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:12, fontWeight:700 }}>
          U
        </button>
      </div>

      {/* MAIN BODY */}
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>

        {/* SIDEBAR */}
        {sidebarOpen && (
          <div style={{ width:220, background:'#0a0a0a', borderRight:'1px solid rgba(255,255,255,0.06)', display:'flex', flexDirection:'column', flexShrink:0, overflow:'hidden' }}>
            <div style={{ padding:'12px 16px', borderBottom:'1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color:'white', fontWeight:700, fontSize:14 }}>BlackMess</div>
              <div style={{ color:'rgba(255,255,255,0.3)', fontSize:11 }}>Enterprise · 47 anggota</div>
            </div>

            <div style={{ flex:1, overflowY:'auto', padding:'8px 4px' }}>
              <div style={{ color:'rgba(255,255,255,0.2)', fontSize:10, fontWeight:700, padding:'4px 12px', letterSpacing:1, textTransform:'uppercase', marginTop:8 }}>Saluran</div>
              {CHANNELS.map(ch => (
                <button key={ch.id} onClick={() => { setActiveChannel(ch.name); setActivePage('messages') }} style={{
                  display:'flex', alignItems:'center', gap:8, width:'100%', padding:'7px 12px',
                  borderRadius:8, border:'none', cursor:'pointer', fontFamily:'inherit',
                  background: activeChannel === ch.name && activePage === 'messages' ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: activeChannel === ch.name && activePage === 'messages' ? '#818cf8' : 'rgba(255,255,255,0.4)',
                  fontSize:13, textAlign:'left',
                  borderLeft: activeChannel === ch.name && activePage === 'messages' ? '2px solid #6366f1' : '2px solid transparent',
                }}>
                  <span style={{ color:'rgba(255,255,255,0.3)' }}>{ch.private ? <LockIcon/> : <HashIcon/>}</span>
                  {ch.name}
                </button>
              ))}
            </div>

            {/* User footer */}
            <div style={{ padding:12, borderTop:'1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display:'flex', alignItems:'center', gap:8, padding:8, borderRadius:10, cursor:'pointer' }}>
                <div style={{ width:30, height:30, borderRadius:8, background:'#222222', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:11, fontWeight:700, flexShrink:0 }}>U</div>
                <div>
                  <div style={{ color:'white', fontSize:12, fontWeight:600 }}>Pengguna</div>
                  <div style={{ color:'#22c55e', fontSize:10 }}>● Aktif</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* CONTENT AREA */}
        <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden', background:'#000000' }}>

          {/* HOME PAGE */}
          {activePage === 'home' && (
            <div style={{ flex:1, overflowY:'auto', padding:16 }}>
              <h2 style={{ color:'white', fontSize:18, fontWeight:700, marginBottom:4 }}>Selamat datang 👋</h2>
              <p style={{ color:'rgba(255,255,255,0.4)', fontSize:13, marginBottom:20 }}>Pilih saluran untuk memulai</p>

              {/* Channel list */}
              {CHANNELS.map(ch => (
                <div key={ch.id} onClick={() => { setActiveChannel(ch.name); setActivePage('messages') }}
                  style={{ display:'flex', alignItems:'center', gap:12, padding:'14px 16px', background:'#111111', borderRadius:12, marginBottom:10, border:'1px solid rgba(255,255,255,0.06)', cursor:'pointer' }}>
                  <div style={{ width:40, height:40, borderRadius:12, background:'rgba(255,255,255,0.06)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                    {ch.private
                      ? <svg width="18" height="18" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                      : <svg width="18" height="18" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"/></svg>
                    }
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ color:'white', fontWeight:600, fontSize:14 }}>#{ch.name}</div>
                    <div style={{ color:'rgba(255,255,255,0.3)', fontSize:12, marginTop:2 }}>
                      {ch.name === 'umum' && 'Pengumuman resmi workspace'}
                      {ch.name === 'acak' && 'Obrolan santai tim'}
                      {ch.name === 'meja-perdagangan' && 'Live trading & statistik'}
                      {ch.name === 'kehadiran' && 'Status kehadiran tim'}
                      {ch.name === 'operasi-brankas' && 'Data sensitif terenkripsi'}
                    </div>
                  </div>
                  <svg width="16" height="16" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              ))}
            </div>
          )}

          {/* MESSAGES PAGE */}
          {activePage === 'messages' && (
            <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
              <div style={{ padding:'12px 16px', borderBottom:'1px solid rgba(255,255,255,0.06)', display:'flex', alignItems:'center', gap:8 }}>
                <span style={{ color:'rgba(255,255,255,0.4)' }}><HashIcon/></span>
                <span style={{ color:'white', fontWeight:600, fontSize:15 }}>{activeChannel}</span>
                <div style={{ flex:1 }}/>
                <span style={{ color:'rgba(255,255,255,0.2)', fontSize:11 }}>E2EE aktif</span>
              </div>

              <div style={{ flex:1, overflowY:'auto', padding:16 }}>

                {/* UMUM - Pengumuman */}
                {activeChannel === 'umum' && (
                  <div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginBottom:12 }}>📌 Pengumuman resmi workspace</div>
                    {CHANNEL_CONTENT['umum'].items.map((m: any) => (
                      <div key={m.id} style={{ display:'flex', gap:10, padding:'10px 12px', borderRadius:10, background: m.pinned ? 'rgba(99,102,241,0.08)' : 'transparent', border: m.pinned ? '1px solid rgba(99,102,241,0.15)' : '1px solid transparent', marginBottom:8 }}>
                        <div style={{ width:34, height:34, borderRadius:10, background:'#222', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:11, fontWeight:700, flexShrink:0 }}>{m.avatar}</div>
                        <div>
                          <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                            <span style={{ color:'white', fontWeight:600, fontSize:13 }}>{m.user}</span>
                            {m.pinned && <span style={{ color:'#818cf8', fontSize:10, background:'rgba(99,102,241,0.1)', padding:'2px 6px', borderRadius:4 }}>📌 Disematkan</span>}
                            <span style={{ color:'rgba(255,255,255,0.2)', fontSize:11 }}>{m.time}</span>
                          </div>
                          <div style={{ color:'rgba(255,255,255,0.7)', fontSize:13, marginTop:2 }}>{m.msg}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* ACAK - Chat iseng */}
                {activeChannel === 'acak' && (
                  <div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginBottom:12 }}>💬 Obrolan santai tim</div>
                    {CHANNEL_CONTENT['acak'].items.map((m: any) => (
                      <div key={m.id} style={{ display:'flex', gap:10, padding:'8px 4px', marginBottom:6 }}>
                        <div style={{ width:34, height:34, borderRadius:10, background:'#222', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:11, fontWeight:700, flexShrink:0 }}>{m.avatar}</div>
                        <div>
                          <div style={{ display:'flex', gap:8, alignItems:'baseline' }}>
                            <span style={{ color:'white', fontWeight:600, fontSize:13 }}>{m.user}</span>
                            <span style={{ color:'rgba(255,255,255,0.2)', fontSize:11 }}>{m.time}</span>
                          </div>
                          <div style={{ color:'rgba(255,255,255,0.7)', fontSize:13, marginTop:2 }}>{m.msg}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* MEJA PERDAGANGAN - Stats + chat */}
                {activeChannel === 'meja-perdagangan' && (
                  <div>
                    <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:10, marginBottom:16 }}>
                      {CHANNEL_CONTENT['meja-perdagangan'].stats.map((s: any) => (
                        <div key={s.label} style={{ background:'#111', border:'1px solid rgba(255,255,255,0.06)', borderRadius:12, padding:14 }}>
                          <div style={{ color:'rgba(255,255,255,0.4)', fontSize:11, marginBottom:4 }}>{s.label}</div>
                          <div style={{ color:s.color, fontSize:20, fontWeight:700 }}>{s.value}</div>
                          <div style={{ color:'#22c55e', fontSize:11 }}>▲ {s.change}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginBottom:10 }}>Live trading feed</div>
                    {CHANNEL_CONTENT['meja-perdagangan'].items.map((m: any) => (
                      <div key={m.id} style={{ display:'flex', gap:10, padding:'8px 4px', marginBottom:6 }}>
                        <div style={{ width:34, height:34, borderRadius:10, background:'#222', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:11, fontWeight:700, flexShrink:0 }}>{m.avatar}</div>
                        <div>
                          <div style={{ display:'flex', gap:8, alignItems:'baseline' }}>
                            <span style={{ color:'white', fontWeight:600, fontSize:13 }}>{m.user}</span>
                            <span style={{ color:'rgba(255,255,255,0.2)', fontSize:11 }}>{m.time}</span>
                          </div>
                          <div style={{ color:'rgba(255,255,255,0.7)', fontSize:13, marginTop:2 }}>{m.msg}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* KEHADIRAN - Daftar orang */}
                {activeChannel === 'kehadiran' && (
                  <div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginBottom:12 }}>👥 Status kehadiran tim hari ini</div>
                    {CHANNEL_CONTENT['kehadiran'].members.map((m: any, i: number) => (
                      <div key={i} style={{ display:'flex', alignItems:'center', gap:12, padding:'12px 16px', background:'#111', borderRadius:12, marginBottom:8, border:'1px solid rgba(255,255,255,0.06)' }}>
                        <div style={{ position:'relative', flexShrink:0 }}>
                          <div style={{ width:40, height:40, borderRadius:12, background: m.name === 'Akbar' ? '#ffffff' : '#222', display:'flex', alignItems:'center', justifyContent:'center', color: m.name === 'Akbar' ? '#000' : 'white', fontSize:12, fontWeight:700 }}>{m.avatar}</div>
                          <span style={{ position:'absolute', bottom:-2, right:-2, width:12, height:12, borderRadius:'50%', background: m.status === 'online' ? '#22c55e' : '#f59e0b', border:'2px solid #000' }}/>
                        </div>
                        <div style={{ flex:1 }}>
                          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                            <span style={{ color:'white', fontWeight:700, fontSize:14 }}>{m.name}</span>
                            {m.name === 'Akbar' && <span style={{ color:'#fbbf24', fontSize:10, background:'rgba(251,191,36,0.1)', padding:'2px 6px', borderRadius:4 }}>CEO</span>}
                          </div>
                          <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12 }}>{m.role}</div>
                        </div>
                        <div style={{ textAlign:'right' }}>
                          <div style={{ color:'rgba(255,255,255,0.4)', fontSize:11 }}>Masuk {m.checkin}</div>
                          <div style={{ fontSize:16, marginTop:2 }}>{m.mood}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* OPERASI BRANKAS - Vault */}
                {activeChannel === 'operasi-brankas' && (
                  <div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginBottom:12 }}>🔐 Data sensitif terenkripsi E2EE + PQC</div>
                    {CHANNEL_CONTENT['operasi-brankas'].items.map((item: any) => (
                      <div key={item.id} style={{ display:'flex', alignItems:'center', gap:14, padding:'14px 16px', background:'#111', borderRadius:12, marginBottom:10, border:'1px solid rgba(255,255,255,0.06)' }}>
                        <div style={{ width:40, height:40, borderRadius:12, background:'rgba(251,191,36,0.1)', border:'1px solid rgba(251,191,36,0.2)', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                          <svg width="20" height="20" fill="none" stroke="#fbbf24" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                          </svg>
                        </div>
                        <div style={{ flex:1 }}>
                          <div style={{ color:'white', fontWeight:600, fontSize:14 }}>{item.name}</div>
                          <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12, marginTop:2 }}>{item.desc}</div>
                        </div>
                        <div style={{ display:'flex', alignItems:'center', gap:4, color:'#22c55e', fontSize:11 }}>
                          <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                          </svg>
                          Terkunci
                        </div>
                      </div>
                    ))}
                  </div>
                )}

              </div>

              {/* Input - sembunyikan di vault & kehadiran */}
              {activeChannel !== 'operasi-brankas' && activeChannel !== 'kehadiran' && (
                <div style={{ padding:'12px 16px', borderTop:'1px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:10, background:'rgba(255,255,255,0.04)', borderRadius:10, border:'1px solid rgba(255,255,255,0.08)', padding:'10px 14px' }}>
                    <input type="text" value={message} onChange={e => setMessage(e.target.value)} placeholder={`Pesan ke #${activeChannel}`}
                      style={{ flex:1, background:'transparent', border:'none', outline:'none', color:'white', fontSize:14, fontFamily:'inherit' }}/>
                    <button onClick={() => setMessage('')} style={{ background: message ? '#ffffff' : 'rgba(255,255,255,0.05)', border:'none', borderRadius:8, width:32, height:32, cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center', color: message ? '#000' : 'white' }}>
                      <SendIcon/>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SEARCH PAGE */}
          {activePage === 'search' && (
            <div style={{ flex:1, padding:20 }}>
              <h2 style={{ color:'white', fontSize:18, fontWeight:700, marginBottom:16 }}>Cari</h2>
              <div style={{ display:'flex', alignItems:'center', gap:10, background:'rgba(255,255,255,0.06)', borderRadius:12, padding:'12px 16px', border:'1px solid rgba(255,255,255,0.1)', marginBottom:20 }}>
                <SearchIcon/>
                <input type="text" placeholder="Cari pesan, file, pengguna..." style={{ flex:1, background:'transparent', border:'none', outline:'none', color:'white', fontSize:14, fontFamily:'inherit' }}/>
              </div>
              <p style={{ color:'rgba(255,255,255,0.3)', fontSize:13 }}>Ketik untuk mulai mencari...</p>
            </div>
          )}

          {/* MORE PAGE */}
          {activePage === 'more' && (
            <div style={{ flex:1, overflowY:'auto', padding:20 }}>
              <h2 style={{ color:'white', fontSize:18, fontWeight:700, marginBottom:16 }}>Lainnya</h2>
              {[
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>, label: 'Vault', desc: 'Penyimpanan terenkripsi' },
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>, label: 'Analitik', desc: 'Laporan dan metrik' },
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Pengaturan', desc: 'Konfigurasi akun' },
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>, label: 'Anggota', desc: '47 anggota aktif' },
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg>, label: 'File', desc: 'Penyimpanan file terenkripsi' },
                { icon: <svg width="22" height="22" fill="none" stroke="white" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>, label: 'Notifikasi', desc: 'Kelola notifikasi' },
              ].map(item => (
                <div key={item.label} style={{ display:'flex', alignItems:'center', gap:14, padding:'14px 16px', borderRadius:12, background:'#111111', border:'1px solid rgba(255,255,255,0.06)', marginBottom:10, cursor:'pointer' }}>
                  <span style={{ fontSize:22 }}>{item.icon}</span>
                  <div>
                    <div style={{ color:'white', fontWeight:600, fontSize:14 }}>{item.label}</div>
                    <div style={{ color:'rgba(255,255,255,0.4)', fontSize:12 }}>{item.desc}</div>
                  </div>
                  <div style={{ flex:1 }}/>
                  <svg width="16" height="16" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>

      {/* BOTTOM NAV */}
      <div style={{ height:60, background:'#000000', borderTop:'1px solid rgba(255,255,255,0.08)', display:'flex', alignItems:'center', justifyContent:'space-around', flexShrink:0, paddingBottom:4 }}>
        {navItems.map(item => (
          <button key={item.id} onClick={() => setActivePage(item.id as any)} style={{
            display:'flex', flexDirection:'column', alignItems:'center', gap:3,
            background: activePage === item.id ? 'rgba(255,255,255,0.08)' : 'none',
            border:'none', cursor:'pointer',
            color: activePage === item.id ? '#ffffff' : 'rgba(255,255,255,0.35)',
            padding:'6px 16px', borderRadius:10,
            transition:'all 0.15s',
            borderTop: activePage === item.id ? '2px solid #ffffff' : '2px solid transparent'
          }}>
            {item.icon}
            <span style={{ fontSize:10, fontWeight: activePage === item.id ? 600 : 400 }}>{item.label}</span>
          </button>
        ))}
      </div>

    </div>
  )
}
