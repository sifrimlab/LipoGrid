"""Publication-ready volcano plots for gene-KO vs. measured-feature results tables.

Used for CROP-seq (rows=gene, columns=KO target) and MSI/bulk lipidomics
(rows=lipid, columns=KO target) results tables alike — both share the same
'{target}_log2FC' / '{target}_pvalue' wide layout.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Divider, Size
from adjustText import adjust_text

from style import DEFAULT_FONT_PATH


def _register_font(font_path):
    """Register a font file with matplotlib and return its family name."""
    if not font_path:
        return None
    fm.fontManager.addfont(font_path)
    return fm.FontProperties(fname=font_path).get_name()


def _set_volcano_style(font_path):
    registered = _register_font(font_path)
    sans_list = ([registered] if registered else []) + \
        ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": sans_list,
        "font.weight": "normal",
        "font.size": 8,
        "axes.titlesize": 12,
        "axes.titleweight": "normal",
        "axes.labelsize": 12,
        "axes.labelweight": "normal",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 1,
        "lines.linewidth": 1,
        "grid.linewidth": 1,
        "pdf.fonttype": 42,
    })


def _fixed_box_axes(box_px, dpi):
    box_in = box_px / dpi
    fig = plt.figure(figsize=(box_in + 2.5, box_in + 2.0), dpi=dpi)
    h = [Size.Fixed(1.5), Size.Fixed(box_in)]
    v = [Size.Fixed(1.0), Size.Fixed(box_in)]
    divider = Divider(fig, (0, 0, 1, 1), h, v, aspect=False)
    ax = fig.add_axes(divider.get_position(), axes_locator=divider.new_locator(nx=1, ny=1))
    return fig, ax


def plot_volcano(
    results_df,
    target,
    font_path=DEFAULT_FONT_PATH,
    pval_cap=1e-10,
    sig_threshold=0.01,
    box_px=300,
    dpi=100,
    dot_size=12,
    color_down="#005AB5",
    color_up="#DC3220",
    color_ns="lightgrey",
    save_dir="../data/lipogrid/pilot/analysis/internalnorm_finalfigs",
    save=True,
    show=True,
):
    """
    Volcano plot for one KO target: one point per row (gene or lipid) of
    `results_df`, using its '{target}_log2FC' / '{target}_pvalue' columns.
    """
    df = results_df.copy()
    df[f"{target}_pvalue"] = df[f"{target}_pvalue"].apply(lambda x: max(x, pval_cap))

    _set_volcano_style(font_path)
    fig, ax = _fixed_box_axes(box_px, dpi)

    sig_mask = df[f"{target}_pvalue"] < sig_threshold
    x = df[f"{target}_log2FC"]
    y = -np.log10(df[f"{target}_pvalue"])

    ax.scatter(x[~sig_mask], y[~sig_mask], c=color_ns, s=dot_size, rasterized=False, zorder=1)
    sig_colors = np.where(df.loc[sig_mask, f"{target}_log2FC"] < 0, color_down, color_up)
    ax.scatter(x[sig_mask], y[sig_mask], c=sig_colors, s=dot_size, rasterized=False, zorder=2)

    texts = [
        ax.text(row[f"{target}_log2FC"], -np.log10(row[f"{target}_pvalue"]), lipid,
                fontsize=8, color="black", ha="center", va="center")
        for lipid, row in df[sig_mask].iterrows()
    ]

    ax.axhline(y=-np.log10(sig_threshold), color="darkred", linestyle="--", linewidth=1,
               label=f"p-value = {sig_threshold}")
    ax.axvline(x=0, color="grey", linestyle="--", linewidth=1, label="Fold Change = 1")

    ax.set_title(f"Effect {target} knockout")
    ax.set_xlabel(f"Log$_2$({target} gRNA/intergenic gRNA)")
    ax.set_ylabel("-Log$_{10}$(p-value)")
    ax.grid(False)
    ax.tick_params(length=5, width=1)

    xabs = np.nanmax(np.abs(df[f"{target}_log2FC"]))
    ax.set_xlim(-xabs * 1.05, xabs * 1.05)
    ymax = float(np.nanmax(-np.log10(df[f"{target}_pvalue"])))
    ax.set_ylim(-0.05, ymax * 1.05)
    ax.margins(y=0)

    adjust_text(
        texts, arrowprops=dict(arrowstyle="-", color="gray", lw=1),
        expand_text=(1.3, 1.3), expand_points=(1.2, 1.2),
        force_text=0.3, force_points=0.3, force_pull=7,
        time_lim=10, min_arrow_len=15,
    )

    if save:
        fig.savefig(f"{save_dir}/volcano_plot_{target}_log2FC_pvalue.pdf", dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    return fig, ax


def plot_volcano_lipid(
    results_df,
    lipid,
    font_path=DEFAULT_FONT_PATH,
    pval_cap=1e-10,
    sig_threshold=0.01,
    box_px=300,
    dpi=100,
    dot_size=12,
    color_down="#005AB5",
    color_up="#DC3220",
    color_ns="lightgrey",
    save_dir="../data/lipogrid/pilot/analysis/internalnorm_finalfigs",
    save=True,
    show=True,
):
    """
    Volcano plot for one row (lipid) of `results_df`: one point per KO gene,
    read from that gene's '{gene}_log2FC' / '{gene}_pvalue' columns.
    """
    genes = [c.replace("_log2FC", "") for c in results_df.columns if c.endswith("_log2FC")]
    row = results_df.loc[lipid]
    plot_df = pd.DataFrame({
        "gene": genes,
        "log2FC": [row[f"{g}_log2FC"] for g in genes],
        "pvalue": [max(row[f"{g}_pvalue"], pval_cap) for g in genes],
    }).set_index("gene")

    _set_volcano_style(font_path)
    fig, ax = _fixed_box_axes(box_px, dpi)

    sig_mask = plot_df["pvalue"] < sig_threshold
    x = plot_df["log2FC"]
    y = -np.log10(plot_df["pvalue"])

    ax.scatter(x[~sig_mask], y[~sig_mask], c=color_ns, s=dot_size, rasterized=False, zorder=1)
    sig_colors = np.where(plot_df.loc[sig_mask, "log2FC"] < 0, color_down, color_up)
    ax.scatter(x[sig_mask], y[sig_mask], c=sig_colors, s=dot_size, rasterized=False, zorder=2)

    texts = [
        ax.text(r["log2FC"], -np.log10(r["pvalue"]), gene,
                fontsize=8, color="black", ha="center", va="center")
        for gene, r in plot_df[sig_mask].iterrows()
    ]

    ax.axhline(y=-np.log10(sig_threshold), color="darkred", linestyle="--", linewidth=1,
               label=f"p-value = {sig_threshold}")
    ax.axvline(x=0, color="grey", linestyle="--", linewidth=1, label="Fold Change = 1")

    ax.set_title(lipid)
    ax.set_xlabel("Log$_2$(gRNA/intergenic gRNA)")
    ax.set_ylabel("-Log$_{10}$(p-value)")
    ax.grid(False)
    ax.tick_params(length=5, width=1)

    xabs = np.nanmax(np.abs(plot_df["log2FC"]))
    ax.set_xlim(-xabs * 1.05, xabs * 1.05)
    ymax = float(np.nanmax(y))
    ax.set_ylim(-0.05, ymax * 1.05)
    ax.margins(y=0)

    adjust_text(
        texts, arrowprops=dict(arrowstyle="-", color="gray", lw=1),
        expand_text=(1.3, 1.3), expand_points=(1.2, 1.2),
        force_text=0.3, force_points=0.3, force_pull=7,
        time_lim=10, min_arrow_len=15,
    )

    if save:
        safe_lipid = lipid.replace("/", "_").replace(" ", "_")
        fig.savefig(f"{save_dir}/volcano_plot_{safe_lipid}_genes.pdf", dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    return fig, ax
