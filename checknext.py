"""
checknext.py
============
Implementation of CheckNext and CTL model checking for hierarchical Kripke structures.
"""

from copy import deepcopy
from typing import Dict, Set, Union, Tuple
from tqdm import tqdm

from formula import Formula, Atom, Neg, And, ExistsNext
from kripke import HierarchicalKripkeStructure, Substructure


def _satisfies_psi(
    hks: HierarchicalKripkeStructure,
    ki: Substructure,
    u: str,
    psi_str: str,
    chi_str: str,
) -> bool:
    """Return True if node u in substructure ki satisfies ψ = ∃○χ."""
    # direct node successors
    for src, tgt in ki.edges:
        if src == u and isinstance(tgt, str) and ki.is_node(tgt):
            if chi_str in ki.labeling.get(tgt, set()):
                return True
    # box successors
    for src, tgt in ki.edges:
        if src == u and isinstance(tgt, str) and ki.is_box(tgt):
            box = tgt
            j = ki.mapping[box]
            target_ki = hks.get(j)
            if chi_str in target_ki.labeling.get(target_ki.entry, set()):
                return True
    return False


def check_next(
    hks: HierarchicalKripkeStructure, chi: Formula
) -> HierarchicalKripkeStructure:
    """
    Transform the hierarchical structure K into K' according to the CheckNext procedure.
    ψ = ∃○χ
    """
    chi_str = str(chi)
    psi = ExistsNext(chi)
    psi_str = str(psi)

    # Precompute satisfaction relations on the original HKS
    psi_satisfied: Dict[int, Set[str]] = {}
    entry_satisfied: Dict[int, bool] = {}

    # progress bar for evaluating all nodes
    total_nodes = sum(len(ki.nodes) for ki in hks)
    with tqdm(total=total_nodes, desc="CheckNext: evaluating ψ", unit="node") as pbar:
        for ki in hks:
            idx = ki.index
            sat = set()
            for u in ki.nodes:
                if _satisfies_psi(hks, ki, u, psi_str, chi_str):
                    sat.add(u)
                pbar.update(1)
            psi_satisfied[idx] = sat
            entry_satisfied[idx] = ki.entry in sat

    # Build new substructures (K_i^0 and K_i^1) with proper labelling
    new_substructures = []
    orig_idx_of_new = {}       # new_index -> original index
    index_map: Dict[int, Union[int, Tuple[int, int]]] = {}
    new_index = 1

    # Sort original substructures by index
    for ki in tqdm(sorted(hks.substructures, key=lambda k: k.index),
                   desc="CheckNext: building K’", unit="substructure"):
        idx = ki.index
        out_sat = ki.exit in psi_satisfied[idx]

        # always create K_i^0
        ki0 = ki.copy()
        ki0.index = new_index
        for u in psi_satisfied[idx]:
            ki0.add_label(u, psi_str)

        if out_sat:
            # exit already satisfies ψ → only one version needed
            new_substructures.append(ki0)
            orig_idx_of_new[ki0.index] = idx
            index_map[idx] = new_index
            new_index += 1
        else:
            # create K_i^1 as well
            ki1 = ki.copy()
            ki1.index = new_index + 1
            for u in psi_satisfied[idx]:
                ki1.add_label(u, psi_str)
            ki1.add_label(ki.exit, psi_str)   # force ψ at exit node

            new_substructures.append(ki0)
            new_substructures.append(ki1)
            orig_idx_of_new[ki0.index] = idx
            orig_idx_of_new[ki1.index] = idx
            index_map[idx] = (new_index, new_index + 1)
            new_index += 2

    # Update box mappings
    original_by_index = {ki.index: ki for ki in hks}
    for ki_new in tqdm(new_substructures, desc="CheckNext: remapping boxes", unit="substructure"):
        orig_idx = orig_idx_of_new[ki_new.index]
        orig_ki = original_by_index[orig_idx]
        new_mapping = {}
        for box, j_orig in orig_ki.mapping.items():
            j_entry_sat = entry_satisfied[j_orig]
            mapped = index_map[j_orig]
            if isinstance(mapped, tuple):
                new_j = mapped[1] if j_entry_sat else mapped[0]   # K^1 / K^0
            else:
                new_j = mapped
            new_mapping[box] = new_j
        ki_new.mapping = new_mapping

    return HierarchicalKripkeStructure(substructures=new_substructures)


def model_check(hks: HierarchicalKripkeStructure, phi: Formula) -> bool:
    """
    Full CTL model‑checking algorithm for single‑exit hierarchical Kripke structures.
    Returns True if the top‑level initial node satisfies φ.
    """
    current = deepcopy(hks)

    # All sub-formulas in non‑decreasing size order
    ordered = phi.all_subformulas_ordered()

    for psi in tqdm(ordered, desc="Model checking", unit="subformula"):
        if isinstance(psi, Atom):
            # atoms are already labelled
            continue
        elif isinstance(psi, Neg):
            sub = psi.sub
            sub_str = str(sub)
            psi_str = str(psi)
            for ki in current:
                for u in ki.nodes:
                    if sub_str not in ki.labeling.get(u, set()):
                        ki.add_label(u, psi_str)
        elif isinstance(psi, And):
            left_str = str(psi.left)
            right_str = str(psi.right)
            psi_str = str(psi)
            for ki in current:
                for u in ki.nodes:
                    labs = ki.labeling.get(u, set())
                    if left_str in labs and right_str in labs:
                        ki.add_label(u, psi_str)
        elif isinstance(psi, ExistsNext):
            chi = psi.sub
            current = check_next(current, chi)
        else:
            raise NotImplementedError(
                f"Operator {type(psi).__name__} not supported."
            )

    top = current.top_level()
    return str(phi) in top.labeling.get(top.entry, set())