<template>
  <div class="app">

    <!-- ── Upload view ─────────────────────────────────────── -->
    <UploadView v-if="!data && !loading" @ready="onFilesReady" />

    <!-- ── App shell (shown after data loaded) ────────────── -->
    <template v-else>

    <!-- ── Navbar ─────────────────────────────────────────── -->
    <nav class="navbar" role="banner">
      <div class="navbar-inner">
        <div class="brand">
          <div class="brand-text">
            <span class="brand-name">Lipo<span class="brand-bold">Grid</span></span>
            <span class="brand-tag">Pilot</span>
          </div>
        </div>

        <button
          class="theme-btn"
          @click="toggle"
          :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <svg v-if="isDark" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <circle cx="12" cy="12" r="4.5"/>
            <line x1="12" y1="2"   x2="12" y2="5"/>
            <line x1="12" y1="19"  x2="12" y2="22"/>
            <line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/>
            <line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/>
            <line x1="2"  y1="12" x2="5"  y2="12"/>
            <line x1="19" y1="12" x2="22" y2="12"/>
            <line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/>
            <line x1="17.66" y1="6.34"  x2="19.78" y2="4.22"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
          <span class="theme-btn-label">{{ isDark ? 'Light' : 'Dark' }}</span>
        </button>
      </div>
    </nav>

    <!-- ── Main ──────────────────────────────────────────────-->
    <main class="main">

      <!-- Loading (parsing uploaded files) -->
      <div v-if="loading" class="state-center" role="status">
        <div class="spinner" aria-hidden="true" />
        <span class="state-label">Parsing datasets…</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="state-center" role="alert">
        <div class="error-card">
          <strong>Failed to load data</strong><br/>{{ error }}
        </div>
      </div>

      <!-- Ready -->
      <template v-else>
        <!-- Search bar — always at the top, fixed height -->
        <div class="search-row">
          <div class="search-wrap">
            <SearchBar
              :results="searchResults"
              @update:query="onQuery"
              @select="onSelect"
            />
            <p class="search-hint">
              Search by gene name, lipid name, or gene KO identifier
            </p>
          </div>
        </div>

        <!-- Content area — fills all remaining vertical space -->
        <div class="content-area">

          <!-- Empty state -->
          <div v-if="!selection" class="state-center">
            <div class="empty-card">
              <div class="empty-icon" aria-hidden="true">
                <svg viewBox="0 0 48 48" width="44" height="44" fill="none">
                  <rect x="4"  y="4"  width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.8" opacity="0.8"/>
                  <rect x="26" y="4"  width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.8" opacity="0.45"/>
                  <rect x="4"  y="26" width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.8" opacity="0.45"/>
                  <rect x="26" y="26" width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.8" opacity="0.2"/>
                </svg>
              </div>
              <p class="empty-title">Select a gene, lipid, or knockout to visualize</p>
              <p class="empty-desc">
                Selecting a gene or lipid shows its response across all KOs.<br/>
                Selecting a <strong>Gene KO</strong> shows two volcano plots side by side.
              </p>
            </div>
          </div>

          <!-- Single volcano: gene or lipid selected -->
          <section
            v-else-if="selection.type !== 'ko'"
            class="plots-area plots-single"
            aria-label="Volcano plot"
          >
            <div class="plot-cell">
              <VolcanoPlot :points="singlePoints" :title="singleTitle" />
            </div>
          </section>

          <!-- Double volcano: KO selected -->
          <section
            v-else
            class="plots-area plots-double"
            aria-label="KO volcano plots"
          >
            <div class="plot-cell">
              <VolcanoPlot
                :points="koLipidPoints"
                :title="`${selection.name} KO — Lipidomics`"
              />
            </div>
            <div class="plot-cell">
              <VolcanoPlot
                :points="koGenePoints"
                :title="`${selection.name} KO — Gene expression`"
              />
            </div>
          </section>

        </div><!-- /content-area -->
      </template>
    </main>

    </template><!-- /app shell -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useData } from './composables/useData'
import { useSearch } from './composables/useSearch'
import { useTheme } from './composables/useTheme'
import SearchBar from './components/SearchBar.vue'
import VolcanoPlot from './components/VolcanoPlot.vue'
import UploadView from './components/UploadView.vue'
import type { SearchCandidate, VolcanoPoint } from './types'

const { data, loading, error, loadFromFiles } = useData()
const { query, results: searchResults } = useSearch(() => data.value)

async function onFilesReady(lipidFile: File, geneFile: File) {
  await loadFromFiles(lipidFile, geneFile)
}
const { isDark, toggle } = useTheme()

const selection = ref<SearchCandidate | null>(null)

function onQuery(q: string) {
  query.value = q
  if (!q) selection.value = null
}

function onSelect(candidate: SearchCandidate) {
  selection.value = candidate.name ? candidate : null
}

const singlePoints = computed<VolcanoPoint[]>(() => {
  if (!data.value || !selection.value || selection.value.type === 'ko') return []
  const map = selection.value.type === 'lipid'
    ? data.value.lipids.get(selection.value.name)
    : data.value.genes.get(selection.value.name)
  if (!map) return []
  return [...map.entries()].map(([ko, e]) => ({ name: ko, log2FC: e.log2FC, pvalue: e.pvalue }))
})

