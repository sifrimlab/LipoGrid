import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  base: '/LipoGrid/',
  plugins: [vue()],
  server: {
    // Allow the dev server to serve the repo-root LICENSE.md
    // imported by src/components/LicenseDialog.vue
    fs: { allow: ['..'] },
  },
})
