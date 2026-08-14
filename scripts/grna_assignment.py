"""Assign each cell to its most likely gRNA based on per-cell gRNA UMI/count matrix."""

from __future__ import annotations

import pandas as pd


def assign_grna_to_cell(
    df: pd.DataFrame,
    min_count: int = 8,
    multi_ratio: float = 1.5,
    min_fraction: float = 0.25,
) -> dict:
    """
    For each cell (row), call the dominant gRNA (column).

    df : rows = cells, columns = gRNAs, values = counts.
    min_count : counts below this are called 'low_count'.
    multi_ratio : if the top count is less than multi_ratio * the 2nd-highest
        count, the cell is called 'multiple_gRNAs' (likely double integration
        or a doublet).
    min_fraction : the top gRNA must make up at least this fraction of the
        cell's total counts, otherwise the cell is called 'ambiguous'.

    Returns {cell: gRNA_name | 'no_gRNA' | 'low_count' | 'multiple_gRNAs' | 'ambiguous'}.
    """
    assignment = {}
    for cell in df.index:
        row = df.loc[cell]
        max_grna = row.idxmax()
        max_count = row.max()
        second_count = row.nlargest(2).iloc[-1]

        if max_count == 0:
            assignment[cell] = "no_gRNA"
        elif max_count < min_count:
            assignment[cell] = "low_count"
        elif max_count < multi_ratio * second_count:
            assignment[cell] = "multiple_gRNAs"
        elif max_count / row.sum() > min_fraction:
            assignment[cell] = max_grna
        else:
            assignment[cell] = "ambiguous"
    return assignment
