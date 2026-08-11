<template>
  <Teleport to="body">
    <div class="license-overlay">
      <div
        ref="panelRef"
        class="license-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="license-dialog-title"
      >
        <header class="license-header">
          <h2 id="license-dialog-title" class="license-title">License Agreement</h2>
          <button
            class="license-close"
            @click="emit('close')"
            aria-label="Close license agreement"
            title="Close"
          >
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <line x1="6" y1="6" x2="18" y2="18"/>
              <line x1="18" y1="6" x2="6" y2="18"/>
            </svg>
          </button>
        </header>
        <div class="license-body">
          <p v-for="(p, i) in paragraphs" :key="i" class="license-paragraph">{{ p }}</p>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import licenseText from '../../../LICENSE.md?raw'
import { onClickOutside } from '../composables/onClickOutside'

const emit = defineEmits<{ close: [] }>()

// Dismiss on outside click
const panelRef = ref<HTMLElement | null>(null)
onClickOutside(panelRef, () => emit('close'))

// Dismiss on Escape
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

// Verbatim LICENSE.md content, split into paragraphs on blank lines
const paragraphs = licenseText.trim().split(/\n\s*\n/)
</script>

<style scoped>
.license-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(10, 10, 16, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: licenseFadeIn 0.15s ease;
}
@keyframes licenseFadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Fixed-size panel; only the body scrolls */
.license-panel {
  width: 640px;
  max-width: calc(100vw - 32px);
  height: 70vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.license-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 18px;
  border-bottom: 1px solid var(--border);
}
.license-title {
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text-1);
}
.license-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-3);
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
  flex-shrink: 0;
}
.license-close:hover { background: var(--accent-muted); color: var(--accent); }
.license-close:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.license-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px 22px 22px;
}
.license-paragraph {
  font-size: 0.85rem;
  line-height: 1.65;
  color: var(--text-2);
  white-space: pre-line; /* preserve line breaks (e.g. bullet lists) from LICENSE.md */
}
.license-paragraph + .license-paragraph { margin-top: 12px; }
.license-paragraph:first-child {
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--text-1);
}
</style>
