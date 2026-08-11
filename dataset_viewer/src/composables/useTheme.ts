import { ref } from 'vue'

const STORAGE_KEY = 'lipogrid-theme'
const mq = window.matchMedia('(prefers-color-scheme: dark)')

function getSystemIsDark(): boolean {
  return mq.matches
}

const stored = localStorage.getItem(STORAGE_KEY)
export const isDark = ref(stored ? stored === 'dark' : getSystemIsDark())

function applyTheme(dark: boolean) {
  const html = document.documentElement
  html.classList.add('theme-transitioning')
  html.setAttribute('data-theme', dark ? 'dark' : 'light')
  setTimeout(() => html.classList.remove('theme-transitioning'), 250)
}

// Follow system changes when user hasn't explicitly chosen
mq.addEventListener('change', (e) => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    isDark.value = e.matches
    applyTheme(e.matches)
  }
})

export function useTheme() {
  function toggle() {
    isDark.value = !isDark.value
    localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
    applyTheme(isDark.value)
  }

  return { isDark, toggle }
}
