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

      const lipidRows = d3.csvParse(lipidText)
      const geneRows = d3.csvParse(geneText)

      const lipidCols = lipidRows.columns
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

      data.value = { lipids, genes, koNames }
    } catch (e) {
      error.value = String(e)
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, loadFromFiles }
}
