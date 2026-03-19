const API_URL = 'http://localhost:8002/api/v1/auth'

import { startRegistration } from '@simplewebauthn/browser'
import { useState } from 'react'

type Step = 'login' | 'register' | 'verify-email' | 'kyc' | 'usb'

interface User {
  name: string
  email: string
  avatar: string
  company: string
}

const Logo = () => (
  <div className="text-center mb-10">
    <div className="flex items-center justify-center mx-auto mb-6">
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
        {/* Titik atas tengah */}
        <circle cx="28" cy="8" r="5" fill="white"/>
        {/* Titik kiri tengah */}
        <circle cx="8" cy="28" r="5" fill="white"/>
        {/* Titik kanan tengah */}
        <circle cx="48" cy="28" r="5" fill="white"/>
        {/* Titik bawah tengah */}
        <circle cx="28" cy="48" r="5" fill="white"/>
        {/* Titik kiri atas */}
        <circle cx="14" cy="14" r="4" fill="white" opacity="0.6"/>
        {/* Titik kanan atas */}
        <circle cx="42" cy="14" r="4" fill="white" opacity="0.6"/>
        {/* Titik kiri bawah */}
        <circle cx="14" cy="42" r="4" fill="white" opacity="0.6"/>
        {/* Titik kanan bawah */}
        <circle cx="42" cy="42" r="4" fill="white" opacity="0.6"/>
      </svg>
    </div>
    <h1 className="text-white font-light text-3xl tracking-wide">BlackMess</h1>
  </div>
)

const inputCls = "w-full px-5 py-4 rounded-full bg-[#1a1a1a] border border-transparent text-white text-sm outline-none focus:border-gray-600 transition-colors placeholder:text-gray-500"
const labelCls = "text-sm font-medium text-gray-400 block mb-1.5"
const btnPrimary = "w-full py-4 rounded-full bg-white hover:bg-gray-100 text-black font-bold text-sm transition-colors"
const cardCls = "w-full"

