import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Load saved theme
const savedTheme = localStorage.getItem('bm_theme') || 'dark'
const root = document.documentElement
if (savedTheme === 'light') {
  root.classList.add('light')
} else if (savedTheme === 'system') {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  if (!prefersDark) root.classList.add('light')
}


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    
      <App />
    
  </React.StrictMode>,
)
