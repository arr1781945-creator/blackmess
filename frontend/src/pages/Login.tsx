import { useState } from 'react'

export default function Login({ onLogin, onRegister }: { onLogin: (token: string) => void, onRegister: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch('http://localhost:8002/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      if (data.access) onLogin(data.access)
      else setError(data.detail || 'Invalid credentials')
    } catch { setError('Server tidak bisa dihubungi') }
    setLoading(false)
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#000000',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>


      <div style={{ width: '100%', maxWidth: 400, margin: '0 16px', position: 'relative', zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 60, height: 60, borderRadius: 16, margin: '0 auto 16px',
            background: '#ffffff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 32px rgba(255,255,255,0.15)'
          }}>
            <div dangerouslySetInnerHTML={{__html: `<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Outer glow ring -->
  <ellipse cx="16" cy="16" rx="15" ry="6" stroke="url(#ring1)" stroke-width="1.5" opacity="0.4"/>
  <!-- Middle ring -->
  <ellipse cx="16" cy="16" rx="12" ry="4.5" stroke="url(#ring2)" stroke-width="2" opacity="0.7"/>
  <!-- Inner bright ring -->
  <ellipse cx="16" cy="16" rx="9" ry="3" stroke="url(#ring3)" stroke-width="2.5" opacity="0.9"/>
  <!-- Black hole center -->
  <circle cx="16" cy="16" r="6" fill="black"/>
  <!-- Accretion disk glow -->
  <ellipse cx="16" cy="16" rx="8" ry="2" fill="url(#disk)" opacity="0.6"/>
  <!-- Core dark circle -->
  <circle cx="16" cy="16" r="5" fill="#050508"/>
  <!-- Photon ring -->
  <ellipse cx="16" cy="16" rx="6" ry="1.5" stroke="#fff" stroke-width="0.5" opacity="0.3"/>

  <defs>
    <linearGradient id="ring1" x1="0" y1="0" x2="32" y2="0">
      <stop offset="0%" stop-color="#f97316"/>
      <stop offset="50%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#f97316"/>
    </linearGradient>
    <linearGradient id="ring2" x1="0" y1="0" x2="32" y2="0">
      <stop offset="0%" stop-color="#fb923c"/>
      <stop offset="40%" stop-color="#fde68a"/>
      <stop offset="60%" stop-color="#fde68a"/>
      <stop offset="100%" stop-color="#fb923c"/>
    </linearGradient>
    <linearGradient id="ring3" x1="0" y1="0" x2="32" y2="0">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="30%" stop-color="#fff7ed"/>
      <stop offset="70%" stop-color="#fff7ed"/>
      <stop offset="100%" stop-color="#f59e0b"/>
    </linearGradient>
    <radialGradient id="disk" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="#f97316" stop-opacity="0"/>
    </radialGradient>
  </defs>
</svg>`}} style={{width:32,height:32}}/>
          </div>
          <h1 style={{ color: 'white', fontSize: 24, fontWeight: 700, margin: '0 0 4px', letterSpacing: -0.5 }}>BlackMess</h1>
          <p style={{ color: '#888888', fontSize: 14, margin: 0 }}>Enterprise Remote Work Platform</p>
        </div>

        {/* Card */}
        <div style={{
          background: '#111111', backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.08)', borderRadius: 20,
          padding: '32px', boxShadow: '0 25px 50px rgba(0,0,0,0.5)'
        }}>
          {/* Social Login */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
            <button style={{
              flex: 1, padding: '11px', borderRadius: 10, border: '1px solid #d0d0d0',
              background: '#ffffff', color: '#000000', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              fontFamily: 'inherit'
            }}
            onMouseOver={e => (e.currentTarget.style.background='#e6e6e6')}
            onMouseOut={e => (e.currentTarget.style.background='#ffffff')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Google
            </button>

            <button style={{
              flex: 1, padding: '11px', borderRadius: 10, border: '1px solid #d0d0d0',
              background: '#ffffff', color: '#000000', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              fontFamily: 'inherit'
            }}
            onMouseOver={e => (e.currentTarget.style.background='#e6e6e6')}
            onMouseOut={e => (e.currentTarget.style.background='#ffffff')}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              GitHub
            </button>
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }}/>
            <span style={{ color: '#666', fontSize: 12 }}>atau masuk dengan email</span>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }}/>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 10, padding: '12px 16px', color: '#f87171',
              fontSize: 13, marginBottom: 16
            }}>{error}</div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', color: '#ffffff', fontSize: 11, fontWeight: 600, letterSpacing: 0.5, textTransform: 'none', marginBottom: 6 }}>Email</label>
              <input
                type="text" value={username}
                onChange={e => setUsername(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                placeholder="your-username"
                style={{
                  width: '100%', padding: '12px 16px', borderRadius: 10,
                  background: '#1a1a1a', border: '1px solid #d0d0d0',
                  color: 'white', fontSize: 14, outline: 'none', boxSizing: 'border-box',
                  fontFamily: 'inherit'
                }}
                onFocus={e => e.target.style.borderColor = '#6366f1'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            </div>

            <div>
              <label style={{ display: 'block', color: '#ffffff', fontSize: 11, fontWeight: 600, letterSpacing: 0.5, textTransform: 'none', marginBottom: 6 }}>Kata sandi</label>
              <input
                type="password" value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                placeholder="••••••••••••"
                style={{
                  width: '100%', padding: '12px 16px', borderRadius: 10,
                  background: '#1a1a1a', border: '1px solid #d0d0d0',
                  color: 'white', fontSize: 14, outline: 'none', boxSizing: 'border-box',
                  fontFamily: 'inherit'
                }}
                onFocus={e => e.target.style.borderColor = '#6366f1'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            </div>

            <button
              onClick={handleLogin} disabled={loading}
              style={{
                width: '100%', padding: '13px', borderRadius: 10, border: 'none',
                background: loading ? 'rgba(255,255,255,0.5)' : '#ffffff',
                color: '#000000', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer',
                marginTop: 4, fontFamily: 'inherit', transition: 'opacity 0.2s'
              }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            <p style={{ textAlign: 'center', marginTop: 16, color: '#475569', fontSize: 13 }}>
              Belum punya akun?{' '}
              <span
                onClick={onRegister}
                style={{ color: '#ffffff', cursor: 'pointer', fontWeight: 600 }}
              >
                Daftar di sini yuk
              </span>
            </p>
          </div>


        </div>
      </div>
    </div>
  )
}
