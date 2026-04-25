"""
visualize.py
============
Draw flat Kripke structures and save them as publication‑quality PDF figures.
"""

import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

from kripke import FlatKripkeStructure


# ── aesthetic settings ──────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})


def draw_flat_structure(
    flat: FlatKripkeStructure,
    formula_str: Optional[str] = None,
    title: str = "Flat Kripke Structure",
    output_path: Optional[str] = None,   # if None -> use "viz/flat_structure.pdf"
    show: bool = False,                   # set True to display interactively
) -> None:
    """
    Create a network graph from the flat structure, save it as a PDF,
    and optionally display it.

    Parameters
    ----------
    flat : FlatKripkeStructure
        The expanded flat Kripke structure.
    formula_str : str, optional
        A formula string to highlight nodes that satisfy it (green).
    title : str
        Title of the figure.
    output_path : str, optional
        File path for the saved PDF. If not given, defaults to ``viz/flat_structure.pdf``.
    show : bool
        If True, open a plot window (default: False).
    """
    G = nx.DiGraph()

    # Add nodes with readable labels
    for state in flat.states:
        label = _state_name(state)
        G.add_node(state, label=label)

    for s, t in flat.transitions:
        G.add_edge(s, t)

    # Node colours
    node_colors = []
    for node in G.nodes():
        if formula_str and formula_str in flat.labeling.get(node, set()):
            node_colors.append("#4CAF50")   # satisfying → green
        else:
            node_colors.append("#90CAF9")   # others → soft blue

    # Layout
    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)
    labels = {node: G.nodes[node]["label"] for node in G.nodes()}

    fig, ax = plt.subplots(figsize=(8, 5))
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True,
                           arrowstyle="->", ax=ax, width=0.8)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200,
                           edgecolors="black", linewidths=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)

    ax.set_title(title, fontweight="bold", pad=20)
    ax.axis("off")
    plt.tight_layout()

    # Save to PDF
    if output_path is None:
        output_path = "viz/flat_structure.pdf"

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)   # create viz/ if needed
    fig.savefig(out_file, dpi=300, bbox_inches="tight", format="pdf")
    print(f"Saved figure to {out_file.resolve()}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def _state_name(state) -> str:
    """Convert a flat state (str or tuple) to a readable string."""
    if isinstance(state, str):
        return state
    # tuple: (box, {inner states})
    return ".".join(str(x) for x in state)