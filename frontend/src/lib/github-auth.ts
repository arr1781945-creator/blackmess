const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID

export function loginWithGitHub() {
  const redirectUri = encodeURIComponent(window.location.origin)
  const scope = encodeURIComponent('user:email')
  window.location.href = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`
}

export async function handleGitHubCallback() {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  if (!code) return null

  // Simpan code - backend yang proses
  localStorage.setItem('bm_github_code', code)
  
  // Ambil user info dari GitHub API
  try {
    const res = await fetch(`https://api.github.com/user`, {
      headers: { 'Authorization': `token ${code}` }
    })
    const data = await res.json()
    return {
      name: data.name || data.login,
      email: data.email || `${data.login}@github.com`,
      avatar: data.login[0].toUpperCase(),
      company: 'github.com'
    }
  } catch(e) {
    return null
  }
}