const singleTitle = computed(() => {
  if (!selection.value) return ''
  const t = selection.value.type === 'lipid' ? 'Lipid' : 'Gene'
  return `${t}: ${selection.value.name} — effect across all KOs`
})

const koGenePoints = computed<VolcanoPoint[]>(() => {
  if (!data.value || selection.value?.type !== 'ko') return []
  const ko = selection.value.name
  return [...data.value.genes.entries()]
    .flatMap(([g, m]) => { const e = m.get(ko); return e ? [{ name: g, log2FC: e.log2FC, pvalue: e.pvalue }] : [] })
})

const koLipidPoints = computed<VolcanoPoint[]>(() => {
  if (!data.value || selection.value?.type !== 'ko') return []
  const ko = selection.value.name
  return [...data.value.lipids.entries()]
    .flatMap(([l, m]) => { const e = m.get(ko); return e ? [{ name: l, log2FC: e.log2FC, pvalue: e.pvalue }] : [] })
})
</script>

<style scoped>
/* ── App shell: locked to viewport height, no scrolling ── */
.app {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

/* ── Navbar ──────────────────────────────────────────────── */
.navbar {
  flex-shrink: 0;
  z-index: 50;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}
.navbar-inner {
  padding: 0 24px;
  height: 52px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand { display: flex; align-items: center; gap: 9px; flex-shrink: 0; }
.brand-icon { color: var(--accent); display: flex; align-items: center; }
.brand-text { display: flex; align-items: baseline; gap: 7px; }
.brand-name {
  font-size: 1.05rem; font-weight: 400;
  letter-spacing: -0.03em; color: var(--text-1);
}
.brand-bold { font-weight: 600; }
.brand-tag {
  font-size: 0.63rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--accent); background: var(--accent-muted);
  padding: 2px 6px; border-radius: 3px;
}
.navbar-subtitle {
  font-size: 0.78rem; color: var(--text-3);
  letter-spacing: 0.01em; flex: 1;
}
.theme-btn {
  display: flex; align-items: center; gap: 5px;
  margin-left: auto;
  padding: 5px 11px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface-2); color: var(--text-2);
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.78rem; font-weight: 500; cursor: pointer;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
  flex-shrink: 0;
}
.theme-btn:hover { background: var(--accent-muted); border-color: var(--accent); color: var(--accent); }
.theme-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.theme-btn-label { line-height: 1; }

/* ── Main: fills remaining viewport height ───────────────── */
.main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 20px 14px;
  gap: 10px;
  overflow: hidden;
}

/* ── Search row ──────────────────────────────────────────── */
.search-row {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
}
.search-wrap {
  width: 100%;
  max-width: 600px;
  text-align: center;
}
.search-hint {
  margin-top: 6px;
  font-size: 0.74rem;
  color: var(--text-3);
}

/* ── Content area: fills all space below search ──────────── */
.content-area {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: stretch;
}

/* ── Centered state (loading / error / empty) ────────────── */
.state-center {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
}
.state-label { font-size: 0.88rem; color: var(--text-2); }

.spinner {
  width: 32px; height: 32px;
  border: 2.5px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-card {
  max-width: 480px;
  padding: 18px 22px;
  background: var(--surface);
  border: 1px solid var(--danger);
  border-radius: var(--radius-md);
  color: var(--danger);
  font-size: 0.88rem;
  text-align: center;
  line-height: 1.6;
}

/* ── Empty state ─────────────────────────────────────────── */
.empty-card {
  max-width: 440px;
  padding: 36px 28px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  text-align: center;
}
.empty-icon { color: var(--text-3); margin-bottom: 18px; }
.empty-title { font-size: 0.95rem; font-weight: 500; color: var(--text-1); margin-bottom: 8px; }
.empty-desc { font-size: 0.82rem; color: var(--text-2); line-height: 1.7; }
.empty-desc strong { color: var(--accent); font-weight: 500; }

/* ── Plots area ──────────────────────────────────────────── */
.plots-area {
  width: 100%;
  height: 100%;
  display: flex;
  gap: 14px;
  animation: fadeIn 0.22s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}

/* Single plot: one cell fills everything */
.plots-single { flex-direction: column; }
.plots-single .plot-cell { flex: 1; }

/* Two plots: side by side on wide screens */
.plots-double { flex-direction: row; }
.plots-double .plot-cell { flex: 1; min-width: 0; }

/* Narrow screens: stack vertically and allow internal scroll */
@media (max-width: 860px) {
  .plots-double {
    flex-direction: column;
    overflow-y: auto;
  }
  .plots-double .plot-cell {
    flex-shrink: 0;
    min-height: 340px;
  }
}

/* ── Plot cell: the sizing container for VolcanoPlot ─────── */
.plot-cell {
  position: relative; /* VolcanoPlot fills this with position:absolute; inset:0 */
  min-height: 0;
}

/* Single cell also fills its column direction */
.plots-single .plot-cell {
  min-height: 0;
}
</style>
