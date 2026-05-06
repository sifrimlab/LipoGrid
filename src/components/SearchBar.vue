<template>
  <div class="search-wrapper" ref="wrapperRef">
    <div class="search-input-row" :class="{ focused: isFocused }">
      <span class="search-icon" aria-hidden="true">
        <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="8.5" cy="8.5" r="5.5"/>
          <path d="M17 17l-3.5-3.5"/>
        </svg>
      </span>
      <input
        ref="inputRef"
        type="text"
        class="search-input"
        placeholder="Search gene, lipid, or gene KO…"
        v-model="query"
        @keydown="onKeydown"
        @focus="onFocus"
        @blur="onBlur"
        autocomplete="off"
        spellcheck="false"
        aria-label="Search for gene, lipid, or gene KO"
        aria-autocomplete="list"
        :aria-expanded="open && results.length > 0"
        aria-haspopup="listbox"
      />
      <button v-if="query" class="clear-btn" @click="clear" aria-label="Clear search" tabindex="-1">
        <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
          <path d="M1 1l12 12M13 1L1 13"/>
        </svg>
      </button>
    </div>

    <ul
      v-if="open && results.length"
      class="dropdown"
      role="listbox"
      aria-label="Search suggestions"
    >
      <li
        v-for="(item, idx) in results"
        :key="item.type + item.name"
        class="dropdown-item"
        :class="{ highlighted: idx === activeIdx }"
        role="option"
        :aria-selected="idx === activeIdx"
        @mousedown.prevent="select(item)"
        @mousemove="activeIdx = idx"
      >
        <span class="badge" :class="'badge-' + item.type" aria-label="Type:">
          {{ item.type === 'ko' ? 'GENE KO' : item.type.toUpperCase() }}
        </span>
        <span class="item-name">{{ item.name }}</span>
      </li>
    </ul>

    <div
      v-if="open && query.trim() && !results.length"
      class="dropdown no-results"
      role="status"
    >
      No matches for "<em>{{ query }}</em>"
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { onClickOutside } from '../composables/onClickOutside'
import type { SearchCandidate } from '../types'

const props = defineProps<{ results: SearchCandidate[] }>()
const emit = defineEmits<{
  (e: 'update:query', v: string): void
  (e: 'select', v: SearchCandidate): void
}>()

const query = ref('')
const open = ref(false)
const isFocused = ref(false)
const activeIdx = ref(-1)
const wrapperRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

watch(query, (v) => {
  emit('update:query', v)
  open.value = true
  activeIdx.value = -1
})

watch(() => props.results, () => { activeIdx.value = -1 })

function select(item: SearchCandidate) {
  query.value = item.name
  open.value = false
  emit('select', item)
}

function clear() {
  query.value = ''
  open.value = false
  inputRef.value?.focus()
  emit('update:query', '')
  emit('select', { name: '', type: 'gene' })
}

function onFocus() {
  isFocused.value = true
  if (query.value) open.value = true
}

function onBlur() {
  isFocused.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value || !props.results.length) {
    if (e.key === 'Escape') { open.value = false }
    return
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIdx.value = Math.min(activeIdx.value + 1, props.results.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIdx.value = Math.max(activeIdx.value - 1, 0)
  } else if (e.key === 'Enter' && activeIdx.value >= 0) {
    e.preventDefault()
    select(props.results[activeIdx.value])
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

onClickOutside(wrapperRef, () => { open.value = false })
</script>

<style scoped>
.search-wrapper {
  position: relative;
  width: 100%;
}

/* Input row */
.search-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.search-input-row.focused {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-muted), var(--shadow-sm);
}

.search-icon {
  color: var(--text-3);
  display: flex;
  align-items: center;
  flex-shrink: 0;
  transition: color var(--transition);
}

.search-input-row.focused .search-icon {
  color: var(--accent);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 13px 0;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.95rem;
  background: transparent;
  color: var(--text-1);
  min-width: 0;
}

.search-input::placeholder {
  color: var(--text-3);
}

.clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-3);
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
  transition: color var(--transition), background var(--transition);
}

.clear-btn:hover {
  color: var(--text-1);
  background: var(--surface-2);
}

/* Dropdown */
.dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  list-style: none;
  z-index: 100;
  max-height: 380px;
  overflow-y: auto;
  padding: 4px 0;
}

.no-results {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 13px 16px;
  color: var(--text-2);
  font-size: 0.875rem;
  z-index: 100;
}

.no-results em {
  font-style: normal;
  color: var(--text-1);
}

/* Dropdown item */
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  cursor: pointer;
  transition: background var(--transition);
  user-select: none;
}

.dropdown-item.highlighted,
.dropdown-item:hover {
  background: var(--accent-muted);
}

/* Badges */
.badge {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
  font-family: 'IBM Plex Mono', monospace;
  flex-shrink: 0;
}

.badge-ko {
  background: color-mix(in srgb, #059669 12%, transparent);
  color: var(--success);
  border: 1px solid color-mix(in srgb, #059669 25%, transparent);
}

.badge-lipid {
  background: color-mix(in srgb, #D97706 10%, transparent);
  color: var(--warning);
  border: 1px solid color-mix(in srgb, #D97706 22%, transparent);
}

.badge-gene {
  background: var(--accent-muted);
  color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
}

.item-name {
  font-size: 0.9rem;
  color: var(--text-1);
  font-family: 'IBM Plex Sans', sans-serif;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
