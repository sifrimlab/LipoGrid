"""Shared matplotlib styling for figures.

Two levels are used across the notebooks:
  - set_default_style()      : quick bold style for exploratory plots.
  - set_publication_style()  : Helvetica Neue (if available) + the
                                consistent look used for figures saved to PDF.
"""

from __future__ import annotations

import os
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

DEFAULT_FONT_PATH = "../data/fonts/HelveticaNeue_ttf/HelveticaNeue.ttf"


def set_default_style(font_size: int = 15) -> None:
    """Bold, larger-font default used for quick/exploratory plots."""
    plt.rcParams.update({
        "font.size": font_size,
        "font.weight": "bold",
        "axes.titleweight": "bold",
        "axes.labelweight": "bold",
    })


def set_publication_style(font_path: str = DEFAULT_FONT_PATH, **overrides) -> str | None:
    """Register Helvetica Neue (if present) and apply the shared publication rcParams.

    Falls back to Helvetica/Arial/DejaVu Sans if the font file isn't found, so
    this is safe to call on machines without the font installed.
    Returns the registered font family name (or None).
    """
    family = None
    if font_path and os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        family = fm.FontProperties(fname=font_path).get_name()

    style = {
        "font.family": "sans-serif",
        "font.sans-serif": ([family] if family else []) + ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.labelweight": "bold",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.linewidth": 1,
        "lines.linewidth": 1,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "pdf.fonttype": 42,
    }
    style.update(overrides)
    plt.rcParams.update(style)
    return family
