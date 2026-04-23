import { loginWithGitHub, handleGitHubCallback } from '../lib/github-auth'
import QRCode from 'react-qr-code'
import { useState, useEffect } from 'react'
import { login, register, sendOTP, verifyOTP, setTokens } from '../lib/api'
import { generateTOTP, verifyTOTPSetup, registerBiometric, verifyBiometric } from '../lib/mfa'

const API_URL = 'https://black-message-production.up.railway.app/api/v1/auth'

type Step = 'login' | 'register' | 'verify-email' | 'totp-setup' | 'usb' | 'done'

interface User {
  name: string
  email: string
  avatar: string
  company: string
  username?: string
}

const bg = '#1D1C1D'
const bgCard = '#2C2D30'
const bgInput = '#1D1C1D'
const border = '#4A154B'

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
    <p style={{ color:'#ABABAD', fontSize:13, marginTop:4 }}>Platform komunikasi enterprise</p>
  </div>
)

const inputStyle = {
  width:'100%', padding:'12px 16px', borderRadius:10,
  background:bgInput, border:'1px solid #4A154B',
  color:'#FFFFFF', fontSize:14, outline:'none', boxSizing:'border-box' as const
}

const btnPrimary = {
  width:'100%', padding:'13px', borderRadius:10,
  background:'#4A154B', color:'#FFFFFF',
  fontSize:15, fontWeight:700, border:'none', cursor:'pointer', marginTop:8
}

// ─── Login/Register ───────────────────────────────────────────────────────────
function AuthStep({ onNext }: { onNext: (user: User, step: Step) => void }) {
  const [tab, setTab] = useState<'login'|'register'>('login')
  const [username, setUsername] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    handleGitHubCallback((githubUser) => {
      const token = localStorage.getItem('bm_token')
      if (token) onNext(githubUser, 'done')
    })
  }, [])

  const handle = async () => {
    setError(''); setLoading(true)
    try {
      if (tab === 'register') {
        if (!username || !email || !pass || !confirm) {
          setError('Semua field wajib diisi!'); setLoading(false); return
        }
        if (pass !== confirm) {
          setError('Password tidak cocok!'); setLoading(false); return
        }
        const { ok, data } = await register({ username, email, password: pass, password_confirm: confirm })
        if (!ok) { setError(data.detail || JSON.stringify(data)); setLoading(false); return }
        localStorage.setItem('bm_token', data.access)
        localStorage.setItem('bm_refresh', data.refresh || '')
        if (data.workspace_id) localStorage.setItem('bm_workspace_id', data.workspace_id)
        const user = { name: data.user?.username || username, email, avatar: username[0].toUpperCase(), company: email.split('@')[1], username }
        // Kirim OTP verifikasi email
        await sendOTP(email, username)
        onNext(user, 'verify-email')
      } else {
        if (!email || !pass) { setError('Email dan password wajib diisi!'); setLoading(false); return }
        const { ok, data } = await login(email, pass)
        if (!ok) { setError(data.detail || 'Login gagal'); setLoading(false); return }
        localStorage.setItem('bm_token', data.access)
        localStorage.setItem('bm_refresh', data.refresh || '')
        if (data.workspace_id) localStorage.setItem('bm_workspace_id', data.workspace_id)
        const user = { name: data.user?.username || username, email: data.user?.email || '', avatar: username[0].toUpperCase(), company: '', username }
        onNext(user, 'done')
      }
    } catch(e) {
      setError('Terjadi kesalahan. Coba lagi.')
    }
    setLoading(false)
  }

  return (
    <div style={{ background:bgCard, borderRadius:16, padding:28, border:'1px solid #333' }}>
      <div style={{ display:'flex', marginBottom:20, background:'#1D1C1D', borderRadius:10, padding:4 }}>
        {(['login','register'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex:1, padding:'10px', borderRadius:8, border:'none', cursor:'pointer', fontWeight:600, fontSize:14,
            background: tab===t ? '#4A154B' : 'transparent',
            color: tab===t ? '#fff' : '#ABABAD',
          }}>{t === 'login' ? 'Masuk' : 'Daftar'}</button>
        ))}
      </div>

      <div style={{ display:'flex', gap:8, marginBottom:16 }}>
        <button onClick={loginWithGitHub} style={{ flex:1, padding:'10px', borderRadius:10, background:'#24292e', color:'#fff', border:'none', cursor:'pointer', fontWeight:600, fontSize:13, display:'flex', alignItems:'center', justifyContent:'center', gap:6 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>
          GitHub
        </button>
        <button style={{ flex:1, padding:'10px', borderRadius:10, background:'#fff', border:'none', cursor:'pointer', fontWeight:600, fontSize:13, display:'flex', alignItems:'center', justifyContent:'center', gap:6, color:'#333' }}>
          <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
          Google
        </button>
      </div>

      <p style={{ color:'#ABABAD', fontSize:13, textAlign:'center', margin:'0 0 16px' }}>atau dengan email</p>

      {error && <div style={{ background:'#3d0000', border:'1px solid #ff4444', borderRadius:8, padding:'10px 14px', color:'#ff8888', fontSize:13, marginBottom:12 }}>{error}</div>}

      {tab === 'register' && (
        <input style={{...inputStyle, marginBottom:10}} placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      )}
      <input style={{...inputStyle, marginBottom:10}} placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input style={{...inputStyle, marginBottom:10}} type="password" placeholder="Password" value={pass} onChange={e => setPass(e.target.value)} />
      {tab === 'register' && (
        <input style={{...inputStyle, marginBottom:10}} type="password" placeholder="Konfirmasi Password" value={confirm} onChange={e => setConfirm(e.target.value)} />
      )}
      <button onClick={handle} disabled={loading} style={btnPrimary}>
        {loading ? 'Memproses...' : tab === 'login' ? 'Masuk' : 'Daftar'}
      </button>
      <p style={{ color:'#ABABAD', fontSize:11, textAlign:'center', marginTop:12, lineHeight:'1.6' }}>
        Dengan melanjutkan, kamu menyetujui <a href="/privacy-policy" style={{ color:'#7C3AED' }}>Kebijakan Privasi</a> dan <a href="/terms" style={{ color:'#7C3AED' }}>Syarat Penggunaan</a> kami. Data kamu dilindungi dengan enkripsi E2EE dan standar keamanan PQC FIPS 203/204. BlackMess tidak menjual data pribadi kamu kepada pihak ketiga.
      </p>
    </div>
  )
}

