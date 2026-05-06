<template>
  <div class="upload-shell">
    <!-- Header -->
    <div class="upload-header">
      <div class="brand-row">
        <span class="brand-name">Lipo<span class="brand-bold">Grid</span></span>
        <span class="brand-tag">Pilot</span>
      </div>
      <p class="upload-subtitle">Load your datasets to begin exploration</p>
    </div>

    <!-- Drop zones -->
    <div class="zones-row">
      <!-- Lipidomic -->
      <DropZone
        label="Lipidomic"
        title="Gene KO Matrix"
        description="CSV with lipid_annotation_self column and {KO}_log2FC / {KO}_pvalue pairs"
        :icon="lipidIcon"
        :state="lipidState"
        :filename="lipidFilename"
        :error-message="lipidError"
        @file="onLipidFile"
      />

      <div class="zone-divider" aria-hidden="true">
        <span class="divider-line" />
        <span class="divider-plus">+</span>
        <span class="divider-line" />
      </div>

      <!-- Transcriptomic -->
      <DropZone
        label="Transcriptomic"
        title="Gene KO Matrix"
        description="CSV with gene name column and {KO}_log2FC / {KO}_pvalue pairs"
        :icon="geneIcon"
        :state="geneState"
        :filename="geneFilename"
        :error-message="geneError"
        @file="onGeneFile"
      />
    </div>

    <!-- Progress indicator -->
    <div class="progress-row" aria-live="polite">
      <div class="progress-dots">
        <span class="dot" :class="{ active: lipidState === 'valid', done: lipidState === 'valid' }" />
        <span class="dot-track" />
        <span class="dot" :class="{ active: geneState === 'valid', done: geneState === 'valid' }" />
      </div>
      <p class="progress-label">
        <template v-if="lipidState !== 'valid' && geneState !== 'valid'">Upload both files to continue</template>
        <template v-else-if="lipidState === 'valid' && geneState !== 'valid'">Lipidomic matrix ready — now upload the transcriptomic matrix</template>
        <template v-else-if="lipidState !== 'valid' && geneState === 'valid'">Transcriptomic matrix ready — now upload the lipidomic matrix</template>
        <template v-else>Both files validated — launching explorer…</template>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import * as d3 from 'd3'
import DropZone from './DropZone.vue'

type ZoneState = 'idle' | 'dragging' | 'valid' | 'error'

const emit = defineEmits<{
  ready: [lipidFile: File, geneFile: File]
}>()

const lipidState = ref<ZoneState>('idle')
const lipidFilename = ref('')
const lipidError = ref('')
const lipidFile = ref<File | null>(null)

const geneState = ref<ZoneState>('idle')
const geneFilename = ref('')
const geneError = ref('')
const geneFile = ref<File | null>(null)

function readCsvHeaders(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => {
      const text = e.target?.result as string
      try {
        const parsed = d3.csvParse(text.slice(0, 8192))
        resolve(parsed.columns)
      } catch {
        reject(new Error('Could not parse CSV'))
      }
    }
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsText(file.slice(0, 65536))
  })
}

function hasLog2FCColumns(cols: string[]): boolean {
  return cols.some(c => c.endsWith('_log2FC'))
}

async function onLipidFile(file: File) {
  lipidFilename.value = file.name
  lipidError.value = ''
  try {
    const cols = await readCsvHeaders(file)
    if (!cols.includes('lipid_annotation_self')) {
      lipidState.value = 'error'
      lipidError.value = 'Missing column: lipid_annotation_self'
      return
    }
    if (!hasLog2FCColumns(cols)) {
      lipidState.value = 'error'
      lipidError.value = 'No {KO}_log2FC columns found'
      return
    }
    lipidFile.value = file
    lipidState.value = 'valid'
  } catch (e) {
    lipidState.value = 'error'
    lipidError.value = String(e)
  }
}

async function onGeneFile(file: File) {
  geneFilename.value = file.name
  geneError.value = ''
  try {
    const cols = await readCsvHeaders(file)
    if (!hasLog2FCColumns(cols)) {
      geneState.value = 'error'
      geneError.value = 'No {KO}_log2FC columns found'
      return
    }
    if (cols.length < 2) {
      geneState.value = 'error'
      geneError.value = 'File appears to be empty or malformed'
      return
    }
    geneFile.value = file
    geneState.value = 'valid'
  } catch (e) {
    geneState.value = 'error'
    geneError.value = String(e)
  }
}

watch([lipidState, geneState], ([ls, gs]) => {
  if (ls === 'valid' && gs === 'valid' && lipidFile.value && geneFile.value) {
    setTimeout(() => emit('ready', lipidFile.value!, geneFile.value!), 520)
  }
})

const lipidIcon = `<svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <ellipse cx="14" cy="14" rx="10" ry="6" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
  <ellipse cx="14" cy="14" rx="6" ry="10" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="14" cy="7" r="2" fill="currentColor" opacity="0.7"/>
  <circle cx="14" cy="21" r="2" fill="currentColor" opacity="0.7"/>
  <circle cx="7" cy="14" r="1.5" fill="currentColor" opacity="0.4"/>
  <circle cx="21" cy="14" r="1.5" fill="currentColor" opacity="0.4"/>
</svg>`

const geneIcon = `<svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 4 C8 4 8 12 14 14 C20 16 20 24 20 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  <path d="M20 4 C20 4 20 12 14 14 C8 16 8 24 8 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="9.5" y1="8" x2="18.5" y2="10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.6"/>
  <line x1="9" y1="18" x2="19" y2="18" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.6"/>
  <line x1="10" y1="13" x2="18" y2="13" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.9"/>
</svg>`
</script>

<style scoped>
.upload-shell {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 20px 48px;
  gap: 40px;
}

/* Header */
.upload-header {
  text-align: center;
}
.brand-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 10px;
}
.brand-name {
  font-size: 1.6rem;
  font-weight: 400;
  letter-spacing: -0.04em;
  color: var(--text-1);
}
.brand-bold { font-weight: 700; }
.brand-tag {
  font-size: 0.65rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  background: var(--accent-muted);
  padding: 2px 7px;
  border-radius: 3px;
}
.upload-subtitle {
  font-size: 0.88rem;
  color: var(--text-3);
  letter-spacing: 0.01em;
}

/* Zone layout */
.zones-row {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 0;
  width: 100%;
  max-width: 860px;
}

.zone-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  gap: 8px;
  flex-shrink: 0;
}
.divider-line {
  flex: 1;
  width: 1px;
  background: var(--border);
  max-height: 60px;
}
.divider-plus {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-3);
  letter-spacing: 0.05em;
}

/* Progress */
.progress-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.progress-dots {
  display: flex;
  align-items: center;
  gap: 0;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--border-strong);
  background: var(--surface);
  transition: border-color 0.3s ease, background 0.3s ease;
}
.dot.done {
  border-color: var(--success);
  background: var(--success);
}
.dot-track {
  width: 56px;
  height: 2px;
  background: var(--border);
  margin: 0 4px;
}
.progress-label {
  font-size: 0.8rem;
  color: var(--text-3);
  text-align: center;
}

/* Mobile: stack vertically */
@media (max-width: 640px) {
  .zones-row {
    flex-direction: column;
    max-width: 420px;
  }
  .zone-divider {
    flex-direction: row;
    padding: 12px 0;
  }
  .divider-line {
    flex: 1;
    width: auto;
    height: 1px;
    max-height: none;
    max-width: 80px;
  }
}
</style>
