<template>
  <div class="card-grid-container">
    <div v-if="items.length === 0" class="grid-empty">
      <p class="grid-empty-text">No matching items</p>
    </div>
    <div v-else class="card-grid">
      <button
        v-for="item in items"
        :key="item.type + item.name"
        class="card"
        :data-type="item.type"
        @click="emit('select', item)"
        :aria-label="`Select ${item.type === 'ko' ? 'Gene KO' : 'Lipid'}: ${item.name}`"
      >
        <span class="badge" :class="'badge-' + item.type">
          {{ item.type === 'ko' ? 'KO' : 'LIPID' }}
        </span>
        <span class="card-name">{{ item.name }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SearchCandidate } from '../types'

defineProps<{ items: SearchCandidate[] }>()

const emit = defineEmits<{
  (e: 'select', v: SearchCandidate): void
}>()
</script>

<style scoped>
.card-grid-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 4px 2px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 8px;
  padding: 4px 0 16px;
}

/* ── Card ──────────────────────────────────────────────────── */
.card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: 'IBM Plex Sans', sans-serif;
  text-align: left;
  transition:
    background var(--transition),
    border-color var(--transition),
    box-shadow var(--transition);
  min-width: 0;
}

.card:hover {
  background: var(--surface-2);
  border-color: var(--accent);
  box-shadow: var(--shadow-sm);
}

.card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.card[data-type="ko"]:hover {
  border-color: var(--success);
}

.card[data-type="lipid"]:hover {
  border-color: var(--warning);
}

/* ── Badge ─────────────────────────────────────────────────── */
.badge {
  font-size: 0.6rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
  font-family: 'IBM Plex Mono', monospace;
  flex-shrink: 0;
  line-height: 1.4;
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

/* ── Card name ─────────────────────────────────────────────── */
.card-name {
  font-size: 0.8rem;
  color: var(--text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* ── Empty state ───────────────────────────────────────────── */
.grid-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
}

.grid-empty-text {
  font-size: 0.88rem;
  color: var(--text-3);
}

/* ── Responsive: smaller cards on narrow screens ───────────── */
@media (max-width: 600px) {
  .card-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 6px;
  }

  .card {
    padding: 6px 8px;
    gap: 6px;
  }

  .card-name {
    font-size: 0.75rem;
  }
}
</style>
