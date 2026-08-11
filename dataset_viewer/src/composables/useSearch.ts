import { ref, watch } from 'vue'
import type { ParsedData, SearchCandidate } from '../types'

const MAX_RESULTS = 20

export function useSearch(getData: () => ParsedData | null) {
  const query = ref('')
  const results = ref<SearchCandidate[]>([])

  function buildCandidates(data: ParsedData): SearchCandidate[] {
    const candidates: SearchCandidate[] = []
    for (const ko of data.koNames) candidates.push({ name: ko, type: 'ko' })
    for (const name of data.lipids.keys()) candidates.push({ name, type: 'lipid' })
    for (const name of data.genes.keys()) candidates.push({ name, type: 'gene' })
    return candidates
  }

  let allCandidates: SearchCandidate[] = []

  watch(
    () => getData(),
    (data) => {
      if (data) allCandidates = buildCandidates(data)
    },
    { immediate: true },
  )

  watch(query, (q) => {
    if (!q.trim()) {
      results.value = []
      return
    }
    let regex: RegExp
    try {
      regex = new RegExp(q, 'i')
    } catch {
      results.value = []
      return
    }

    const kos: SearchCandidate[] = []
    const lipids: SearchCandidate[] = []
    const genes: SearchCandidate[] = []

    for (const c of allCandidates) {
      if (!regex.test(c.name)) continue
      if (c.type === 'ko') kos.push(c)
      else if (c.type === 'lipid') lipids.push(c)
      else genes.push(c)
      if (kos.length + lipids.length + genes.length >= MAX_RESULTS) break
    }

    results.value = [...kos, ...lipids, ...genes].slice(0, MAX_RESULTS)
  })

  return { query, results }
}
