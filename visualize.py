"""
visualize.py
============
Draw flat Kripke structures with labels and highlight states satisfying a formula.
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional
from kripke import FlatKripkeStructure


def draw_flat_structure(
    flat: FlatKripkeStructure,
    formula_str: Optional[str] = None,
    title: str = "Flat Kripke Structure",
) -> None:
    """Create a network graph from the flat structure and display it."""
    G = nx.DiGraph()

    # labelling nodes with readable names
    for state in flat.states:
        label = _state_name(state)
        G.add_node(state, label=label)

    for s, t in flat.transitions:
        G.add_edge(s, t)

    # color nodes that satisfy the given formula
    node_colors = []
    for node in G.nodes():
        if formula_str and formula_str in flat.labeling.get(node, set()):
            node_colors.append("limegreen")
        else:
            node_colors.append("lightblue")

    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)
    labels = {node: G.nodes[node]["label"] for node in G.nodes()}

    plt.figure(figsize=(8, 5))
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowstyle="->")
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200)
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def _state_name(state) -> str:
    """Convert a flat state (str or tuple) to a readable string."""
    if isinstance(state, str):
        return state
    # tuple: (box, ...)
    return ".".join(str(x) for x in state)