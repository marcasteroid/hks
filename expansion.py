"""
expansion.py
============
Flatten a HierarchicalKripkeStructure into a FlatKripkeStructure.
No progress bars here – the operation is near‑instantaneous.
"""

from typing import Dict, Set, Tuple
from kripke import (
    Substructure,
    HierarchicalKripkeStructure,
    FlatKripkeStructure,
    FlatState,
    Label,
)

def flatten(hks: HierarchicalKripkeStructure) -> FlatKripkeStructure:
    """Recursively expand a hierarchical structure into a flat one."""

    memo = {}

    def expand(index: int, context: tuple) -> Tuple[
        Set[FlatState], Set[Tuple[FlatState, FlatState]], Dict[FlatState, Set[Label]]
    ]:
        key = (index, context)
        if key in memo:
            return memo[key]

        ki = hks.get(index)
        local_states: Set[FlatState] = set()
        local_trans: Set[Tuple[FlatState, FlatState]] = set()
        local_label: Dict[FlatState, Set[Label]] = {}

        def to_flat(node_or_pair):
            if isinstance(node_or_pair, str):
                return (*context, node_or_pair) if context else node_or_pair
            else:  # (box, exit_node) pair
                box, exit_n = node_or_pair
                return (*context, box, exit_n) if context else (box, exit_n)

        # 1. Add plain nodes and their labels
        for n in ki.nodes:
            flat_n = to_flat(n)
            local_states.add(flat_n)
            local_label[flat_n] = set(ki.labeling.get(n, set()))

        # 2. Process every edge
        for src, tgt in ki.edges:
            flat_src = to_flat(src)

            if isinstance(tgt, str) and ki.is_node(tgt):
                # simple node → node transition
                flat_tgt = to_flat(tgt)
                local_trans.add((flat_src, flat_tgt))

            elif isinstance(tgt, str) and ki.is_box(tgt):
                # node → box : enter the referenced substructure
                box = tgt
                j = ki.mapping[box]
                sub_context = (*context, box) if context else (box,)

                # recursively expand the inner structure
                sub_states, sub_trans, sub_label = expand(j, sub_context)
                local_states.update(sub_states)
                local_trans.update(sub_trans)
                for s, labs in sub_label.items():
                    local_label[s] = labs

                # entry point of the inner structure
                entry_flat = (*sub_context, hks.get(j).entry)
                local_trans.add((flat_src, entry_flat))

            # else: other edge types (e.g. (box,exit) → box) can be added here if needed

        memo[key] = (local_states, local_trans, local_label)
        return local_states, local_trans, local_label

    # start with the top‑level structure, empty context
    top = hks.top_level()
    all_states, all_trans, all_label = expand(top.index, ())

    initial_flat = top.entry  # context is empty for the initial state of K1
    if initial_flat not in all_states:
        all_states.add(initial_flat)

    return FlatKripkeStructure(
        states=list(all_states),
        initial=initial_flat,
        transitions=all_trans,
        labeling=all_label,
    )