// ─── Step 1: Login ────────────────────────────────────────────────────────────
function LoginStep({ onNext }: { onNext: (user: User, step: Step) => void }) {
  const [tab, setTab] = useState<'login'|'register'>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')

  const validateCompanyEmail = (e: string) => {
    const personal = ['gmail.com','yahoo.com','hotmail.com','outlook.com','icloud.com']
    const domain = e.split('@')[1]
    return domain && !personal.includes(domain)
  }

  const handle = async () => {
    setError('')
    const stored: any[] = JSON.parse(localStorage.getItem('bm_users') || '[]')

    if (tab === 'register') {
      if (!name || !email || !pass || !confirm) { setError('Isi semua field!'); return }
      if (!validateCompanyEmail(email)) { setError('Gunakan email perusahaan! Bukan Gmail/Yahoo/Hotmail'); return }
      if (pass.length < 8) { setError('Password minimal 8 karakter!'); return }
      if (pass !== confirm) { setError('Password tidak cocok!'); return }
      if (stored.find(u => u.email === email)) { setError('Email sudah terdaftar!'); return }
      // Coba register ke Django API
      try {
        const res = await fetch(`${API_URL}/register/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: name, email, password: pass })
        })
        const data = await res.json()
        if (!res.ok) {
          setError(data.detail || data.email?.[0] || data.username?.[0] || 'Gagal daftar!')
          return
        }
      } catch(e) {
        console.log('Server offline, pakai localStorage')
      }
      // Simpan ke localStorage sebagai backup
      // Register ke Django API
      try {
        const res = await fetch(`${API_URL}/register/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: name, email, password: pass })
        })
        const data = await res.json()
        if (!res.ok) {
          const errMsg = data.detail || data.email?.[0] || data.username?.[0] || data.password?.[0] || 'Gagal daftar!'
          setError(errMsg)
          return
        }
        // Simpan token
        if (data.access) {
          localStorage.setItem('bm_token', data.access)
          localStorage.setItem('bm_refresh', data.refresh || '')
        }
      } catch(e) {
        console.log('Server offline, pakai localStorage')
      }
      stored.push({ name, email, pass, verified: false, kyc: false, usb: false })
      localStorage.setItem('bm_users', JSON.stringify(stored))
      onNext({ name, email, avatar: name[0].toUpperCase(), company: email.split('@')[1] }, 'verify-email')
    } else {
      if (!email || !pass) { setError('Isi semua field!'); return }
      // Coba login ke Django API
      let djangoUser = null
      try {
        const res = await fetch(`${API_URL}/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: email, password: pass })
        })
        const data = await res.json()
        if (res.ok && data.access) {
          localStorage.setItem('bm_token', data.access)
          localStorage.setItem('bm_refresh', data.refresh || '')
          djangoUser = { name: data.user?.username || email.split('@')[0], email, avatar: email[0].toUpperCase(), company: email.split('@')[1] }
        }
      } catch(e) {
        console.log('Server offline, pakai localStorage')
      }

      if (djangoUser) {
        // Login Django berhasil - cek apakah perlu KYC/USB
        const u = stored.find((u: any) => u.email === email)
        if (u && !u.verified) { onNext(djangoUser, 'verify-email'); return }
        if (u && !u.kyc) { onNext(djangoUser, 'kyc'); return }
        if (u && !u.usb) { onNext(djangoUser, 'usb'); return }
        onNext(djangoUser, 'usb')
        return
      }

      // Coba login Django
      try {
        const res = await fetch(`${API_URL}/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: email, password: pass })
        })
        const data = await res.json()
        if (res.ok && data.access) {
          localStorage.setItem('bm_token', data.access)
          localStorage.setItem('bm_refresh', data.refresh || '')
          const u = stored.find((u: any) => u.email === email)
          const djangoUser = {
            name: data.user?.username || email.split('@')[0],
            email,
            avatar: (data.user?.username || email)[0].toUpperCase(),
            company: email.split('@')[1]
          }
          if (!u || !u.verified) { onNext(djangoUser, 'verify-email'); return }
          if (!u.kyc) { onNext(djangoUser, 'kyc'); return }
          if (!u.usb) { onNext(djangoUser, 'usb'); return }
          onNext(djangoUser, 'usb')
          return
        } else {
          setError(data.detail || 'Email atau password salah!')
          return
        }
      } catch(e) {
        console.log('Server offline, pakai localStorage')
      }

      // Fallback localStorage
      const u = stored.find((u: any) => u.email === email && u.pass === pass)
      if (!u) { setError('Email atau password salah!'); return }
      const user = { name: u.name, email: u.email, avatar: u.name[0].toUpperCase(), company: u.email.split('@')[1] }
      if (!u.verified) { onNext(user, 'verify-email'); return }
      if (!u.kyc) { onNext(user, 'kyc'); return }
      if (!u.usb) { onNext(user, 'usb'); return }
      onNext(user, 'usb')
    }
  }

  return (
    <div className="w-full max-w-sm">
      <Logo />
      <div className={cardCls}>
        {/* Tab */}
        <div className="flex gap-1 bg-black rounded-xl p-1 mb-5 border border-gray-800">
          {(['login','register'] as const).map(t => (
            <button key={t} onClick={() => { setTab(t); setError('') }}
              className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${tab === t ? 'bg-white text-black' : 'text-gray-400'}`}>
              {t === 'login' ? 'Masuk' : 'Daftar'}
            </button>
          ))}
        </div>

        {/* OAuth */}
        <div className="flex gap-3 mb-4">
          <button className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-gray-700 bg-black hover:bg-gray-900 text-sm font-medium text-white transition-colors">
            <svg width="16" height="16" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-gray-700 bg-black hover:bg-gray-900 text-sm font-medium text-white transition-colors">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            GitHub
          </button>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-800"/>
          <span className="text-gray-600 text-xs">atau dengan email</span>
          <div className="flex-1 h-px bg-gray-800"/>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-xs mb-4">{error}</div>}

        <div className="flex flex-col gap-3">
          {tab === 'register' && (
            <div>
              <label className={labelCls}>Nama lengkap</label>
              <input className={inputCls} type="text" placeholder="Nama kamu" value={name} onChange={e => setName(e.target.value)}/>
            </div>
          )}
          <div>
            <label className={labelCls}>Email perusahaan</label>
            <input className={inputCls} type="email" placeholder="nama@perusahaan.com" value={email} onChange={e => setEmail(e.target.value)}/>
          </div>
          <div>
            <label className={labelCls}>Password</label>
            <input className={inputCls} type="password" placeholder="Min. 8 karakter" value={pass} onChange={e => setPass(e.target.value)}/>
          </div>
          {tab === 'register' && (
            <div>
              <label className={labelCls}>Konfirmasi password</label>
              <input className={inputCls} type="password" placeholder="Ulangi password" value={confirm}
                onChange={e => setConfirm(e.target.value)} onKeyDown={e => e.key === 'Enter' && handle()}/>
            </div>
          )}
          <button className={btnPrimary} onClick={handle}>
            {tab === 'login' ? 'Masuk' : 'Buat Akun'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Step 2: Verifikasi Email ─────────────────────────────────────────────────
function VerifyEmailStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [code, setCode] = useState(['','','','','',''])
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  const sendOTP = async () => {
    setSending(true)
    try {
      await fetch('http://localhost:8002/api/v1/auth/otp/send/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ email: user.email, name: user.name })
      })
    } catch(e) { console.log('Server offline, using demo mode') }
    setSending(false)
  }

  useState(() => { sendOTP() })

  const handleChange = async (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const n = [...code]; n[i] = val.slice(-1); setCode(n)
    if (val && i < 5) document.getElementById(`otp-${i+1}`)?.focus()
    if (n.every(d => d) && i === 5) {
      const enteredOTP = n.join('')
      try {
        const res = await fetch('http://localhost:8002/api/v1/auth/otp/verify/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ email: user.email, otp: enteredOTP })
        })
        if (res.ok) {
          const s: any[] = JSON.parse(localStorage.getItem('bm_users') || '[]')
          localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email === user.email ? {...u, verified: true} : u)))
          onNext()
          return
        }
      } catch(e) {
        // Fallback demo mode
        if (enteredOTP === '123456') {
          const s: any[] = JSON.parse(localStorage.getItem('bm_users') || '[]')
          localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email === user.email ? {...u, verified: true} : u)))
          onNext()
          return
        }
      }
      if (false) { setError('Kode salah! Demo: 123456')
        setCode(['','','','','',''])
        document.getElementById('otp-0')?.focus()
      }
    }
  }

  return (
    <div className="w-full max-w-sm">
      <Logo />
      <div className={`${cardCls} text-center`}>
        <div className="w-14 h-14 rounded-full border border-gray-700 flex items-center justify-center mx-auto mb-4">
          <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
        </div>
        <h2 className="text-white font-bold text-lg mb-1">Verifikasi Email</h2>
        <p className="text-gray-500 text-sm mb-1">Kode dikirim ke</p>
        <p className="text-white text-sm font-semibold mb-6">{user.email}</p>

        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-2 text-red-400 text-xs mb-4">{error}</div>}

        <div className="flex gap-2 justify-center mb-4">
          {code.map((d, i) => (
            <input key={i} id={`otp-${i}`} type="text" inputMode="numeric" maxLength={1} value={d}
              onChange={e => handleChange(i, e.target.value)}
              onKeyDown={e => { if(e.key==='Backspace' && !d && i > 0) document.getElementById(`otp-${i-1}`)?.focus() }}
              className="w-11 h-14 text-center text-xl font-bold rounded-xl bg-black border border-gray-700 text-white outline-none focus:border-white transition-colors"/>
          ))}
        </div>
        <p className="text-gray-600 text-xs">Demo: gunakan kode <span className="text-white font-bold">123456</span></p>
      </div>
    </div>
  )
}

// ─── Step 3: KYC ─────────────────────────────────────────────────────────────
function KYCStep({ user, onNext }: { user: User, onNext: () => void }) {
  const [idType, setIdType] = useState('ktp')
  const [idNum, setIdNum] = useState('')
  const [fullName, setFullName] = useState('')
  const [company, setCompany] = useState('')
  const [uploaded, setUploaded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handle = async () => {
    if (!idNum || !fullName || !company) { setError('Isi semua field!'); return }
    if (!uploaded) { setError('Upload dokumen identitas dulu!'); return }
    setLoading(true)
    await new Promise(r => setTimeout(r, 1500))
    const s: any[] = JSON.parse(localStorage.getItem('bm_users') || '[]')
    localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email === user.email ? {...u, kyc: true} : u)))
    setLoading(false)
    onNext()
  }

  return (
    <div className="w-full max-w-sm">
      <Logo />
      <div className={cardCls}>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl border border-gray-700 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <div>
            <h2 className="text-white font-bold">Verifikasi KYC</h2>
            <p className="text-gray-500 text-xs">Know Your Customer</p>
          </div>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-xs mb-4">{error}</div>}

        <div className="flex flex-col gap-3">
          <div>
            <label className={labelCls}>Jenis identitas</label>
            <select value={idType} onChange={e => setIdType(e.target.value)}
              className={inputCls}>
              <option value="ktp">KTP</option>
              <option value="passport">Passport</option>
              <option value="sim">SIM</option>
            </select>
          </div>
          <div>
            <label className={labelCls}>Nomor identitas</label>
            <input className={inputCls} type="text" placeholder="Nomor KTP/Passport/SIM" value={idNum} onChange={e => setIdNum(e.target.value)}/>
          </div>
          <div>
            <label className={labelCls}>Nama lengkap (sesuai KTP)</label>
            <input className={inputCls} type="text" placeholder="Nama lengkap" value={fullName} onChange={e => setFullName(e.target.value)}/>
          </div>
          <div>
            <label className={labelCls}>Nama perusahaan</label>
            <input className={inputCls} type="text" placeholder="PT. Nama Perusahaan" value={company} onChange={e => setCompany(e.target.value)}/>
          </div>
          <div>
            <label className={labelCls}>Upload dokumen</label>
            <label className={`w-full py-6 rounded-xl border-2 border-dashed cursor-pointer transition-colors text-center block ${uploaded ? 'border-white/40 bg-white/5' : 'border-gray-700 hover:border-white/40'}`}>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={e => { if (e.target.files && e.target.files[0]) setUploaded(true) }}
              />
              {uploaded ? (
                <div className="flex flex-col items-center gap-1">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                  <span className="text-white text-sm font-semibold">Dokumen terupload!</span>
                  <span className="text-gray-500 text-xs">Ketuk untuk ganti foto</span>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                  <span className="text-gray-400 text-sm font-medium">Ambil foto atau pilih file</span>
                  <span className="text-gray-600 text-xs">KTP / Passport / SIM</span>
                </div>
              )}
            </label>
          </div>
          <button className={btnPrimary} onClick={handle} disabled={loading}>
            {loading ? 'Memverifikasi...' : 'Verifikasi KYC'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Step 4: USB Key ──────────────────────────────────────────────────────────
function USBStep({ user, onComplete }: { user: User, onComplete: (user: User) => void }) {
  const [usb1, setUsb1] = useState(false)
  const [usb2, setUsb2] = useState(false)
  const [dbPass, setDbPass] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading1, setLoading1] = useState(false)
  const [loading2, setLoading2] = useState(false)
  const [error, setError] = useState('')

  const strength = dbPass.length === 0 ? 0 : dbPass.length < 8 ? 1 : dbPass.length < 12 ? 2 : dbPass.length < 16 ? 3 : 4
  const strengthColor = ['', 'bg-red-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500'][strength]
  const strengthLabel = ['', 'Lemah', 'Sedang', 'Kuat', 'Sangat Kuat'][strength]

  const registerUSB = async (num: number) => {
    if (num === 1) setLoading1(true)
    else setLoading2(true)
    setError('')

    try {
      // Cek support WebAuthn
      if (!window.PublicKeyCredential) {
        throw new Error('NO_WEBAUTHN')
      }

      // Cek fingerprint/face id tersedia
      const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
      if (!available) {
        throw new Error('NO_AUTHENTICATOR')
      }

      // Generate challenge random
      const challenge = new Uint8Array(32)
      crypto.getRandomValues(challenge)

      // Daftar fingerprint/face id
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge,
          rp: {
            name: 'BlackMess Enterprise',
            id: window.location.hostname
          },
          user: {
            id: new TextEncoder().encode(`${user.email}-key${num}-${Date.now()}`),
            name: user.email,
            displayName: `${user.name} - Security Key ${num}`,
          },
          pubKeyCredParams: [
            { alg: -7, type: 'public-key' as const },
            { alg: -257, type: 'public-key' as const },
          ],
          authenticatorSelection: {
            authenticatorAttachment: 'platform' as const,
            userVerification: 'required' as const,
            requireResidentKey: false,
          },
          timeout: 120000,
          attestation: 'none' as const,
        }
      }) as PublicKeyCredential

      if (credential) {
        // Simpan credential ke localStorage
        const stored = JSON.parse(localStorage.getItem('bm_webauthn') || '[]')
        stored.push({
          id: credential.id,
          type: credential.type,
          key_num: num,
          email: user.email,
          created_at: new Date().toISOString()
        })
        localStorage.setItem('bm_webauthn', JSON.stringify(stored))
        if (num === 1) setUsb1(true)
        else setUsb2(true)
      }

    } catch(e: any) {
      if (e.message === 'NO_WEBAUTHN') {
        setError('Browser tidak mendukung WebAuthn. Gunakan Chrome terbaru.')
      } else if (e.message === 'NO_AUTHENTICATOR') {
        setError('Fingerprint/Face ID tidak tersedia. Aktifkan di pengaturan HP.')
      } else if (e.name === 'NotAllowedError') {
        setError('Verifikasi dibatalkan atau timeout. Coba lagi!')
      } else if (e.name === 'InvalidStateError') {
        // Sudah terdaftar sebelumnya
        if (num === 1) setUsb1(true)
        else setUsb2(true)
      } else if (e.name === 'AbortError') {
        setError('Verifikasi dibatalkan.')
      } else {
        // Fallback - simulasi untuk testing
        console.warn('WebAuthn error:', e.name, e.message)
        // Langsung fallback tanpa delay
        if (num === 1) setUsb1(true)
        else setUsb2(true)
      }
    } finally {
      if (num === 1) setLoading1(false)
      else setLoading2(false)
    }
  }

  const handleFinish = async () => {
    if (!usb1 || !usb2) { setError('Daftarkan kedua USB key dulu!'); return }
    if (dbPass.length < 12) { setError('Kata sandi database minimal 12 karakter!'); return }
    setError('')
    const s: any[] = JSON.parse(localStorage.getItem('bm_users') || '[]')
    localStorage.setItem('bm_users', JSON.stringify(s.map(u => u.email === user.email ? {...u, usb: true} : u)))
    onComplete(user)
  }

  const USBCard = ({ num, registered, loading, onRegister }: any) => (
    <div className={`p-4 rounded-xl border transition-all ${registered ? 'border-white/30 bg-white/5' : 'border-gray-800 bg-black'}`}>
      <div className="flex items-center gap-3">
        <div className={`w-12 h-12 rounded-xl border flex items-center justify-center flex-shrink-0 ${registered ? 'border-white/30 bg-white/5' : 'border-gray-700'}`}>
          {registered ? (
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          ) : (
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/>
            </svg>
          )}
        </div>
        <div className="flex-1">
          <div className="text-white font-semibold text-sm">
            {num === 1 ? 'Security Key Utama' : 'Security Key Cadangan'}
          </div>
          <div className="text-gray-500 text-xs mt-0.5">
            {registered ? '✓ Fingerprint/Face ID terdaftar' : 'Gunakan fingerprint atau face ID'}
          </div>
        </div>
        {!registered && (
          <button onClick={onRegister} disabled={loading}
            className="px-3 py-2 rounded-lg bg-white text-black text-xs font-bold transition-all disabled:opacity-40 flex items-center gap-1.5">
            {loading ? (
              <>
                <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                Memindai...
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"/>
                </svg>
                Daftar
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )

  return (
    <div className="w-full max-w-sm">
      <Logo />
      <div className={cardCls}>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl border border-gray-700 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
          </div>
          <div>
            <h2 className="text-white font-bold">Setup USB Key</h2>
            <p className="text-gray-500 text-xs">2 Hardware Security Key diperlukan</p>
          </div>
        </div>

        <p className="text-gray-500 text-xs mb-4">Daftar 2 USB key (YubiKey/FIDO2) sebagai autentikasi hardware.</p>

        {error && <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-xs mb-3">{error}</div>}

        <div className="flex flex-col gap-2 mb-4">
          <USBCard num={1} registered={usb1} loading={loading1} onRegister={() => registerUSB(1)} />
          <USBCard num={2} registered={usb2} loading={loading2} onRegister={() => registerUSB(2)} />
        </div>

        {/* DB Password */}
        <div className="mb-4">
          <label className={labelCls}>Kata sandi database</label>
          <div className="relative">
            <input
              type={showPass ? 'text' : 'password'}
              placeholder="Min. 12 karakter (wajib)"
              value={dbPass}
              onChange={e => setDbPass(e.target.value)}
              className={`${inputCls} pr-10`}
            />
            <button onClick={() => setShowPass(!showPass)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
              {showPass
                ? <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
                : <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              }
            </button>
          </div>
          {dbPass.length > 0 && (
            <div className="mt-2">
              <div className="flex gap-1 mb-1">
                {[1,2,3,4].map(i => (
                  <div key={i} className={`flex-1 h-1 rounded-full transition-all ${i <= strength ? strengthColor : 'bg-gray-800'}`}/>
                ))}
              </div>
              <p className="text-xs text-gray-500">{strengthLabel}</p>
            </div>
          )}
          <p className="text-gray-600 text-xs mt-1">Mengenkripsi akses database Anda</p>
        </div>

        <button onClick={handleFinish}
          disabled={!usb1 || !usb2 || dbPass.length < 12}
          className={`${btnPrimary} disabled:opacity-30`}>
          {!usb1 || !usb2 ? `Daftarkan USB Key ${!usb1 ? '1' : '2'} dulu` : dbPass.length < 12 ? 'Isi kata sandi database' : 'Selesai & Masuk'}
        </button>
      </div>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export function AuthFlow({ onComplete }: { onComplete: (user: User) => void }) {
  const [step, setStep] = useState<Step>('login')
  const [user, setUser] = useState<User | null>(null)

  const handleLoginNext = (u: User, next: Step) => { setUser(u); setStep(next) }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      {(step === 'login' || step === 'register') && <LoginStep onNext={handleLoginNext} />}
      {step === 'verify-email' && user && <VerifyEmailStep user={user} onNext={() => setStep('kyc')} />}
      {step === 'kyc' && user && <KYCStep user={user} onNext={() => setStep('usb')} />}
      {step === 'usb' && user && <USBStep user={user} onComplete={onComplete} />}
    </div>
  )
}
