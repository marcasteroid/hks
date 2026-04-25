"""
ctl/kripke.py
=============
Data structures for flat and hierarchical Kripke structures.

Flat Kripke structure
---------------------
  M = (W, in, R, L)
  where W = states, in = initial state,
        R ⊆ W × W = transition relation,
        L : W → 2^AP = labelling function.

Hierarchical Kripke structure (single-exit case)
-------------------------------------------------
  K = ⟨K₁, K₂, …, Kₙ⟩
  Each Kᵢ = ⟨Nᵢ, Bᵢ, inᵢ, outᵢ, Xᵢ, Yᵢ, Eᵢ⟩

Edge types in Eᵢ
----------------
  (NodeId, NodeId)              regular state transition
  (NodeId, BoxId)               node → box (enter nested structure)
  ((BoxId, NodeId), NodeId)     box-exit → node  (return to parent)
  ((BoxId, NodeId), BoxId)      box-exit → box   (chain into next box)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# ── type aliases ──────────────────────────────────────────────────────────────
NodeId = str
BoxId  = str
Label  = str

# An edge source is either a plain node/box id OR a (box, exit-node) pair.
EdgeSrc  = Union[NodeId, Tuple[BoxId, NodeId]]
EdgeTgt  = Union[NodeId, BoxId]
Edge     = Tuple[EdgeSrc, EdgeTgt]


# ─────────────────────────────────────────────────────────────────────────────
# Substructure  Kᵢ
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Substructure:
    """One layer of a hierarchical Kripke structure.

    Parameters
    ----------
    index    : 1-based position in the parent HierarchicalKripkeStructure.
    nodes    : Nᵢ — ordinary states.
    boxes    : Bᵢ — references to nested substructures.
    entry    : inᵢ — designated starting node.
    exit     : outᵢ — single exit node (single-exit case).
    labeling : Xᵢ : Nᵢ → 2^AP — atomic-proposition and formula labels.
    mapping  : Yᵢ : Bᵢ → {i+1,…,n} — box-to-substructure index mapping.
    edges    : Eᵢ — transition relation (see module docstring for edge types).
    """

    index:    int
    nodes:    Set[NodeId]
    boxes:    Set[BoxId]
    entry:    NodeId
    exit:     NodeId
    labeling: Dict[NodeId, Set[Label]]
    mapping:  Dict[BoxId, int]
    edges:    Set[Edge]

    # ── validation ────────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        assert self.entry in self.nodes, \
            f"K{self.index}: entry '{self.entry}' not in nodes {self.nodes}"
        assert self.exit in self.nodes, \
            f"K{self.index}: exit '{self.exit}' not in nodes {self.nodes}"
        # Ensure every node has an entry (possibly empty) in labeling
        for n in self.nodes:
            self.labeling.setdefault(n, set())

    # ── accessors ─────────────────────────────────────────────────────────────

    def is_node(self, name: str) -> bool:
        return name in self.nodes

    def is_box(self, name: str) -> bool:
        return name in self.boxes

    def get_labels(self, node: NodeId) -> Set[Label]:
        return self.labeling.get(node, set())

    def add_label(self, node: NodeId, label: Label) -> None:
        self.labeling.setdefault(node, set()).add(label)

    def successors(self, src: EdgeSrc) -> List[EdgeTgt]:
        """All immediate successors of *src* in Eᵢ."""
        return [tgt for (s, tgt) in self.edges if s == src]

    # ── copying ───────────────────────────────────────────────────────────────

    def copy(self) -> "Substructure":
        """Deep copy preserving all fields."""
        return Substructure(
            index    = self.index,
            nodes    = set(self.nodes),
            boxes    = set(self.boxes),
            entry    = self.entry,
            exit     = self.exit,
            labeling = {n: set(lbls) for n, lbls in self.labeling.items()},
            mapping  = dict(self.mapping),
            edges    = set(self.edges),
        )

    def __repr__(self) -> str:
        return (
            f"K{self.index}(nodes={sorted(self.nodes)}, "
            f"boxes={sorted(self.boxes)}, "
            f"entry={self.entry!r}, exit={self.exit!r})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Hierarchical Kripke structure  K
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HierarchicalKripkeStructure:
    """K = ⟨K₁, K₂, …, Kₙ⟩

    Substructures are identified by their 1-based ``index`` field.
    K₁ is the outermost (top-level) structure.
    """

    substructures: List[Substructure]

    # ── accessors ─────────────────────────────────────────────────────────────

    def get(self, index: int) -> Substructure:
        """Return the substructure with the given 1-based index (raises KeyError)."""
        for ki in self.substructures:
            if ki.index == index:
                return ki
        raise KeyError(f"No substructure with index {index}")

    def index_map(self) -> Dict[int, Substructure]:
        return {ki.index: ki for ki in self.substructures}

    def top_level(self) -> Substructure:
        """Return K₁ (the outermost structure)."""
        return min(self.substructures, key=lambda ki: ki.index)

    def __len__(self) -> int:
        return len(self.substructures)

    def __iter__(self):
        return iter(sorted(self.substructures, key=lambda ki: ki.index))

    def __repr__(self) -> str:
        names = [f"K{ki.index}" for ki in sorted(self.substructures, key=lambda k: k.index)]
        return f"HKS({', '.join(names)})"


# ─────────────────────────────────────────────────────────────────────────────
# Flat Kripke structure  M
# ─────────────────────────────────────────────────────────────────────────────

# A flat state can be a plain string (top-level node) or a nested tuple
# (box_id, inner_state) to capture context.
FlatState = Any


@dataclass
class FlatKripkeStructure:
    """M = ⟨W, in, R, L⟩

    Produced by recursively expanding a HierarchicalKripkeStructure.
    """

    states:      List[FlatState]
    initial:     FlatState
    transitions: Set[Tuple[FlatState, FlatState]]
    labeling:    Dict[FlatState, Set[Label]]

    # ── accessors ─────────────────────────────────────────────────────────────

    def successors(self, state: FlatState) -> List[FlatState]:
        return [t for (s, t) in self.transitions if s == state]

    def predecessors(self, state: FlatState) -> List[FlatState]:
        return [s for (s, t) in self.transitions if t == state]

    def get_labels(self, state: FlatState) -> Set[Label]:
        return self.labeling.get(state, set())

    def add_label(self, state: FlatState, label: Label) -> None:
        self.labeling.setdefault(state, set()).add(label)

    def __repr__(self) -> str:
        return f"FlatKS(|W|={len(self.states)}, |R|={len(self.transitions)})"