// ─── Verify Email OTP ─────────────────────────────────────────────────────────
function VerifyEmailStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(true)

  const resend = async () => {
    setSent(false)
    await sendOTP(user.email, user.name)
    setSent(true)
  }

  const verify = async () => {
    setError(''); setLoading(true)
    const { ok, data } = await verifyOTP(user.email, code)
    if (ok) { onNext() }
    else { setError(data.error || 'Kode salah.') }
    setLoading(false)
  }

  return (
    <div style={{ background:bgCard, borderRadius:16, padding:28, border:'1px solid #333', textAlign:'center' }}>
      <div style={{ fontSize:48, marginBottom:12 }}>📧</div>
      <h2 style={{ color:'#fff', marginBottom:8 }}>Verifikasi Email</h2>
      <p style={{ color:'#ABABAD', fontSize:14, marginBottom:24 }}>Kode OTP dikirim ke <strong style={{color:'#c4b5fd'}}>{user.email}</strong></p>
      {error && <div style={{ background:'#3d0000', border:'1px solid #ff4444', borderRadius:8, padding:'10px 14px', color:'#ff8888', fontSize:13, marginBottom:12 }}>{error}</div>}
      <input style={{...inputStyle, marginBottom:12, textAlign:'center', fontSize:24, letterSpacing:8}} placeholder="000000" maxLength={6} value={code} onChange={e => setCode(e.target.value.replace(/\D/g,''))} />
      <button onClick={verify} disabled={loading} style={btnPrimary}>{loading ? 'Memverifikasi...' : 'Verifikasi'}</button>
      <button onClick={resend} style={{ background:'none', border:'none', color:'#a78bda', cursor:'pointer', fontSize:13, marginTop:12 }}>Kirim ulang kode</button>
    </div>
  )
}

