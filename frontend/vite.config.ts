import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import crypto from 'crypto'

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'csp-nonce',
      transformIndexHtml(html) {
        const nonce = crypto.randomBytes(16).toString('base64')
        return html
          .replace(/VITE_NONCE_PLACEHOLDER/g, nonce)
          .replace(
            /<script/g,
            `<script nonce="${nonce}"`
          )
      }
    }
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
