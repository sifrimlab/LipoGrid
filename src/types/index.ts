export type EntityType = 'lipid' | 'gene' | 'ko'

export interface SearchCandidate {
  name: string
  type: EntityType
}

export interface VolcanoPoint {
  name: string
  log2FC: number
  pvalue: number
}

export interface KOEntry {
  log2FC: number
  pvalue: number
}

export interface ParsedData {
  lipids: Map<string, Map<string, KOEntry>>
  genes: Map<string, Map<string, KOEntry>>
  koNames: string[]
}
