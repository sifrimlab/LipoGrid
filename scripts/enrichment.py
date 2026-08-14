"""
Systematic GO / pathway enrichment for one or many gene sets.

Two backends are supported:
  - Enrichr  (via gseapy)     -> human/mouse, huge library catalogue
  - g:Profiler (via gprofiler-official) -> many organisms, well-curated

Install:
    pip install gseapy gprofiler-official pandas tqdm

Typical use:
    from enrichment import enrich_enrichr, enrich_gprofiler, batch_enrich

    # Single set, multiple libraries via Enrichr
    res = enrich_enrichr(
        genes=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2", "MDM2", "CDKN1A"],
        libraries=["GO_Biological_Process_2023",
                   "KEGG_2021_Human",
                   "Reactome_2022",
                   "MSigDB_Hallmark_2020"],
        outdir="enrichr_out",
    )

    # Single set via g:Profiler (uses a background of all annotated genes)
    res2 = enrich_gprofiler(
        genes=["TP53", "BRCA1", "BRCA2", "ATM", "CHEK2"],
        organism="hsapiens",
        sources=["GO:BP", "GO:MF", "GO:CC", "KEGG", "REAC", "WP"],
    )

    # Many gene sets at once (e.g. clusters from scRNA-seq)
    gene_sets = {
        "cluster_1": ["TP53", "BRCA1", "BRCA2", ...],
        "cluster_2": ["MYC", "MAX", "MXI1", ...],
    }
    summary = batch_enrich(gene_sets, backend="gprofiler", organism="hsapiens")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union

import pandas as pd


# 0. Direct Enrichr library fetcher (bypasses gseapy's flaky GMT parser)
_ENRICHR_HOSTS = {
    # Most "*_Human" / "*_Mouse" libraries live on the main Enrichr host.
    "human": "https://maayanlab.cloud/Enrichr",
    "mouse": "https://maayanlab.cloud/Enrichr",
    # Non-mammal species use modEnrichr sub-sites:
    "fly":   "https://maayanlab.cloud/FlyEnrichr",
    "worm":  "https://maayanlab.cloud/WormEnrichr",
    "yeast": "https://maayanlab.cloud/YeastEnrichr",
    "fish":  "https://maayanlab.cloud/FishEnrichr",
}


def fetch_enrichr_library(name: str, organism: str = "human",
                          timeout: int = 60) -> Dict[str, List[str]]:
    """
    Download an Enrichr gene-set library directly via HTTP.
    Returns {term: [genes]}. Avoids the bytes/str bug in some gseapy versions.
    """
    import urllib.request

    host = _ENRICHR_HOSTS.get(organism.lower(), _ENRICHR_HOSTS["human"])
    url = f"{host}/geneSetLibrary?mode=text&libraryName={name}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:                                              # noqa: BLE001
        raise RuntimeError(f"Could not download '{name}' from {url}: {e}") from e

    out: Dict[str, List[str]] = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        term = parts[0]
        # Enrichr lines look like:  "term\t\tgeneA\tgeneB,1.0\tgeneC..."
        # The 2nd field is an (often empty) description; gene cells may carry
        # a ",weight" suffix that we strip.
        genes = [g.split(",")[0].strip() for g in parts[1:] if g.strip()]
        if genes:
            out[term] = genes
    if not out:
        raise RuntimeError(f"Library '{name}' came back empty — check the name.")
    return out


# 1. Enrichr backend (gseapy)
def enrich_enrichr(
    genes: Sequence[str],
    libraries: Sequence[str] = (
        "GO_Biological_Process_2023",
        "GO_Molecular_Function_2023",
        "GO_Cellular_Component_2023",
        "KEGG_2021_Human",
        "Reactome_2022",
        "WikiPathway_2023_Human",
        "MSigDB_Hallmark_2020",
    ),
    organism: str = "human",          # 'human', 'mouse', 'fly', 'yeast', 'worm', 'fish'
    outdir: Optional[str] = None,
    cutoff: float = 0.05,             # adjusted-p cutoff for the bar plots gseapy makes
) -> pd.DataFrame:
    """
    Run Enrichr enrichment for one gene list against several libraries.
    Returns a long-format DataFrame with one row per term and a 'Library' column.
    """
    import gseapy as gp

    genes = [str(g).strip() for g in genes if str(g).strip()]
    if not genes:
        raise ValueError("Empty gene list.")

    out = Path(outdir) if outdir else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)

    enr = gp.enrichr(
        gene_list=list(genes),
        gene_sets=list(libraries),
        organism=organism,
        outdir=str(out) if out else None,
        cutoff=cutoff,
        no_plot=out is None,
    )
    df = enr.results.copy()
    # Standardise column names a bit
    df = df.rename(columns={"Gene_set": "Library"})
    df["n_input_genes"] = len(genes)
    return df.sort_values(["Library", "Adjusted P-value"]).reset_index(drop=True)


# 2. g:Profiler backend (gprofiler-official)
def enrich_gprofiler(
    genes: Sequence[str],
    organism: str = "hsapiens",
    sources: Sequence[str] = ("GO:BP", "GO:MF", "GO:CC", "KEGG", "REAC", "WP"),
    background: Optional[Sequence[str]] = None,
    user_threshold: float = 0.05,
    significance_threshold_method: str = "g_SCS",   # 'g_SCS' | 'fdr' | 'bonferroni'
    no_iea: bool = False,                            # drop electronic GO annotations
    ordered: bool = False,                           # True if `genes` is ranked
) -> pd.DataFrame:
    """
    Run g:Profiler (g:GOSt) enrichment.
    Returns a DataFrame with one row per significant term across requested sources.
    """
    from gprofiler import GProfiler

    genes = [str(g).strip() for g in genes if str(g).strip()]
    if not genes:
        raise ValueError("Empty gene list.")

    gp = GProfiler(return_dataframe=True)
    df = gp.profile(
        organism=organism,
        query=list(genes),
        sources=list(sources),
        user_threshold=user_threshold,
        significance_threshold_method=significance_threshold_method,
        background=list(background) if background else None,
        no_iea=no_iea,
        ordered=ordered,
        no_evidences=False,
    )
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df["n_input_genes"] = len(genes)
    return df.sort_values(["source", "p_value"]).reset_index(drop=True)


# 2b. Preranked GSEA (gseapy.prerank) — for *ranked* gene lists
def gsea_prerank(
    ranking: Union[pd.Series, pd.DataFrame],
    gene_sets: Union[str, Sequence[str], Dict[str, Sequence[str]]] = (
        "GO_Biological_Process_2023",
        "KEGG_2021_Human",
        "Reactome_2022",
        "MSigDB_Hallmark_2020",
    ),
    organism: str = "human",
    outdir: Optional[str] = None,
    min_size: int = 5,
    max_size: int = 500,
    permutation_num: int = 1000,
    seed: int = 0,
    threads: int = 4,
    return_run: bool = False,
):
    """
    Preranked GSEA on a *ranked* gene list (e.g. log2FC, t-stat, signed -log10(p)).

    Parameters
    ----------
    ranking : pd.Series  (index=gene, value=score)   OR
              pd.DataFrame with two columns [gene, score]
        Rows are sorted internally (descending). Duplicates are aggregated by mean.
    gene_sets : str | list[str] | dict
        Enrichr library name(s), a path to a local .gmt, or a {set: [genes]} dict.
        Lists of library names are pre-fetched to dicts to avoid a known
        gseapy GMT-parser bug ("a bytes-like object is required, not 'str'").
    organism : 'human' | 'mouse' | ... (only used when fetching Enrichr libraries).
    min_size, max_size : pathway-size filters (standard GSEA defaults are 15, 500).
    permutation_num : number of gene-set permutations for empirical p-values.
    return_run : if True, also return the underlying gseapy Prerank object
                 (useful for `gp.gseaplot(rank_metric=run.ranking, **run.results[term])`).

    Returns
    -------
    DataFrame (or (DataFrame, Prerank) if return_run=True).
    Columns include: Term, ES, NES, NOM p-val, FDR q-val, Tag %, Lead_genes.
    Sorted by FDR ascending then |NES| descending.
    """
    import gseapy as gp

    # 1. Normalise the ranking to a clean (gene -> score) Series
    if isinstance(ranking, pd.DataFrame):
        if ranking.shape[1] < 2:
            raise ValueError("DataFrame ranking must have at least 2 columns: gene, score.")
        s = pd.Series(
            pd.to_numeric(ranking.iloc[:, 1], errors="coerce").values,
            index=ranking.iloc[:, 0].astype(str).values,
        )
    elif isinstance(ranking, pd.Series):
        s = ranking.copy()
        s.index = s.index.astype(str)
        s = pd.to_numeric(s, errors="coerce")
    else:
        raise TypeError("ranking must be a pandas Series or DataFrame.")

    s = s.dropna()
    s = s.groupby(level=0).mean()              # collapse duplicate symbols
    s = s.sort_values(ascending=False)
    if s.empty:
        raise ValueError("Empty ranking after cleaning.")

    # 2. Resolve gene_sets to a dict to dodge the gseapy parser bug
    if isinstance(gene_sets, dict):
        gs = gene_sets
    elif isinstance(gene_sets, str) and gene_sets.lower().endswith(".gmt"):
        gs = gene_sets                          # local GMT path is fine
    else:
        names = [gene_sets] if isinstance(gene_sets, str) else list(gene_sets)
        gs = {}
        for lib in names:
            lib_dict = fetch_enrichr_library(lib, organism=organism)
            # Prefix term names with the library to avoid collisions across libs
            for term, genes in lib_dict.items():
                gs[f"{lib}|{term}"] = list(genes)
        if not gs:
            raise RuntimeError("No gene sets fetched.")

    # 3. Run GSEA
    out = Path(outdir) if outdir else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)

    pre = gp.prerank(
        rnk=s,
        gene_sets=gs,
        outdir=str(out) if out else None,
        min_size=min_size,
        max_size=max_size,
        permutation_num=permutation_num,
        seed=seed,
        threads=threads,
        no_plot=out is None,
        verbose=False,
    )

    df = pre.res2d.copy()
    # Split the "lib|term" prefix back out into its own column when we made it
    if df["Term"].astype(str).str.contains(r"\|", regex=True).all():
        split = df["Term"].astype(str).str.split("|", n=1, expand=True)
        df.insert(0, "Library", split[0])
        df["Term"] = split[1]
    df["abs_NES"] = df["NES"].abs()
    df = df.sort_values(["FDR q-val", "abs_NES"], ascending=[True, False]).drop(columns="abs_NES")
    df["n_input_genes"] = len(s)
    df = df.reset_index(drop=True)

    return (df, pre) if return_run else df


# 3. Batch driver — many gene sets at once
def batch_enrich(
    gene_sets: Dict[str, Sequence[str]],
    backend: str = "gprofiler",
    outdir: Optional[str] = "enrichment_out",
    top_n: Optional[int] = 20,
    **kwargs,
) -> pd.DataFrame:
    """
    Run enrichment on a dict of {set_name: [genes...]} and return a single
    concatenated DataFrame with a 'set' column. Per-set CSVs + a combined
    summary are written to `outdir`.
    """
    from tqdm import tqdm

    if backend not in ("enrichr", "gprofiler"):
        raise ValueError("backend must be 'enrichr' or 'gprofiler'")

    out = Path(outdir) if outdir else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)

    rows: List[pd.DataFrame] = []
    for name, genes in tqdm(gene_sets.items(), desc=f"{backend} enrichment"):
        try:
            if backend == "enrichr":
                sub_out = (out / name) if out else None
                df = enrich_enrichr(genes, outdir=str(sub_out) if sub_out else None, **kwargs)
                pcol = "Adjusted P-value"
            else:
                df = enrich_gprofiler(genes, **kwargs)
                pcol = "p_value"
        except Exception as e:                                  # noqa: BLE001
            print(f"[warn] {name}: {e}")
            continue

        if df is None or len(df) == 0:
            continue
        df.insert(0, "set", name)
        if out is not None:
            df.to_csv(out / f"{name}.csv", index=False)
        if top_n:
            df = df.sort_values(pcol).groupby(
                "Library" if backend == "enrichr" else "source",
                group_keys=False,
            ).head(top_n)
        rows.append(df)

    combined = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if out is not None and len(combined):
        combined.to_csv(out / "all_sets_topterms.csv", index=False)
    return combined


# 4. Convenience: read gene sets from a TSV / GMT / folder of txts
def load_gene_sets(path: Union[str, os.PathLike]) -> Dict[str, List[str]]:
    """
    Load gene sets from:
      - a .gmt file (one set per line: name<TAB>desc<TAB>gene1<TAB>gene2...)
      - a 2-column TSV: set_name<TAB>gene
      - a directory of *.txt files (one gene per line, filename = set name)
    """
    p = Path(path)
    if p.is_dir():
        return {f.stem: [g.strip() for g in f.read_text().splitlines() if g.strip()]
                for f in p.glob("*.txt")}
    text = p.read_text()
    if p.suffix.lower() == ".gmt":
        sets = {}
        for line in text.splitlines():
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3:
                sets[parts[0]] = [g for g in parts[2:] if g]
        return sets
    # assume 2-col TSV
    df = pd.read_csv(p, sep="\t", header=None, names=["set", "gene"])
    return {s: g["gene"].dropna().astype(str).tolist() for s, g in df.groupby("set")}


# CLI
if __name__ == "__main__":
    import argparse, json, sys

    ap = argparse.ArgumentParser(description="Systematic GO/pathway enrichment.")
    ap.add_argument("input", help="GMT, 2-col TSV, dir of .txt, OR a single gene list (.txt)")
    ap.add_argument("--backend", choices=["enrichr", "gprofiler"], default="gprofiler")
    ap.add_argument("--organism", default="hsapiens",
                    help="hsapiens / mmusculus / ... for gprofiler; "
                         "human / mouse / ... for enrichr")
    ap.add_argument("--sources", nargs="*", default=None,
                    help="GO:BP GO:MF KEGG REAC WP HP TF MIRNA CORUM HPA  (gprofiler) "
                         "or Enrichr library names")
    ap.add_argument("--outdir", default="enrichment_out")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    p = Path(args.input)
    if p.is_file() and p.suffix.lower() == ".txt":
        # single gene list
        genes = [g.strip() for g in p.read_text().splitlines() if g.strip()]
        gene_sets = {p.stem: genes}
    else:
        gene_sets = load_gene_sets(p)
    print(f"Loaded {len(gene_sets)} gene set(s).", file=sys.stderr)

    kw = {"organism": args.organism}
    if args.sources:
        kw["sources" if args.backend == "gprofiler" else "libraries"] = args.sources

    df = batch_enrich(gene_sets, backend=args.backend,
                      outdir=args.outdir, top_n=args.top, **kw)
    print(f"Wrote {len(df)} rows to {args.outdir}/", file=sys.stderr)
    if len(df):
        print(df.head(20).to_csv(index=False))
