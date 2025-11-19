import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'url' // Dùng cách mới

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Đây là cách "lách" không cần __dirname
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})