// ─── TOTP Setup ───────────────────────────────────────────────────────────────
function TOTPSetupStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [qrUri, setQrUri] = useState('')
  const [secret, setSecret] = useState('')
  const [code, setCode] = useState('')
  const [step, setStep] = useState<'qr'|'verify'>('qr')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    generateTOTP().then(data => {
      setQrUri(data.totp_uri || '')
      setSecret(data.secret || '')
    })
  }, [])

  const verify = async () => {
    setError(''); setLoading(true)
    const { ok, data } = await verifyTOTPSetup(code)
    if (ok) { onNext() }
    else { setError(data.error || data.detail || 'Kode salah.') }
    setLoading(false)
  }

  return (
    <div style={{ background:bgCard, borderRadius:16, padding:28, border:'1px solid #333', textAlign:'center' }}>
      <div style={{ fontSize:48, marginBottom:12 }}>🔐</div>
      <h2 style={{ color:'#fff', marginBottom:8 }}>Setup Google Authenticator</h2>
      {step === 'qr' ? (
        <>
          <p style={{ color:'#ABABAD', fontSize:13, marginBottom:20 }}>Scan QR code ini dengan Google Authenticator</p>
          {qrUri && <div style={{ background:'#fff', padding:16, borderRadius:12, display:'inline-block', marginBottom:16 }}><QRCode value={qrUri} size={160} /></div>}
          {secret && <p style={{ color:'#6b7280', fontSize:11, marginBottom:20 }}>Manual: <code style={{color:'#c4b5fd'}}>{secret}</code></p>}
          <button onClick={() => setStep('verify')} style={btnPrimary}>Sudah Scan → Verifikasi</button>
        </>
      ) : (
        <>
          <p style={{ color:'#ABABAD', fontSize:13, marginBottom:20 }}>Masukkan kode 6 digit dari Google Authenticator</p>
          {error && <div style={{ background:'#3d0000', border:'1px solid #ff4444', borderRadius:8, padding:'10px 14px', color:'#ff8888', fontSize:13, marginBottom:12 }}>{error}</div>}
          <input style={{...inputStyle, marginBottom:12, textAlign:'center', fontSize:24, letterSpacing:8}} placeholder="000000" maxLength={6} value={code} onChange={e => setCode(e.target.value.replace(/\D/g,''))} />
          <button onClick={verify} disabled={loading} style={btnPrimary}>{loading ? 'Memverifikasi...' : 'Verifikasi'}</button>
          <button onClick={() => setStep('qr')} style={{ background:'none', border:'none', color:'#a78bda', cursor:'pointer', fontSize:13, marginTop:12 }}>← Kembali</button>
        </>
      )}
    </div>
  )
}

// ─── Biometric / USB Setup ────────────────────────────────────────────────────
function BiometricStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const register = async () => {
    setError(''); setLoading(true); setStatus('Menunggu verifikasi biometrik...')
    const result = await registerBiometric(`${user.name} - ${navigator.platform}`)
    if (result.ok) {
      setStatus('✅ ' + result.message)
      setDone(true)
    } else {
      setError(result.message)
      setStatus('')
    }
    setLoading(false)
  }

  return (
    <div style={{ background:bgCard, borderRadius:16, padding:28, border:'1px solid #333', textAlign:'center' }}>
      <div style={{ fontSize:48, marginBottom:12 }}>🔑</div>
      <h2 style={{ color:'#fff', marginBottom:8 }}>Daftarkan Biometrik</h2>
      <p style={{ color:'#ABABAD', fontSize:13, marginBottom:24 }}>Face ID, sidik jari, atau hardware key untuk keamanan ekstra</p>
      {error && <div style={{ background:'#3d0000', border:'1px solid #ff4444', borderRadius:8, padding:'10px 14px', color:'#ff8888', fontSize:13, marginBottom:12 }}>{error}</div>}
      {status && <p style={{ color:'#a78bda', fontSize:13, marginBottom:12 }}>{status}</p>}
      {!done ? (
        <>
          <button onClick={register} disabled={loading} style={btnPrimary}>
            {loading ? 'Menunggu...' : '🔏 Daftarkan Biometrik'}
          </button>
          <button onClick={onNext} style={{ background:'none', border:'none', color:'#6b7280', cursor:'pointer', fontSize:13, marginTop:12, display:'block', width:'100%' }}>
            Lewati untuk sekarang →
          </button>
        </>
      ) : (
        <button onClick={onNext} style={btnPrimary}>Lanjut →</button>
      )}
    </div>
  )
}

// ─── Main AuthFlow ────────────────────────────────────────────────────────────
export function AuthFlow({ onComplete }: { onComplete: (user: User) => void }) {
  const [step, setStep] = useState<Step>('login')
  const [user, setUser] = useState<User | null>(null)

  const handleAuth = (u: User, nextStep: Step) => {
    setUser(u)
    setStep(nextStep)
  }

  if (step === 'done' && user) {
    onComplete(user)
    return null
  }

  return (
    <div style={{ minHeight:'100vh', background:bg, display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
      <div style={{ width:'100%', maxWidth:420 }}>
        <Logo />
        {step === 'login' && <AuthStep onNext={handleAuth} />}
        {step === 'verify-email' && user && <VerifyEmailStep user={user} onNext={() => setStep('totp-setup')} />}
        {step === 'totp-setup' && user && <TOTPSetupStep user={user} onNext={() => setStep('usb')} />}
        {step === 'usb' && user && <BiometricStep user={user} onNext={() => { setStep('done'); onComplete(user!) }} />}
      </div>
    </div>
  )
}
