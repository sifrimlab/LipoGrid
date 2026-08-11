import { ref } from 'vue'
import * as d3 from 'd3'
import type { ParsedData, KOEntry } from '../types'

export function useData() {
  const data = ref<ParsedData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function extractKONames(columns: string[]): string[] {
    const names = new Set<string>()
    for (const col of columns) {
      if (col.endsWith('_log2FC')) names.add(col.slice(0, -7))
    }
    return [...names].sort()
  }

  function parseDatasets(lipidText: string, geneText: string): ParsedData {
    const lipidRows = d3.csvParse(lipidText)
    const geneRows = d3.csvParse(geneText)

    const lipidCols = lipidRows.columns
    if (!lipidCols.includes('lipid_annotation_self')) {
      throw new Error('Lipid matrix missing column: lipid_annotation_self')
    }
    if (!lipidCols.some(c => c.endsWith('_log2FC'))) {
      throw new Error('Lipid matrix has no {KO}_log2FC columns')
    }
    if (geneRows.columns.length < 2 || !geneRows.columns.some(c => c.endsWith('_log2FC'))) {
      throw new Error('Gene matrix has no {KO}_log2FC columns')
    }

    const lipidKOs = extractKONames(lipidCols)

    const lipids = new Map<string, Map<string, KOEntry>>()
    for (const row of lipidRows) {
      const name = row['lipid_annotation_self']
      if (!name) continue
      const koMap = new Map<string, KOEntry>()
      for (const ko of lipidKOs) {
        const fc = parseFloat(row[`${ko}_log2FC`] ?? '')
        const pv = parseFloat(row[`${ko}_pvalue`] ?? '')
        if (!isNaN(fc) && !isNaN(pv) && pv > 0) {
          koMap.set(ko, { log2FC: fc, pvalue: pv })
        }
      }
      lipids.set(name, koMap)
    }

    const geneCols = geneRows.columns
    const geneKOs = extractKONames(geneCols)
    const geneNameCol = geneCols[0]

    const genes = new Map<string, Map<string, KOEntry>>()
    for (const row of geneRows) {
      const name = row[geneNameCol]
      if (!name) continue
      const koMap = new Map<string, KOEntry>()
      for (const ko of geneKOs) {
        const fc = parseFloat(row[`${ko}_log2FC`] ?? '')
        const pv = parseFloat(row[`${ko}_pvalue`] ?? '')
        if (!isNaN(fc) && !isNaN(pv) && pv > 0) {
          koMap.set(ko, { log2FC: fc, pvalue: pv })
        }
      }
      genes.set(name, koMap)
    }

    const koSet = new Set([...lipidKOs, ...geneKOs])
    const koNames = [...koSet].sort()

    return { lipids, genes, koNames }
  }

  function readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = e => resolve(e.target?.result as string)
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
  }

  async function loadFromFiles(lipidFile: File, geneFile: File) {
    loading.value = true
    error.value = null
    try {
      const [lipidText, geneText] = await Promise.all([
        readFileAsText(lipidFile),
        readFileAsText(geneFile),
      ])
      data.value = parseDatasets(lipidText, geneText)
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  async function loadFromUrls(lipidUrl: string, geneUrl: string): Promise<boolean> {
    loading.value = true
    try {
      const [lipidRes, geneRes] = await Promise.all([fetch(lipidUrl), fetch(geneUrl)])
      if (!lipidRes.ok || !geneRes.ok) {
        throw new Error(`HTTP ${lipidRes.status} / ${geneRes.status}`)
      }
      const [lipidText, geneText] = await Promise.all([lipidRes.text(), geneRes.text()])
      data.value = parseDatasets(lipidText, geneText)
      return true
    } catch (e) {
      console.warn('[LipoGrid] Bundled data unavailable, falling back to upload', e)
      return false
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, loadFromFiles, loadFromUrls }
}
