<template>
  <!--
    The wrapper fills whatever .plot-cell gives it (position: absolute; inset: 0).
    ResizeObserver reads the actual pixel size and drives D3.
  -->
  <div class="volcano-wrapper" ref="wrapperRef">
    <svg ref="svgRef" :width="plotWidth" :height="plotHeight" style="display:block" />
    <div
      v-if="tooltip.visible"
      class="tooltip"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      role="tooltip"
    >
      <div class="tooltip-name">{{ tooltip.name }}</div>
      <table class="tooltip-table">
        <tbody>
          <tr>
            <td class="tooltip-key">log₂FC</td>
            <td class="tooltip-val">{{ tooltip.log2FC }}</td>
          </tr>
          <tr>
            <td class="tooltip-key">p-value</td>
            <td class="tooltip-val">{{ tooltip.pvalue }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { isDark } from '../composables/useTheme'
import type { VolcanoPoint } from '../types'

const props = defineProps<{
  points: VolcanoPoint[]
  title: string
}>()

/* ── Sizing via ResizeObserver ───────────────────────────── */
const svgRef     = ref<SVGSVGElement | null>(null)
const wrapperRef = ref<HTMLDivElement | null>(null)
const plotWidth  = ref(0)
const plotHeight = ref(0)

const margin = { top: 52, right: 90, bottom: 64, left: 72 }

let drawRaf: number | null = null
let ro: ResizeObserver | null = null

let wrapperRect = { left: 0, top: 0 }

function schedDraw() {
  if (drawRaf !== null) cancelAnimationFrame(drawRaf)
  drawRaf = requestAnimationFrame(() => {
    drawRaf = null
    draw()
  })
}

onMounted(() => {
  precompute()
  if (!wrapperRef.value) return
  ro = new ResizeObserver((entries) => {
    const { width, height } = entries[0].contentRect
    if (width > 40 && height > 40) {
      plotWidth.value  = Math.floor(width)
      plotHeight.value = Math.floor(height)
      wrapperRect = wrapperRef.value!.getBoundingClientRect()
      schedDraw()
    }
  })
  ro.observe(wrapperRef.value)
})

onUnmounted(() => {
  ro?.disconnect()
  if (drawRaf !== null) cancelAnimationFrame(drawRaf)
  svgGroups = null
  zoomBehavior = null
})

/* ── Tooltip ─────────────────────────────────────────────── */
const tooltip = reactive({
  visible: false,
  x: 0, y: 0,
  name: '', log2FC: '', pvalue: '',
})

/* ── Theme-aware colours ─────────────────────────────────── */
const c = computed(() =>
  isDark.value
    ? {
        grid:           '#21262D',
        axisDomain:     '#444C56',
        axisText:       '#8B949E',
        axisLabel:      '#CDD5DF',
        title:          '#E6EDF3',
        dotBelow:       '#3D4A5C',
        dotBelowStroke: '#2D3748',
        dotAbove:       '#F87171',
        dotAboveStroke: '#EF4444',
        threshold:      '#60A5FA',
        threshLabel:    '#93C5FD',
        label:          '#FCA5A5',
        zero:           '#30363D',
      }
    : {
        grid:           '#EAEAE4',
        axisDomain:     '#C0C4D0',
        axisText:       '#52526A',
        axisLabel:      '#16161C',
        title:          '#16161C',
        dotBelow:       '#94A3B8',
        dotBelowStroke: '#64748B',
        dotAbove:       '#DC2626',
        dotAboveStroke: '#B91C1C',
        threshold:      '#1A56DB',
        threshLabel:    '#1447C0',
        label:          '#991B1B',
        zero:           '#D1D5DB',
      },
)

type Colors = typeof c.value

/* ── Threshold state ─────────────────────────────────────── */
const DEFAULT_THRESHOLD = -Math.log10(0.05)
let thresholdNegLog = DEFAULT_THRESHOLD
function negLog10(p: number) { return -Math.log10(p) }

/* ── Pre-computed values (rebuilt when props.points changes) ── */
let cachedPts: VolcanoPoint[] = []
let negLogByName = new Map<string, number>()
let cachedMaxNegLog = 0
let cachedAbsMax = 0

function precompute() {
  cachedPts = props.points.filter((p) => p.pvalue > 0 && isFinite(p.log2FC))
  negLogByName = new Map()
  cachedMaxNegLog = 0
  cachedAbsMax = 0
  for (const p of cachedPts) {
    const nl = negLog10(p.pvalue)
    negLogByName.set(p.name, nl)
    if (nl > cachedMaxNegLog) cachedMaxNegLog = nl
    const abs = Math.abs(p.log2FC)
    if (abs > cachedAbsMax) cachedAbsMax = abs
  }
}

/* ── Persistent SVG groups ───────────────────────────────── */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnySel = d3.Selection<any, any, any, any>

// Unique clip-path id per component instance
const clipId = `vc-${Math.random().toString(36).slice(2, 9)}`

let svgGroups: {
  g: AnySel
  zoomBg: AnySel     // transparent bg rect — captures events in empty areas of the plot
  gridX: AnySel; gridY: AnySel
  axisX: AnySel; axisY: AnySel
  xLabel: AnySel; yLabel: AnySel
  title: AnySel
  clipRect: AnySel   // <rect> inside clipPath — dimensions updated on resize
  zeroLine: AnySel   // clipped vertical reference at x=0
  dots: AnySel       // clipped scatter circles
  labels: AnySel     // clipped point labels
  thresh: AnySel     // threshold line + drag area (NOT clipped — label extends past right edge)
} | null = null

function ensureGroups(svg: AnySel) {
  if (svgGroups) return

  // Clip path covering the inner plot area
  const clipRect = svg.append('defs')
    .append('clipPath').attr('id', clipId)
    .append('rect')

  const g = svg.append('g')

  // Transparent background rect as first child so it sits behind everything.
  // Its size is updated each draw() to match iW×iH, giving the zoom behavior a
  // surface to capture wheel/drag events even where no data element exists.
  const zoomBg = g.append('rect').attr('fill', 'none').attr('pointer-events', 'all')

  // Grid and axes are NOT clipped (they fill the inner area by construction)
  const gridX  = g.append('g')
  const gridY  = g.append('g')
  const axisX  = g.append('g')
  const axisY  = g.append('g')
  const xLabel = g.append('text')
  const yLabel = g.append('text')

  // Data elements are clipped so zoomed points don't bleed into margins
  const dataG    = g.append('g').attr('clip-path', `url(#${clipId})`)
  const zeroLine = dataG.append('line')
  const dots     = dataG.append('g')
  const labels   = dataG.append('g')

  // Threshold group is outside the clip so its p-value label can sit in the right margin
  const thresh = g.append('g')

  svgGroups = {
    g, zoomBg, gridX, gridY, axisX, axisY, xLabel, yLabel,
    title: svg.append('text'),
    clipRect, zeroLine, dots, labels, thresh,
  }
}

/* ── Zoom state ──────────────────────────────────────────── */
type Scale = d3.ScaleLinear<number, number>

let baseXScale: Scale | null = null
let baseYScale: Scale | null = null
let lastIW = 0
let lastIH = 0
let zoomBehavior: d3.ZoomBehavior<SVGGElement, unknown> | null = null
let suppressZoom = false

function onZoom(event: d3.D3ZoomEvent<SVGGElement, unknown>) {
  if (suppressZoom || !baseXScale || !baseYScale || !svgGroups) return
  const xZ = event.transform.rescaleX(baseXScale)
  const yZ = event.transform.rescaleY(baseYScale)
  renderContent(xZ, yZ, lastIW, lastIH, c.value)
}

/* ── Shared rendering (called by draw() and onZoom) ─────── */
function renderContent(xScale: Scale, yScale: Scale, iW: number, iH: number, col: Colors) {
  const s = svgGroups!

  // Grid
  s.gridX.attr('transform', `translate(0,${iH})`)
    .call(d3.axisBottom(xScale).tickSize(-iH).tickFormat(() => ''))
    .call((a: AnySel) => a.select('.domain').remove())
    .call((a: AnySel) => a.selectAll('line').attr('stroke', col.grid).attr('stroke-dasharray', '3,3'))
  s.gridY
    .call(d3.axisLeft(yScale).tickSize(-iW).tickFormat(() => ''))
    .call((a: AnySel) => a.select('.domain').remove())
    .call((a: AnySel) => a.selectAll('line').attr('stroke', col.grid).attr('stroke-dasharray', '3,3'))

  // X axis
  s.axisX.attr('transform', `translate(0,${iH})`)
    .call(d3.axisBottom(xScale).ticks(Math.max(4, Math.floor(iW / 80))))
    .call((a: AnySel) => a.select('.domain').attr('stroke', col.axisDomain))
    .call((a: AnySel) => a.selectAll('text').attr('fill', col.axisText).attr('font-size', '11px').attr('font-family', 'IBM Plex Mono, monospace'))

  // Y axis
  s.axisY
    .call(d3.axisLeft(yScale).ticks(Math.max(3, Math.floor(iH / 60))))
    .call((a: AnySel) => a.select('.domain').attr('stroke', col.axisDomain))
    .call((a: AnySel) => a.selectAll('text').attr('fill', col.axisText).attr('font-size', '11px').attr('font-family', 'IBM Plex Mono, monospace'))

  // Zero line (clipped)
  s.zeroLine
    .attr('x1', xScale(0)).attr('x2', xScale(0)).attr('y1', 0).attr('y2', iH)
    .attr('stroke', col.zero).attr('stroke-width', 1).attr('stroke-dasharray', '4,4')

  function isAbove(d: VolcanoPoint) { return (negLogByName.get(d.name) ?? 0) >= thresholdNegLog }

  // Dots (clipped)
  s.dots.selectAll<SVGCircleElement, VolcanoPoint>('circle')
    .data(cachedPts, (d: VolcanoPoint) => d.name)
    .join('circle')
    .attr('cx', (d: VolcanoPoint) => xScale(d.log2FC))
    .attr('cy', (d: VolcanoPoint) => yScale(negLogByName.get(d.name)!))
    .attr('r', 4)
    .attr('fill', (d: VolcanoPoint) => isAbove(d) ? col.dotAbove : col.dotBelow)
    .attr('fill-opacity', 0.8)
    .attr('stroke', (d: VolcanoPoint) => isAbove(d) ? col.dotAboveStroke : col.dotBelowStroke)
    .attr('stroke-width', 0.6)
    .style('cursor', 'pointer')
    .on('mouseover', (event: MouseEvent, d: VolcanoPoint) => {
      tooltip.visible = true
      tooltip.x = event.clientX - wrapperRect.left + 14
      tooltip.y = event.clientY - wrapperRect.top - 8
      tooltip.name   = d.name
      tooltip.log2FC = (d.log2FC >= 0 ? '+' : '') + d.log2FC.toFixed(3)
      tooltip.pvalue = d.pvalue.toExponential(3)
      d3.select(event.currentTarget as SVGCircleElement).attr('r', 6.5).attr('stroke-width', 1.2)
    })
    .on('mousemove', (event: MouseEvent) => {
      tooltip.x = event.clientX - wrapperRect.left + 14
      tooltip.y = event.clientY - wrapperRect.top - 8
    })
    .on('mouseleave', (event: MouseEvent) => {
      tooltip.visible = false
      d3.select(event.currentTarget as SVGCircleElement).attr('r', 4).attr('stroke-width', 0.6)
    })

  // Labels (clipped)
  const sig = cachedPts.filter(isAbove).sort((a, b) => a.pvalue - b.pvalue).slice(0, 40)
  s.labels.selectAll<SVGTextElement, VolcanoPoint>('text')
    .data(sig, (d: VolcanoPoint) => d.name)
    .join('text')
    .attr('x', (d: VolcanoPoint) => xScale(d.log2FC))
    .attr('y', (d: VolcanoPoint) => yScale(negLogByName.get(d.name)!) - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('font-family', 'IBM Plex Mono, monospace')
    .attr('fill', col.label)
    .attr('pointer-events', 'none')
    .text((d: VolcanoPoint) => d.name)

  // Threshold line + drag (not clipped)
  s.thresh.selectAll('*').remove()
  const ty = yScale(thresholdNegLog)
  const pCutoff = Math.pow(10, -thresholdNegLog)
  const pLabel  = pCutoff < 0.001 ? pCutoff.toExponential(1) : pCutoff.toFixed(3)

  s.thresh.append('line')
    .attr('x1', 0).attr('x2', iW).attr('y1', ty).attr('y2', ty)
    .attr('stroke', col.threshold).attr('stroke-width', 1.5).attr('stroke-dasharray', '6,3')
    .style('cursor', 'ns-resize')

  s.thresh.append('text')
    .attr('x', iW + 5).attr('y', ty + 4)
    .attr('font-size', '9.5px').attr('font-family', 'IBM Plex Mono, monospace')
    .attr('fill', col.threshLabel)
    .text(`p=${pLabel}`)

  s.thresh.append('rect')
    .attr('x', 0).attr('width', iW).attr('y', ty - 9).attr('height', 18)
    .attr('fill', 'transparent').style('cursor', 'ns-resize')
    .call(
      d3.drag<SVGRectElement, unknown>().on('drag', (event) => {
        const [, my] = d3.pointer(event, s.g.node())
        // Use the scales that were in effect when this threshold was rendered
        thresholdNegLog = Math.max(0, yScale.invert(Math.max(0, Math.min(iH, my))))
        renderContent(xScale, yScale, iW, iH, col)
      }),
    )
}

/* ── Main draw (resize / data change) ───────────────────── */
function draw() {
  const tW = plotWidth.value
  const tH = plotHeight.value
  if (tW < 40 || tH < 40) return

  const iW = tW - margin.left - margin.right
  const iH = tH - margin.top  - margin.bottom
  if (iW < 10 || iH < 10) return

  const svg = d3.select(svgRef.value!)
  ensureGroups(svg)

  const s = svgGroups!

  // Update clip rect and zoom background to match current inner plot dimensions
  s.clipRect.attr('width', iW).attr('height', iH)
  s.zoomBg.attr('width', iW).attr('height', iH)

  lastIW = iW
  lastIH = iH

  if (!cachedPts.length) {
    s.dots.selectAll('*').remove()
    s.labels.selectAll('*').remove()
    s.thresh.selectAll('*').remove()
    return
  }

  const col = c.value

  // Compute base scales from data domain + current plot size
  baseXScale = d3.scaleLinear()
    .domain([-cachedAbsMax * 1.12, cachedAbsMax * 1.12]).range([0, iW]).nice()
  baseYScale = d3.scaleLinear()
    .domain([0, cachedMaxNegLog * 1.12]).range([iH, 0]).nice()

  // Set up zoom behavior once per instance
  if (!zoomBehavior) {
    zoomBehavior = d3.zoom<SVGGElement, unknown>()
      .scaleExtent([1, 100])   // k=1 is the minimum — can't zoom out past original view
      .extent([[0, 0], [iW, iH]])
      .translateExtent([[0, 0], [iW, iH]])
      .on('zoom', onZoom)
    s.g.call(zoomBehavior)
  } else {
    zoomBehavior.extent([[0, 0], [iW, iH]]).translateExtent([[0, 0], [iW, iH]])
  }

  // Reset zoom to identity on every resize / data change.
  // suppressZoom prevents onZoom from firing and double-rendering.
  suppressZoom = true
  s.g.call(zoomBehavior.transform, d3.zoomIdentity)
  suppressZoom = false

  // Static elements (unchanged by zoom)
  s.g.attr('transform', `translate(${margin.left},${margin.top})`)

  s.xLabel.attr('x', iW / 2).attr('y', iH + 50)
    .attr('text-anchor', 'middle').attr('fill', col.axisLabel)
    .attr('font-size', '12.5px').attr('font-family', 'IBM Plex Sans, sans-serif').attr('font-weight', '500')
    .text('log₂ Fold Change')

  s.yLabel
    .attr('transform', 'rotate(-90)').attr('x', -iH / 2).attr('y', -58)
    .attr('text-anchor', 'middle').attr('fill', col.axisLabel)
    .attr('font-size', '12.5px').attr('font-family', 'IBM Plex Sans, sans-serif').attr('font-weight', '500')
    .text('-log₁₀(p-value)')

  s.title.attr('x', tW / 2).attr('y', 26)
    .attr('text-anchor', 'middle').attr('font-size', '13.5px').attr('font-weight', '600')
    .attr('font-family', 'IBM Plex Sans, sans-serif').attr('fill', col.title)
    .text(props.title)

  // Zoom-dependent content rendered at identity (base scales)
  renderContent(baseXScale, baseYScale, iW, iH, col)
}

watch(() => props.points, () => {
  thresholdNegLog = DEFAULT_THRESHOLD
  precompute()
  schedDraw()
})
watch(isDark, () => schedDraw())
</script>

<style scoped>
/* Fills .plot-cell absolutely — parent must be position:relative */
.volcano-wrapper {
  position: absolute;
  inset: 0;
  background: var(--plot-bg, var(--surface));
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  transition: background var(--transition), border-color var(--transition);
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--tooltip-bg);
  color: var(--tooltip-text);
  border-radius: var(--radius-sm);
  padding: 9px 13px;
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: nowrap;
  z-index: 200;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255,255,255,0.06);
}

.tooltip-name {
  font-weight: 600;
  font-family: 'IBM Plex Mono', monospace;
  margin-bottom: 5px;
  color: var(--tooltip-name);
  font-size: 0.82rem;
}

.tooltip-table { border-collapse: collapse; width: 100%; }

.tooltip-key {
  font-family: 'IBM Plex Sans', sans-serif;
  color: var(--text-3, #6E7681);
  padding-right: 14px;
  font-size: 0.77rem;
}

.tooltip-val {
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 500;
  font-size: 0.77rem;
  text-align: right;
}
</style>
