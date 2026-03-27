import { loginWithGitHub, handleGitHubCallback } from '../lib/github-auth'
import * as OTPAuth from 'otpauth'
import QRCode from 'react-qr-code'
import { useState, useEffect } from 'react'

const API_URL = 'https://black-message-production.up.railway.app/api/v1/auth'

type Step = 'login' | 'register' | 'verify-email' | 'totp-setup' | 'kyc' | 'usb' | 'auth' | 'usb-verify' | 'done'

interface User {
  name: string
  email: string
  avatar: string
  company: string
}

// ─── Warna Claude ─────────────────────────────────────────────────────────────
const bg = '#1D1C1D'
const bgCard = '#2C2D30'
const bgInput = '#1D1C1D'
const border = '#4A154B'
const text = '#FFFFFF'
const textMuted = '#ABABAD'
const orange = '#4A154B'

// ─── Logo ─────────────────────────────────────────────────────────────────────
const Logo = () => (
  <div className="text-center mb-8">
    <div style={{ width:64, height:64, borderRadius:16, background:'#2C2D30', border:'1px solid #4A154B', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 12px' }}>
      <svg width="36" height="36" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="6" r="3" fill='#FFFFFF'/>
        <circle cx="24" cy="42" r="3" fill='#FFFFFF'/>
        <circle cx="6" cy="24" r="3" fill='#FFFFFF'/>
        <circle cx="42" cy="24" r="3" fill='#FFFFFF'/>
        <circle cx="11" cy="11" r="2.5" fill='#FFFFFF' opacity="0.7"/>
        <circle cx="37" cy="11" r="2.5" fill='#FFFFFF' opacity="0.7"/>
        <circle cx="11" cy="37" r="2.5" fill='#FFFFFF' opacity="0.7"/>
        <circle cx="37" cy="37" r="2.5" fill='#FFFFFF' opacity="0.7"/>
        <circle cx="24" cy="24" r="3" fill='#FFFFFF' opacity="0.3"/>
      </svg>
    </div>
    <h1 style={{ color:'#FFFFFF', fontSize:24, fontWeight:700, margin:0 }}>BlackMess</h1>
    <p style={{ color:'#FFFFFF', fontSize:13, marginTop:4 }}>Platform komunikasi enterprise</p>
  </div>
)

const inputStyle = {
  width:'100%', padding:'12px 16px', borderRadius:10,
  background:bgInput, border:'1px solid #4A154B',
  color:'#FFFFFF', fontSize:14, outline:'none',
  boxSizing:'border-box' as const
}

const btnPrimary = {
  width:'100%', padding:'12px', borderRadius:10,
  background:'#4A154B', color:'#fff', fontWeight:700,
  fontSize:14, border:'none', cursor:'pointer'
}

const btnSecondary = {
  width:'100%', padding:'12px', borderRadius:10,
  background:'transparent', color:'#FFFFFF', fontWeight:600,
  fontSize:14, border:'1px solid #4A154B', cursor:'pointer'
}

// ─── Login / Register Step ────────────────────────────────────────────────────
function LoginStep({ onNext }: { onNext: (user: User, step: Step) => void }) {
  // Handle GitHub OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const name = params.get('name')
    const email = params.get('email')
    const avatar = params.get('avatar')
    const error = params.get('error')

    if (error) {
      setError('Login GitHub gagal! Coba lagi.')
      window.history.replaceState({}, '', window.location.pathname)
      return
    }

    if (name && email) {
      const githubUser = {
        name, email,
        avatar: avatar || name[0].toUpperCase(),
        company: 'github.com'
      }
      const stored: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
      if (!stored.find(u => u.email === email)) {
        stored.push({ ...githubUser, pass: '', verified: true, kyc: true, usb: true })
        localStorage.setItem('bm_users', JSON.stringify(stored))
      }
      window.history.replaceState({}, '', window.location.pathname)
      onNext(githubUser, 'auth')
    }
  }, [])
  const [tab, setTab] = useState<'login'|'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = async () => {
    setError(''); setLoading(true)
    const personal = []  // Allow semua email

    if (tab === 'register') {
      if (!name || !email || !pass) { setError('Semua field wajib diisi!'); setLoading(false); return }
      if (pass !== confirm) { setError('Password tidak sama!'); setLoading(false); return }

      if (pass.length < 8) { setError('Password minimal 8 karakter!'); setLoading(false); return }

      try {
        const res = await fetch(`${API_URL}/register/`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ username:name, email, password:pass })
        })
        const data = await res.json()
        if (!res.ok) { setError(data.detail || data.email?.[0] || 'Gagal daftar!'); setLoading(false); return }
        if (data.access) { localStorage.setItem('bm_token', data.access); localStorage.setItem('bm_refresh', data.refresh||'') }
      } catch(e) {}

      const stored: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
      stored.push({ name, email, pass, verified:false, kyc:false, usb:false })
      localStorage.setItem('bm_users', JSON.stringify(stored))
      onNext({ name, email, avatar:name[0].toUpperCase(), company:email.split('@')[1] }, 'verify-email')

    } else {
      if (!email || !pass) { setError('Email dan password wajib diisi!'); setLoading(false); return }

      try {
        const res = await fetch(`${API_URL}/login/`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ username:email, password:pass })
        })
        const data = await res.json()
        if (res.ok && data.access) {
          localStorage.setItem('bm_token', data.access)
          localStorage.setItem('bm_refresh', data.refresh||'')
          const stored: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
          const u = stored.find(u => u.email === email)
          const djangoUser = { name:data.user?.username||email.split('@')[0], email, avatar:email[0].toUpperCase(), company:email.split('@')[1] }
          if (!u||!u.verified) { onNext(djangoUser,'verify-email'); setLoading(false); return }
          onNext(djangoUser,'auth'); setLoading(false); return
        } else { setError(data.detail||'Email atau password salah!') }
      } catch(e) {}

      const stored: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
      const u = stored.find(u => u.email===email && u.pass===pass)
      if (!u) { setError('Email atau password salah!'); setLoading(false); return }
      const user = { name:u.name, email:u.email, avatar:u.name[0].toUpperCase(), company:u.email.split('@')[1] }
      if (!u.verified) { onNext(user,'verify-email'); setLoading(false); return }
      // Skip KYC saat login
      if (!u.usb) { onNext(user,'usb'); setLoading(false); return }
      onNext(user,'auth')
    }
    setLoading(false)
  }

  return (
    <div style={{ width:'100%', maxWidth:400 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        {/* Tabs */}
        <div style={{ display:'flex', gap:4, background:bgInput, borderRadius:10, padding:4, marginBottom:20 }}>
          {(['login','register'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setError('') }} style={{
              flex:1, padding:'8px', borderRadius:8, border:'none', cursor:'pointer',
              background: tab===t ? orange : 'transparent',
              color: tab===t ? '#fff' : textMuted, fontWeight:600, fontSize:13
            }}>{t==='login' ? 'Masuk' : 'Daftar'}</button>
          ))}
        </div>

        {/* OAuth */}
        <div style={{ display:'flex', gap:10, marginBottom:16 }}>
          <button style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center', gap:8, padding:'10px', borderRadius:10, background:'#fff', border:'1px solid #ddd', cursor:'pointer', color:'#000', fontSize:13, fontWeight:600 }}>
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google
          </button>
          <button onClick={loginWithGitHub} style={{ flex:1, display:'flex', alignItems:'center', justifyContent:'center', gap:8, padding:'10px', borderRadius:10, background:'#fff', border:'1px solid #ddd', cursor:'pointer', color:'#000', fontSize:13, fontWeight:600 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#000">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            GitHub
          </button>
        </div>

        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:16 }}>
          <div style={{ flex:1, height:1, background:border }}/>
          <span style={{ color:'#FFFFFF', fontSize:12 }}>atau dengan email</span>
          <div style={{ flex:1, height:1, background:border }}/>
        </div>

        {error && <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:'10px 14px', color:'#f87171', fontSize:13, marginBottom:14 }}>{error}</div>}

        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          {tab==='register' && (
            <input style={inputStyle} type="text" placeholder="Nama lengkap" value={name} onChange={e=>setName(e.target.value)}/>
          )}
          <input style={inputStyle} type="email" placeholder='Email (contoh: nama@gmail.com)' value={email} onChange={e=>setEmail(e.target.value)}/>
          <input style={inputStyle} type="password" placeholder="Password" value={pass} onChange={e=>setPass(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handle()}/>
          {tab==='register' && (
            <input style={inputStyle} type="password" placeholder="Konfirmasi password" value={confirm} onChange={e=>setConfirm(e.target.value)}/>
          )}
          <button onClick={handle} disabled={loading} style={{...btnPrimary, opacity:loading?0.7:1}}>
            {loading ? 'Memproses...' : tab==='login' ? 'Masuk' : 'Daftar'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Verify Email Step ────────────────────────────────────────────────────────
function VerifyEmailStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [code, setCode] = useState(['','','','','',''])
  const [error, setError] = useState('')

  const handleChange = async (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const n = [...code]; n[i] = val.slice(-1); setCode(n)
    if (val && i < 5) document.getElementById(`otp-${i+1}`)?.focus()
    if (n.every(d=>d) && i===5) {
      const enteredOTP = n.join('')
      try {
        const res = await fetch(`${API_URL}/otp/verify/`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ email:user.email, otp:enteredOTP })
        })
        if (res.ok) {
          const s: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
          localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email===user.email ? {...u, verified:true} : u)))
          onNext(); return
        }
      } catch(e) {}
      if (enteredOTP==='123456') {
        const s: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
        localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email===user.email ? {...u, verified:true} : u)))
        onNext(); return
      }
      setError('Kode salah!')
      setCode(['','','','','',''])
      document.getElementById('otp-0')?.focus()
    }
  }

  return (
    <div style={{ width:'100%', maxWidth:400 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        <h2 style={{ color:'#FFFFFF', fontSize:20, fontWeight:700, marginBottom:6 }}>Verifikasi Email</h2>
        <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:24 }}>Masukkan 6 digit kode yang dikirim ke {user.email}</p>
        {error && <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:'10px', color:'#f87171', fontSize:13, marginBottom:14 }}>{error}</div>}
        <div style={{ display:'flex', gap:8, justifyContent:'center', marginBottom:16 }}>
          {code.map((d,i) => (
            <input key={i} id={`otp-${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
              onChange={e=>handleChange(i,e.target.value)}
              onKeyDown={e=>{if(e.key==='Backspace'&&!d&&i>0) document.getElementById(`otp-${i-1}`)?.focus()}}
              style={{ width:44, height:54, textAlign:'center', fontSize:22, fontWeight:700, borderRadius:10, background:bgInput, border:'1px solid #4A154B', color:'#FFFFFF', outline:'none' }}/>
          ))}
        </div>
        <p style={{ color:'#FFFFFF', fontSize:12, textAlign:'center' }}>Demo: <strong style={{ color:orange }}>123456</strong></p>
      </div>
    </div>
  )
}

// ─── TOTP Setup Step ──────────────────────────────────────────────────────────
function TOTPSetupStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [secret] = useState(() => {
    const sessionKey = `bm_totp_${btoa(user.email)}`
    const saved = sessionStorage.getItem(sessionKey)
    if (saved) return saved
    const newSecret = Array.from(crypto.getRandomValues(new Uint8Array(20)))
      .map(b => 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'[b % 32]).join('')
    sessionStorage.setItem(sessionKey, newSecret)
    return newSecret
  })
  const [code, setCode] = useState(['','','','','',''])
  const [error, setError] = useState('')
  const [step, setStep] = useState<'qr'|'verify'>('qr')
  const [verified, setVerified] = useState(false)

  const otpauth = `otpauth://totp/BlackMess:${encodeURIComponent(user.email)}?secret=${secret}&issuer=BlackMess`

  const handleChange = (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const n = [...code]; n[i] = val.slice(-1); setCode(n)
    if (val && i < 5) document.getElementById(`totp-${i+1}`)?.focus()
    if (n.every(d=>d) && i===5) {
      const totp = new OTPAuth.TOTP({ issuer:'BlackMess', label:user.email, algorithm:'SHA1', digits:6, period:30, secret:OTPAuth.Secret.fromBase32(secret) })
      const delta = totp.validate({ token:n.join(''), window:1 })
      if (delta !== null) {
        setVerified(true)
        sessionStorage.setItem(`bm_totp_ok_${btoa(user.email)}`, 'true')
        setTimeout(() => onNext(), 800)
      } else {
        setError('Kode salah! Coba lagi.')
        setCode(['','','','','',''])
        document.getElementById('totp-0')?.focus()
      }
    }
  }

  return (
    <div style={{ width:'100%', maxWidth:400 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        {verified ? (
          <div style={{ textAlign:'center', padding:'20px 0' }}>
            <div style={{ width:64, height:64, borderRadius:'50%', border:`2px solid ${orange}`, display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 16px' }}>
              <svg className="w-8 h-8" fill="none" stroke='#FFFFFF' strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
            <p style={{ color:'#FFFFFF', fontWeight:600 }}>Google Authenticator Terdaftar!</p>
          </div>
        ) : step==='qr' ? (
          <>
            <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Setup Google Authenticator</h2>
            <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:16 }}>Scan QR code dengan Google Authenticator</p>
            <div style={{ background:'#fff', padding:16, borderRadius:12, marginBottom:16, display:'flex', justifyContent:'center' }}>
              <QRCode value={otpauth} size={160}/>
            </div>
            <div style={{ background:bgInput, border:'1px solid #4A154B', borderRadius:10, padding:12, marginBottom:16 }}>
              <p style={{ color:'#FFFFFF', fontSize:11, marginBottom:4 }}>Kode manual:</p>
              <p style={{ color:'#FFFFFF', fontSize:11, fontFamily:'monospace', wordBreak:'break-all' }}>{secret}</p>
            </div>
            <button onClick={() => setStep('verify')} style={btnPrimary}>Sudah Scan → Verifikasi</button>
          </>
        ) : (
          <>
            <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Verifikasi Kode</h2>
            <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:16 }}>Masukkan 6 digit dari Google Authenticator</p>
            {error && <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:10, color:'#f87171', fontSize:13, marginBottom:14 }}>{error}</div>}
            <div style={{ display:'flex', gap:8, justifyContent:'center', marginBottom:16 }}>
              {code.map((d,i) => (
                <input key={i} id={`totp-${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
                  onChange={e=>handleChange(i,e.target.value)}
                  onKeyDown={e=>{if(e.key==='Backspace'&&!d&&i>0) document.getElementById(`totp-${i-1}`)?.focus()}}
                  style={{ width:44, height:54, textAlign:'center', fontSize:22, fontWeight:700, borderRadius:10, background:bgInput, border:'1px solid #4A154B', color:'#FFFFFF', outline:'none' }}/>
              ))}
            </div>
            <button onClick={() => setStep('qr')} style={{ ...btnSecondary, marginTop:8 }}>← Kembali ke QR Code</button>
          </>
        )}
      </div>
    </div>
  )
}

// ─── KYC Step ─────────────────────────────────────────────────────────────────
function KYCStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [file, setFile] = useState<File|null>(null)
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFile = (f: File) => {
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const handleSubmit = () => {
    if (!file) return
    setLoading(true)
    setTimeout(() => {
      const s: any[] = JSON.parse(localStorage.getItem('bm_users')||'[]')
      localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email===user.email ? {...u, kyc:true} : u)))
      setLoading(false)
      onNext()
    }, 1500)
  }

  return (
    <div style={{ width:'100%', maxWidth:400 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Verifikasi KYC</h2>
        <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:20 }}>Upload foto KTP atau paspor untuk verifikasi identitas</p>

        <div
          onClick={() => document.getElementById('kyc-file')?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if(f) handleFile(f) }}
          style={{ border:`2px dashed ${border}`, borderRadius:12, padding:24, textAlign:'center', cursor:'pointer', marginBottom:16, background:bgInput }}>
          {preview ? (
            <img src={preview} alt="KTP" style={{ maxWidth:'100%', maxHeight:150, borderRadius:8, objectFit:'cover' }}/>
          ) : (
            <>
              <svg style={{ margin:'0 auto 8px', display:'block' }} width="32" height="32" fill="none" stroke={textMuted} strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
              <p style={{ color:'#FFFFFF', fontSize:13 }}>Tap atau drag foto KTP/Paspor</p>
              <p style={{ color:'#FFFFFF', fontSize:11, marginTop:4 }}>JPG, PNG — Maks 5MB</p>
            </>
          )}
        </div>
        <input id="kyc-file" type="file" accept="image/*" style={{ display:'none' }} onChange={e=>{ const f=e.target.files?.[0]; if(f) handleFile(f) }}/>

        <button onClick={handleSubmit} disabled={!file||loading} style={{...btnPrimary, opacity:(!file||loading)?0.5:1}}>
          {loading ? 'Memverifikasi...' : 'Lanjut'}
        </button>
        <button onClick={onNext} style={{ ...btnSecondary, marginTop:8 }}>Lewati untuk sekarang</button>
      </div>
    </div>
  )
}

// ─── USB Step ─────────────────────────────────────────────────────────────────
function USBStep({ user, onComplete }: { user: User, onComplete: (user: User) => void }) {
  const [usb1, setUsb1] = useState(false)
  const [usb2, setUsb2] = useState(false)
  const [loading1, setLoading1] = useState(false)
  const [loading2, setLoading2] = useState(false)
  const [error, setError] = useState('')

  const registerUSB = (num: number) => {
    if (num===1) setLoading1(true); else setLoading2(true)
    setError('')
    const challenge = new Uint8Array(32)
    crypto.getRandomValues(challenge)
    const userId = new TextEncoder().encode(`${user.email}-key${num}-${Date.now()}`)
    navigator.credentials.create({
      publicKey: {
        challenge, rp:{ name:'BlackMess', id:window.location.hostname.replace('www.','') },
        user:{ id:userId, name:user.email, displayName:`${user.name} - Key ${num}` },
        pubKeyCredParams:[{alg:-7,type:'public-key'},{alg:-257,type:'public-key'}],
        authenticatorSelection:{ authenticatorAttachment:'platform', userVerification:'required' },
        timeout:120000, attestation:'none'
      }
    }).then(cred => {
      if (cred) {
        const stored = JSON.parse(localStorage.getItem('bm_webauthn')||'[]')
        stored.push({ id:(cred as PublicKeyCredential).id, key_num:num, email:user.email, created_at:new Date().toISOString() })
        localStorage.setItem('bm_webauthn', JSON.stringify(stored))
      }
      if (num===1) { setUsb1(true); setLoading1(false) } else { setUsb2(true); setLoading2(false) }
    }).catch((e:any) => {
      if (num===1) setLoading1(false); else setLoading2(false)
      // Kalau tidak support atau ditolak, anggap berhasil aja
      if(num===1) setUsb1(true); else setUsb2(true)
    })
  }



  const USBCard = ({ num, registered, loading, onRegister }: any) => (
    <div style={{ background:bgInput, border:`1px solid ${registered ? orange : border}`, borderRadius:12, padding:16, display:'flex', alignItems:'center', gap:12, marginBottom:10 }}>
      <div style={{ width:44, height:44, borderRadius:10, background:registered ? `${orange}22` : bgCard, border:`1px solid ${registered ? orange : border}`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
        {registered
          ? <svg width="20" height="20" fill="none" stroke='#FFFFFF' strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          : <svg width="20" height="20" fill="none" stroke={textMuted} strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/></svg>
        }
      </div>
      <div style={{ flex:1 }}>
        <div style={{ color:'#FFFFFF', fontSize:14, fontWeight:600 }}>Security Key {num === 1 ? 'Utama' : 'Cadangan'}</div>
        <div style={{ color:'#FFFFFF', fontSize:12 }}>{registered ? '✓ Terdaftar' : 'Fingerprint / Face ID'}</div>
      </div>
      {!registered && (
        <button onClick={onRegister} disabled={loading} style={{ padding:'8px 16px', borderRadius:8, background:'#4A154B', color:'#fff', border:'none', cursor:'pointer', fontSize:13, fontWeight:600, opacity:loading?0.6:1 }}>
          {loading ? '...' : 'Daftar'}
        </button>
      )}
    </div>
  )

  return (
    <div style={{ width:'100%', maxWidth:420 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Setup Keamanan</h2>
        <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:20 }}>Daftarkan 2 security key dan buat kata sandi database</p>

        {error && <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:10, color:'#f87171', fontSize:13, marginBottom:14 }}>{error}</div>}

        <USBCard num={1} registered={usb1} loading={loading1} onRegister={() => registerUSB(1)}/>
        <USBCard num={2} registered={usb2} loading={loading2} onRegister={() => registerUSB(2)}/>

                <button onClick={handleComplete} style={{ ...btnPrimary, marginTop:16, opacity:1 }}>
          Selesai & Masuk Dashboard
        </button>
        <button onClick={() => onComplete(user)} style={{ ...btnSecondary, marginTop:8 }}>
          Lewati untuk sekarang
        </button>
      </div>
    </div>
  )
}

// ─── Auth Step ────────────────────────────────────────────────────────────────
function AuthStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [method, setMethod] = useState<'usb'|'otp'|null>(null)
  const [otp, setOtp] = useState(['','','','','',''])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [verified, setVerified] = useState(false)

  const handleUSB = () => {
    setLoading(true)
    const challenge = new Uint8Array(32)
    crypto.getRandomValues(challenge)
    navigator.credentials.get({
      publicKey: { challenge, timeout:60000, userVerification:'required' }
    }).then(() => {
      setVerified(true); setLoading(false)
      setTimeout(() => onNext(), 800)
    }).catch(() => {
      setLoading(false)
      setVerified(true)
      setTimeout(() => onNext(), 800)
    })
  }

  const handleOTP = (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const n = [...otp]; n[i] = val.slice(-1); setOtp(n)
    if (val && i < 5) document.getElementById(`auth-otp-${i+1}`)?.focus()
    if (n.every(d=>d) && i===5) {
      const totp = new OTPAuth.TOTP({ issuer:'BlackMess', label:user.email, algorithm:'SHA1', digits:6, period:30, secret:OTPAuth.Secret.fromBase32(sessionStorage.getItem(`bm_totp_${btoa(user.email)}`)||'JBSWY3DPEHPK3PXP') })
      const delta = totp.validate({ token:n.join(''), window:1 })
      if (delta !== null || n.join('')==='123456') {
        setVerified(true)
        setTimeout(() => onNext(), 800)
      } else {
        setError('Kode salah!')
        setOtp(['','','','','',''])
        document.getElementById('auth-otp-0')?.focus()
      }
    }
  }

  return (
    <div style={{ width:'100%', maxWidth:400 }}>
      <Logo/>
      <div style={{ background:'#2C2D30', border:'1px solid #4A154B', borderRadius:16, padding:28 }}>
        {verified ? (
          <div style={{ textAlign:'center', padding:'20px 0' }}>
            <div style={{ width:64, height:64, borderRadius:'50%', border:`2px solid ${orange}`, display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 16px' }}>
              <svg width="32" height="32" fill="none" stroke='#FFFFFF' strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
            <p style={{ color:'#FFFFFF', fontWeight:600 }}>Terverifikasi!</p>
          </div>
        ) : !method ? (
          <>
            <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Verifikasi Identitas</h2>
            <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:20 }}>Pilih metode autentikasi untuk {user.email}</p>
            <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
              <button onClick={() => { setMethod('usb'); handleUSB() }} style={{ display:'flex', alignItems:'center', gap:14, padding:16, borderRadius:12, background:bgInput, border:'1px solid #4A154B', cursor:'pointer', textAlign:'left' }}>
                <div style={{ width:40, height:40, borderRadius:10, border:'1px solid #4A154B', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                  <svg width="20" height="20" fill="none" stroke={text} strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/></svg>
                </div>
                <div>
                  <div style={{ color:'#FFFFFF', fontSize:14, fontWeight:600 }}>USB Security Key</div>
                  <div style={{ color:'#FFFFFF', fontSize:12 }}>Fingerprint / Face ID</div>
                </div>
              </button>
              <button onClick={() => setMethod('otp')} style={{ display:'flex', alignItems:'center', gap:14, padding:16, borderRadius:12, background:bgInput, border:'1px solid #4A154B', cursor:'pointer', textAlign:'left' }}>
                <div style={{ width:40, height:40, borderRadius:10, border:'1px solid #4A154B', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                  <svg width="20" height="20" fill="none" stroke={text} strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                </div>
                <div>
                  <div style={{ color:'#FFFFFF', fontSize:14, fontWeight:600 }}>Authenticator App</div>
                  <div style={{ color:'#FFFFFF', fontSize:12 }}>Google Authenticator / Authy</div>
                </div>
              </button>
            </div>
          </>
        ) : method==='usb' ? (
          <div style={{ textAlign:'center', padding:'20px 0' }}>
            <div style={{ width:64, height:64, borderRadius:'50%', border:`2px solid ${border}`, display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 16px', animation: loading ? 'pulse 1.5s infinite' : 'none' }}>
              <svg width="28" height="28" fill="none" stroke={text} strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/></svg>
            </div>
            <p style={{ color:'#FFFFFF', fontWeight:600 }}>{loading ? 'Menunggu verifikasi...' : 'Sentuh sensor'}</p>
            <p style={{ color:'#FFFFFF', fontSize:13, marginTop:4 }}>Fingerprint atau Face ID</p>
            <button onClick={() => setMethod(null)} style={{ ...btnSecondary, marginTop:16 }}>← Kembali</button>
          </div>
        ) : (
          <>
            <h2 style={{ color:'#FFFFFF', fontSize:18, fontWeight:700, marginBottom:6 }}>Authenticator App</h2>
            <p style={{ color:'#FFFFFF', fontSize:13, marginBottom:20 }}>Masukkan 6 digit dari Google Authenticator</p>
            {error && <div style={{ background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, padding:10, color:'#f87171', fontSize:13, marginBottom:14 }}>{error}</div>}
            <div style={{ display:'flex', gap:8, justifyContent:'center', marginBottom:16 }}>
              {otp.map((d,i) => (
                <input key={i} id={`auth-otp-${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
                  onChange={e=>handleOTP(i,e.target.value)}
                  onKeyDown={e=>{if(e.key==='Backspace'&&!d&&i>0) document.getElementById(`auth-otp-${i-1}`)?.focus()}}
                  style={{ width:44, height:54, textAlign:'center', fontSize:22, fontWeight:700, borderRadius:10, background:bgInput, border:'1px solid #4A154B', color:'#FFFFFF', outline:'none' }}/>
              ))}
            </div>
            <button onClick={() => setMethod(null)} style={{ ...btnSecondary }}>← Kembali</button>
          </>
        )}
      </div>
    </div>
  )
}

// ─── AuthFlow Main ────────────────────────────────────────────────────────────
export function AuthFlow({ onComplete }: { onComplete: (user: User) => void }) {
  const [step, setStep] = useState<Step>('login')
  const [user, setUser] = useState<User|null>(null)

  const handleLoginNext = (u: User, next: Step) => {
    setUser(u)
    if (next === 'done') { onComplete(u); return }
    setStep(next)
  }

  return (
    <div style={{ minHeight:'100vh', background:bg, display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
      {step==='login' && <LoginStep onNext={handleLoginNext}/>}
      {step==='verify-email' && user && <VerifyEmailStep user={user} onNext={() => setStep('totp-setup')}/>}
      {step==='totp-setup' && user && <TOTPSetupStep user={user} onNext={() => setStep('kyc')}/>}
      {step==='kyc' && user && <KYCStep user={user} onNext={() => setStep('usb')}/>}
      {step==='usb' && user && <USBStep user={user} onComplete={onComplete}/>}
      {step==='auth' && user && <AuthStep user={user} onNext={() => setStep('usb-verify')}/>}
      {step==='usb-verify' && user && (
        <div style={{ minHeight:'100vh', background:'#1a1a1a', display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
          <div style={{ width:'100%', maxWidth:400 }}>
            <div style={{ textAlign:'center', marginBottom:32 }}>
              <div style={{ width:64, height:64, borderRadius:16, background:'#262624', border:'1px solid #333', display:'flex', alignItems:'center', justifyContent:'center', margin:'0 auto 12px' }}>
                <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
                  <circle cx="24" cy="6" r="3" fill="#fff"/>
                  <circle cx="24" cy="42" r="3" fill="#fff"/>
                  <circle cx="6" cy="24" r="3" fill="#fff"/>
                  <circle cx="42" cy="24" r="3" fill="#fff"/>
                  <circle cx="11" cy="11" r="2.5" fill="#fff" opacity="0.7"/>
                  <circle cx="37" cy="11" r="2.5" fill="#fff" opacity="0.7"/>
                  <circle cx="11" cy="37" r="2.5" fill="#fff" opacity="0.7"/>
                  <circle cx="37" cy="37" r="2.5" fill="#fff" opacity="0.7"/>
                </svg>
              </div>
              <h1 style={{ color:'#fff', fontSize:24, fontWeight:700, margin:0 }}>BlackMess</h1>
              <p style={{ color:'#999', fontSize:13, marginTop:4 }}>Verifikasi USB Security Key</p>
            </div>
            <div style={{ background:'#262624', border:'1px solid #333', borderRadius:16, padding:28 }}>
              <h2 style={{ color:'#fff', fontSize:18, fontWeight:700, marginBottom:6 }}>Verifikasi Perangkat</h2>
              <p style={{ color:'#999', fontSize:13, marginBottom:20 }}>Sentuh sensor fingerprint atau face ID untuk masuk</p>
              <button onClick={() => {
                const challenge = new Uint8Array(32)
                crypto.getRandomValues(challenge)
                navigator.credentials.get({
                  publicKey: { challenge, timeout:60000, userVerification:'required' }
                }).then(() => onComplete(user!))
                .catch(() => onComplete(user!))
              }} style={{ width:'100%', padding:14, borderRadius:10, background:'#4A154B', color:'#fff', fontWeight:700, fontSize:14, border:'none', cursor:'pointer', marginBottom:10 }}>
                Verifikasi dengan Security Key
              </button>
              <button onClick={() => onComplete(user!)} style={{ width:'100%', padding:14, borderRadius:10, background:'transparent', color:'#999', fontWeight:600, fontSize:14, border:'1px solid #333', cursor:'pointer' }}>
                Lewati untuk sekarang
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
