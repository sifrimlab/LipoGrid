"""
plot_term_vs_lipid with optional KO→target arrow overlay.

New parameters compared to the original function:

    ko_effect_df        : pd.DataFrame with downstream genes as index and
                          columns named '<KO>_log2FC', '<KO>_pvalue'
                          (e.g. your CROP_seq_log2FC_manw_pergeneKO_sameKOs.csv
                          loaded with index_col=0). If None, no arrows are
                          drawn and the function behaves like the original.
    ko_pval_cutoff      : significance threshold for drawing an arrow
                          (default 0.05; applied to the KO's *_pvalue column).
    ko_log2fc_min       : optional minimum |log2FC| to draw an arrow
                          (default 0.0 = include any non-zero effect that
                          passes the p-value cut).
    arrow_up_color      : color for upregulation arrows (log2FC > 0).
    arrow_down_color    : color for downregulation arrows (log2FC < 0).
    arrow_alpha         : transparency for arrows.
    arrow_lw            : line width for arrows.
    arrow_curve_rad     : curvature for reciprocal pairs (set 0 for straight).
    arrow_mutation_scale: arrowhead size (matplotlib FancyArrowPatch units).
    arrow_zorder        : z-order; arrows drawn below text labels by default.
    arrow_in_legend     : whether to add up/down entries to the legend.

Arrows are drawn only between genes that:
  - both appear as labeled (annotated) points on the plot,
  - are not the same gene (no self-loops),
  - have a significant KO→target effect at the given p-value cutoff,
  - have both a column entry (`{KO}_log2FC`, `{KO}_pvalue`) in ko_effect_df
    and a row entry for the target gene.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from adjustText import adjust_text


def _draw_ko_arrows(
    ax,
    labeled_genes,
    x_vis, y_vis,
    ko_effect_df,
    *,
    ko_pval_cutoff=0.05,
    ko_log2fc_min=0.0,
    log2fc_suffix="_log2FC",
    pval_suffix="_pvalue",
    up_color="#D62728",
    down_color="#1F77B4",
    alpha=0.6,
    lw=1.2,
    curve_rad=0.15,
    mutation_scale=14,
    zorder=3,
):
    """Draw KO→target arrows between labeled genes. Returns (n_up, n_down)."""
    if ko_effect_df is None or not labeled_genes:
        return 0, 0

    # Restrict to genes that have a position on the plot
    labeled = [g for g in labeled_genes if g in x_vis.index]
    if len(labeled) < 2:
        return 0, 0

    # Determine which labeled genes have a KO column block and which appear as
    # downstream rows in ko_effect_df.
    ko_cols = set(ko_effect_df.columns)
    has_ko_block = {
        g for g in labeled
        if f"{g}{log2fc_suffix}" in ko_cols and f"{g}{pval_suffix}" in ko_cols
    }
    targets_in_index = set(ko_effect_df.index) & set(labeled)

    # First pass: collect all (ko, target, log2fc) tuples that pass the cutoff
    edges = []
    for g_ko in has_ko_block:
        l2fc_col = f"{g_ko}{log2fc_suffix}"
        pval_col = f"{g_ko}{pval_suffix}"
        # Subset to labeled targets that are in the index
        candidates = list(targets_in_index - {g_ko})  # no self-loops
        if not candidates:
            continue
        sub = ko_effect_df.loc[candidates, [l2fc_col, pval_col]]
        sig = sub[
            sub[pval_col].notna()
            & (sub[pval_col] <= ko_pval_cutoff)
            & sub[l2fc_col].notna()
            & (sub[l2fc_col].abs() >= ko_log2fc_min)
        ]
        for tgt, row in sig.iterrows():
            edges.append((g_ko, tgt, float(row[l2fc_col])))

    if not edges:
        return 0, 0

    # If both A→B and B→A exist, curve them in opposite directions so the
    # arrows don't overlap.
    edge_set = {(a, b) for a, b, _ in edges}
    n_up = n_down = 0
    for g_ko, g_tgt, l2fc in edges:
        reciprocal = (g_tgt, g_ko) in edge_set
        # Stable rule: lexicographically smaller endpoint curves positive,
        # the other curves negative — guarantees opposite curvatures for the
        # two members of a reciprocal pair.
        if reciprocal:
            rad = curve_rad if g_ko < g_tgt else -curve_rad
        else:
            rad = 0.0

        color = up_color if l2fc > 0 else down_color
        arrow = FancyArrowPatch(
            (x_vis[g_ko],  y_vis[g_ko]),
            (x_vis[g_tgt], y_vis[g_tgt]),
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            color=color,
            alpha=alpha,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=8, shrinkB=8,
            zorder=zorder,
        )
        ax.add_patch(arrow)
        if l2fc > 0:
            n_up += 1
        else:
            n_down += 1
    return n_up, n_down


def plot_term_vs_lipid(
    nes_df, lipid_df, term, lipid,
    fdr_df=None, fdr_cutoff=0.25,
    nes_cutoff=None,
    lipid_pval_df=None, lipid_pval_cutoff=0.05,
    annotate_top_n=20, annotate_genes=None,
    show_nonsig=False,
    color_both="#8315BE",
    color_fdr_only="#1C57E2",
    color_lipid_only="#E2970C",
    color_neither="lightgray",
    label_fontsize=16, label_color="blue", forced_color="red",
    legend=True,
    figsize=(10, 10), ax=None,
    # NEW: KO→target arrow overlay
    ko_effect_df=None,
    ko_pval_cutoff=0.05,
    ko_log2fc_min=0.0,
    ko_log2fc_suffix="_log2FC",
    ko_pval_suffix="_pvalue",
    arrow_up_color="#D62728",
    arrow_down_color="#1F77B4",
    arrow_alpha=0.6,
    arrow_lw=1.2,
    arrow_curve_rad=0.15,
    arrow_mutation_scale=14,
    arrow_zorder=3,
    arrow_in_legend=True,
    # NEW: forced extra genes (shown regardless of cutoffs)
    extra_genes=None,
    extra_genes_color="gray",
):
    """
    Per-gene scatter of one pathway's NES vs one lipid's value.

    Term-significance axis:
      - nes_cutoff : if set, genes are called significant when |NES| >= nes_cutoff
                     (keeps BOTH positive and negative NES). Takes precedence over
                     fdr_df/fdr_cutoff and does not require an FDR matrix.
      - fdr_df/fdr_cutoff : used only when nes_cutoff is None (original behaviour).

    See module docstring for the ko_effect_df / arrow_* parameters.
    """
    # existence checks
    if term not in nes_df.index:
        raise KeyError(f"{term!r} not in nes_df.index")
    if lipid not in lipid_df.index:
        raise KeyError(f"{lipid!r} not in lipid_df.index")

    common = nes_df.columns.intersection(lipid_df.columns)
    # FDR is only the active term-criterion when nes_cutoff is not set
    if fdr_df is not None and nes_cutoff is None:
        if term not in fdr_df.index:
            raise KeyError(f"{term!r} not in fdr_df.index")
        common = common.intersection(fdr_df.columns)
    if lipid_pval_df is not None:
        if lipid not in lipid_pval_df.index:
            raise KeyError(f"{lipid!r} not in lipid_pval_df.index")
        common = common.intersection(lipid_pval_df.columns)
    if len(common) == 0:
        raise ValueError("No shared gene columns between the input DataFrames")

    # pull values
    y = nes_df.loc[term, common]
    x = lipid_df.loc[lipid, common]
    keep = x.notna() & y.notna()

    # term-significance axis: |NES| threshold (takes precedence) or FDR
    # nes_cutoff keeps BOTH positive and negative NES (absolute value).
    term_pass = pd.Series(True, index=common)
    term_thr_provided = (nes_cutoff is not None) or (fdr_df is not None)
    if nes_cutoff is not None:
        term_pass = y.notna() & (y.abs() >= nes_cutoff)
        term_pass_label = f"|NES| ≥ {nes_cutoff}"
        term_fail_label = f"|NES| < {nes_cutoff}"
    elif fdr_df is not None:
        fdr = fdr_df.loc[term, common]
        term_pass = fdr.notna() & (fdr <= fdr_cutoff)
        term_pass_label = f"NES FDR ≤ {fdr_cutoff}"
        term_fail_label = f"NES FDR > {fdr_cutoff}"

    lipid_pass = pd.Series(True, index=common)
    if lipid_pval_df is not None:
        lp = lipid_pval_df.loc[lipid, common]
        lipid_pass = lp.notna() & (lp <= lipid_pval_cutoff)

    # categorize
    both_provided = term_thr_provided and (lipid_pval_df is not None)
    if both_provided:
        cats = [
            (keep & ~term_pass & ~lipid_pass, color_neither,    "neither"),
            (keep &  term_pass & ~lipid_pass, color_fdr_only,   term_pass_label),
            (keep & ~term_pass &  lipid_pass, color_lipid_only, f"lipid p ≤ {lipid_pval_cutoff}"),
            (keep &  term_pass &  lipid_pass, color_both,       "both thresholds"),
        ]
    elif term_thr_provided:
        cats = [
            (keep & ~term_pass, color_neither,  term_fail_label),
            (keep &  term_pass, color_fdr_only, term_pass_label),
        ]
    elif lipid_pval_df is not None:
        cats = [
            (keep & ~lipid_pass, color_neither,    f"lipid p > {lipid_pval_cutoff}"),
            (keep &  lipid_pass, color_lipid_only, f"lipid p ≤ {lipid_pval_cutoff}"),
        ]
    else:
        cats = [(keep, color_fdr_only, None)]

    # Hide the "fail" / "neither" category unless show_nonsig is True
    visible_mask = pd.Series(False, index=common)
    drawn_cats = []
    for mask, color, label in cats:
        if color == color_neither and not show_nonsig:
            continue
        drawn_cats.append((mask, color, label))
        visible_mask = visible_mask | mask

    # gene → category color lookup (later category wins)
    gene_to_color = {}
    for mask, color, _label in drawn_cats:
        for g in mask[mask].index:
            gene_to_color[g] = color

    # plot
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    for mask, color, label in drawn_cats:
        if mask.any():
            ax.scatter(x[mask], y[mask],
                       s=25, alpha=0.75,
                       edgecolor="black", linewidth=0.3,
                       color=color, label=label, zorder=2)

    # decide which genes to label (top-N + forced)
    x_vis = x[visible_mask]
    y_vis = y[visible_mask]

    # extra genes: always shown, grey if they fail all cutoffs
    extra_set = set(extra_genes or []) & set(keep[keep].index)
    if extra_set:
        extra_nonsig = {g for g in extra_set if g not in visible_mask.index[visible_mask]}
        if extra_nonsig:
            em = list(extra_nonsig)
            ax.scatter(x[em], y[em],
                       s=25, alpha=0.75,
                       edgecolor="black", linewidth=0.3,
                       color=extra_genes_color, zorder=2)
            x_vis = pd.concat([x_vis, x[em]])
            y_vis = pd.concat([y_vis, y[em]])
            for g in extra_nonsig:
                gene_to_color[g] = extra_genes_color

    label_set = set()
    if annotate_top_n and len(x_vis) > 0:
        mag = (x_vis - x_vis.mean()).abs() + (y_vis - y_vis.mean()).abs()
        label_set.update(mag.nlargest(annotate_top_n).index)
    forced = set(annotate_genes or [])
    label_set.update(forced)
    label_set.update(extra_set)

    # KO→target arrow overlay
    n_up, n_down = _draw_ko_arrows(
        ax,
        labeled_genes=label_set,
        x_vis=x_vis, y_vis=y_vis,
        ko_effect_df=ko_effect_df,
        ko_pval_cutoff=ko_pval_cutoff,
        ko_log2fc_min=ko_log2fc_min,
        log2fc_suffix=ko_log2fc_suffix,
        pval_suffix=ko_pval_suffix,
        up_color=arrow_up_color,
        down_color=arrow_down_color,
        alpha=arrow_alpha,
        lw=arrow_lw,
        curve_rad=arrow_curve_rad,
        mutation_scale=arrow_mutation_scale,
        zorder=arrow_zorder,
    )

    # text labels (placed on top of arrows)
    texts = []
    for g in label_set:
        if g not in x_vis.index:
            continue
        if g in forced:
            c = forced_color
        else:
            c = gene_to_color.get(g, label_color)
        texts.append(
            ax.text(x_vis[g], y_vis[g], g,
                    fontsize=label_fontsize, fontweight="bold",
                    color=c, ha="center", va="center",
                    zorder=arrow_zorder + 1)
        )

    if texts:
        adjust_text(
            texts, ax=ax,
            arrowprops=dict(arrowstyle="-", color="gray", lw=1),
            expand_text=(1.3, 1.3),
            expand_points=(1.3, 1.3),
            force_text=0.3,
            force_points=0.3,
            force_pull=10,
            time_lim=12,
            min_arrow_len=18,
        )

    ax.axhline(0, color="black", linestyle="--", linewidth=0.5)
    ax.axvline(0, color="black", linestyle="--", linewidth=0.5)
    ax.set_xlabel(f"{lipid} log2FC over intergenic", fontweight="bold", size=label_fontsize * 1.1)
    ax.set_ylabel(f"{term}  (NES)", fontweight="bold", size=label_fontsize * 1.1)

    # legend
    if legend and (term_thr_provided or lipid_pval_df is not None
                   or (arrow_in_legend and (n_up or n_down))):
        # category entries (text-only, colored)
        legend_entries = [(color, label) for mask, color, label in drawn_cats
                          if label is not None]

        # Pick a location, biased to the middle of the y-axis (unchanged)
        legend_loc = "best"
        if len(x_vis) > 0:
            x_lo, x_hi = x_vis.min(), x_vis.max()
            y_lo, y_hi = y_vis.min(), y_vis.max()
            x_mid = 0.5 * (x_lo + x_hi)
            y_band_lo = y_lo + (y_hi - y_lo) * 0.35
            y_band_hi = y_lo + (y_hi - y_lo) * 0.65
            in_mid_y = (y_vis >= y_band_lo) & (y_vis <= y_band_hi)
            left_count  = int((in_mid_y & (x_vis <  x_mid)).sum())
            right_count = int((in_mid_y & (x_vis >= x_mid)).sum())
            threshold = max(2, int(len(x_vis) * 0.04))
            if min(left_count, right_count) <= threshold:
                legend_loc = ("center left" if left_count <= right_count
                              else "center right")

        # Build mixed handles: text-only for category labels, line+arrow for KO arrows
        handles = []
        text_colors = []
        for col, lab in legend_entries:
            handles.append(Line2D([], [], marker="", linestyle="", label=lab))
            text_colors.append(col)
        if arrow_in_legend and (n_up or n_down):
            if n_up:
                handles.append(Line2D([0], [0], color=arrow_up_color,
                                      lw=arrow_lw + 0.5,
                                      label=f"KO → upregulates ({n_up})"))
                text_colors.append(arrow_up_color)
            if n_down:
                handles.append(Line2D([0], [0], color=arrow_down_color,
                                      lw=arrow_lw + 0.5,
                                      label=f"KO → downregulates ({n_down})"))
                text_colors.append(arrow_down_color)

        leg = ax.legend(
            handles=handles,
            frameon=False, loc=legend_loc,
            fontsize=label_fontsize * 0.9,
            handlelength=1.5, handletextpad=0.6,
        )
        # Color every legend entry's text in its plotted color, including the
        # KO arrow entries.
        for text, col in zip(leg.get_texts(), text_colors):
            text.set_color(col)
            text.set_fontweight("bold")

    fig.tight_layout()
    return fig, ax