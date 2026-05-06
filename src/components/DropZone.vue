<template>
  <div
    class="dropzone-wrapper"
    :class="{ dragging: isDragging }"
    role="region"
    :aria-label="`${label} file upload`"
  >
    <div class="zone-label-row">
      <span class="zone-chip">{{ label }}</span>
    </div>

    <h3 class="zone-title">{{ title }}</h3>
    <p class="zone-desc">{{ description }}</p>

    <!-- Drop area -->
    <div
      class="drop-area"
      :class="stateClass"
      @dragenter.prevent="onDragEnter"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
      @click="triggerInput"
      tabindex="0"
      role="button"
      :aria-label="state === 'valid' ? `${filename} uploaded successfully` : 'Click or drag file to upload'"
      @keydown.enter.space.prevent="triggerInput"
    >
      <!-- Idle / dragging -->
      <template v-if="state === 'idle' || state === 'dragging'">
        <div class="drop-icon" :class="{ pulse: state === 'dragging' }" v-html="icon" />
        <p class="drop-main-text">
          <span class="drop-link">Choose file</span>
          <span class="drop-or"> or drag &amp; drop</span>
        </p>
        <p class="drop-sub-text">CSV format</p>
      </template>

      <!-- Valid -->
      <template v-else-if="state === 'valid'">
        <div class="drop-status-icon valid-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8"/>
            <polyline points="7,12 10.5,15.5 17,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <p class="drop-filename">{{ filename }}</p>
        <p class="drop-valid-text">Format verified</p>
        <button class="replace-btn" @click.stop="triggerInput" tabindex="-1">Replace file</button>
      </template>

      <!-- Error -->
      <template v-else-if="state === 'error'">
        <div class="drop-status-icon error-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8"/>
            <line x1="12" y1="8" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <circle cx="12" cy="16.5" r="1.2" fill="currentColor"/>
          </svg>
        </div>
        <p class="drop-error-text">{{ errorMessage }}</p>
        <p class="drop-sub-text">Click to try a different file</p>
      </template>

      <input
        ref="inputRef"
        type="file"
        accept=".csv,text/csv"
        class="file-input"
        :aria-hidden="true"
        @change="onInputChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

type ZoneState = 'idle' | 'dragging' | 'valid' | 'error'

const props = defineProps<{
  label: string
  title: string
  description: string
  icon: string
  state: ZoneState
  filename?: string
  errorMessage?: string
}>()

const emit = defineEmits<{
  file: [file: File]
}>()

const isDragging = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const stateClass = computed(() => ({
  'drop-idle': props.state === 'idle',
  'drop-dragging': props.state === 'dragging' || isDragging.value,
  'drop-valid': props.state === 'valid',
  'drop-error': props.state === 'error',
}))

function triggerInput() {
  inputRef.value?.click()
}

function onInputChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) emit('file', file)
  if (inputRef.value) inputRef.value.value = ''
}

function onDragEnter() { isDragging.value = true }
function onDragOver()  { isDragging.value = true }
function onDragLeave() { isDragging.value = false }

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) emit('file', file)
}
</script>

<style scoped>
.dropzone-wrapper {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 24px 20px 28px;
}

/* Chip */
.zone-label-row {
  display: flex;
  align-items: center;
}
.zone-chip {
  font-size: 0.66rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
  background: var(--accent-muted);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  padding: 3px 9px;
  border-radius: 4px;
}

/* Titles */
.zone-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-1);
  letter-spacing: -0.02em;
}
.zone-desc {
  font-size: 0.76rem;
  color: var(--text-3);
  line-height: 1.55;
  min-height: 36px;
}

/* Drop area */
.drop-area {
  position: relative;
  border: 1.5px dashed var(--border-strong);
  border-radius: var(--radius-md);
  padding: 32px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  text-align: center;
  background: var(--surface);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
  min-height: 180px;
  outline: none;
}
.drop-area:focus-visible {
  box-shadow: 0 0 0 3px var(--accent-muted);
  border-color: var(--accent);
}

.drop-idle:hover {
  border-color: var(--accent);
  background: var(--accent-muted);
}

.drop-dragging {
  border-color: var(--accent);
  border-style: solid;
  background: var(--accent-muted);
  box-shadow: 0 0 0 3px var(--accent-muted);
}

.drop-valid {
  border-color: var(--success);
  border-style: solid;
  background: color-mix(in srgb, var(--success) 7%, var(--surface));
  cursor: default;
}

.drop-error {
  border-color: var(--danger);
  border-style: solid;
  background: color-mix(in srgb, var(--danger) 7%, var(--surface));
}
.drop-error:hover {
  background: color-mix(in srgb, var(--danger) 11%, var(--surface));
}

/* Icon inside drop area */
.drop-icon {
  color: var(--text-3);
  width: 28px;
  height: 28px;
  transition: color 0.2s ease, transform 0.2s ease;
  margin-bottom: 4px;
}
.drop-idle:hover .drop-icon,
.drop-dragging .drop-icon {
  color: var(--accent);
}
.drop-icon.pulse {
  animation: pulse-scale 0.8s ease-in-out infinite;
}
@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.15); }
}

/* Text in drop area */
.drop-main-text {
  font-size: 0.84rem;
  color: var(--text-2);
}
.drop-link {
  font-weight: 600;
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.drop-or {
  color: var(--text-2);
}
.drop-sub-text {
  font-size: 0.72rem;
  color: var(--text-3);
  margin-top: 2px;
}

/* Valid state */
.drop-status-icon {
  margin-bottom: 6px;
}
.valid-icon {
  color: var(--success);
  animation: pop-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes pop-in {
  from { transform: scale(0.6); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
}
.error-icon { color: var(--danger); }

.drop-filename {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--success);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.drop-valid-text {
  font-size: 0.73rem;
  color: var(--success);
  opacity: 0.8;
}
.replace-btn {
  margin-top: 8px;
  font-size: 0.72rem;
  color: var(--text-3);
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 3px 10px;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}
.replace-btn:hover {
  border-color: var(--border-strong);
  color: var(--text-2);
}

.drop-error-text {
  font-size: 0.8rem;
  color: var(--danger);
  font-weight: 500;
  max-width: 200px;
}

/* Hidden input */
.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  pointer-events: none;
}

/* Dragging-over state for the whole wrapper */
.dropzone-wrapper.dragging .drop-area {
  border-color: var(--accent);
  border-style: solid;
}

/* Mobile */
@media (max-width: 640px) {
  .dropzone-wrapper {
    padding: 16px 4px 20px;
  }
}
</style>
