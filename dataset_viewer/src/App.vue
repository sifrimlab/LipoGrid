<template>
  <div class="app">
    <div class="app-body">

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
          class="nav-btn"
          @click="licenseOpen = true"
          aria-label="View license agreement"
          title="View license agreement"
        >
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <circle cx="12" cy="12" r="9"/>
            <path d="M15 9.5a4 4 0 1 0 0 5"/>
          </svg>
          <span class="nav-btn-label">License</span>
        </button>

        <button
          class="nav-btn nav-btn-right"
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
          <span class="nav-btn-label">{{ isDark ? 'Light' : 'Dark' }}</span>
        </button>
      </div>
    </nav>

    <!-- ── Main ──────────────────────────────────────────────-->
    <main class="main">

      <!-- Loading (parsing uploaded files) -->
      <div v-if="loading" class="state-center" role="status">
        <div class="spinner" aria-hidden="true" />
        <span class="state-label">Loading datasets…</span>
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
              :query-prop="query"
              @update:query="onQuery"
              @select="onSelect"
            />
            <p class="search-hint">
              Search by gene name, lipid name, or gene KO identifier
            </p>
          </div>
        </div>

        <!-- Content area — fills all remaining vertical space -->
        <div class="content-area" :class="{ 'content-area-grid': !selection }">

          <!-- Card grid: no selection yet -->
          <CardGrid
            v-if="!selection"
            :items="gridItems"
            @select="onCardSelect"
          />

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
    </div><!-- /app-body -->

    <!-- ── Footer ─────────────────────────────────────────── -->
    <footer class="app-footer">© 2026 KU Leuven — All rights reserved</footer>

    <!-- ── License dialog ─────────────────────────────────── -->
    <LicenseDialog v-if="licenseOpen" @close="licenseOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useData } from './composables/useData'
import { useSearch } from './composables/useSearch'
import { useTheme } from './composables/useTheme'
import SearchBar from './components/SearchBar.vue'
import VolcanoPlot from './components/VolcanoPlot.vue'
import UploadView from './components/UploadView.vue'
import CardGrid from './components/CardGrid.vue'
import LicenseDialog from './components/LicenseDialog.vue'
import type { SearchCandidate, VolcanoPoint } from './types'

const LIPID_URL = `${import.meta.env.BASE_URL}data/all_lipid_log2FC_pvalues_per_gene.csv`
const GENE_URL = `${import.meta.env.BASE_URL}data/CROP_seq_log2FC_manw_pergeneKO_sameKOs.csv`

const { data, loading, error, loadFromFiles, loadFromUrls } = useData()
const { query, results: searchResults } = useSearch(() => data.value)

// Auto-load bundled datasets; on failure UploadView shows automatically
onMounted(() => { void loadFromUrls(LIPID_URL, GENE_URL) })

async function onFilesReady(lipidFile: File, geneFile: File) {
  await loadFromFiles(lipidFile, geneFile)
}
const { isDark, toggle } = useTheme()

const licenseOpen = ref(false)

const selection = ref<SearchCandidate | null>(null)

function onQuery(q: string) {
  query.value = q
  if (!q) selection.value = null
}

function onSelect(candidate: SearchCandidate) {
  selection.value = candidate.name ? candidate : null
}

function onCardSelect(candidate: SearchCandidate) {
  selection.value = candidate
  query.value = candidate.name
}

const gridItems = computed<SearchCandidate[]>(() => {
  if (!data.value) return []
  const items: SearchCandidate[] = [
    ...data.value.koNames.map(name => ({ name, type: 'ko' as const })),
    ...[...data.value.lipids.keys()].map(name => ({ name, type: 'lipid' as const })),
  ]
  const q = query.value.trim()
  if (!q) return items
  try {
    const regex = new RegExp(q, 'i')
    return items.filter(item => regex.test(item.name))
  } catch {
    return items
  }
})

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

/* ── Body: fills space between top and footer ────────────── */
.app-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* ── Footer ──────────────────────────────────────────────── */
.app-footer {
  flex-shrink: 0;
  padding: 8px 24px;
  text-align: center;
  font-size: 0.72rem;
  letter-spacing: 0.02em;
  color: var(--text-3);
  background: var(--surface);
  border-top: 1px solid var(--border);
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
.nav-btn {
  display: flex; align-items: center; gap: 5px;
  padding: 5px 11px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface-2); color: var(--text-2);
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.78rem; font-weight: 500; cursor: pointer;
  transition: background var(--transition), border-color var(--transition), color var(--transition);
  flex-shrink: 0;
}
.nav-btn:hover { background: var(--accent-muted); border-color: var(--accent); color: var(--accent); }
.nav-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.nav-btn-label { line-height: 1; }
.nav-btn-right { margin-left: auto; }

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

/* When showing the card grid, allow vertical scrolling */
.content-area-grid {
  overflow-y: auto;
}

/* ── Centered state (loading / error) ────────────── */
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
