"""
main.py
=======
Example: build a hierarchical structure, model check a CTL formula, and visualize.
"""

from formula import Atom, ExistsNext
from kripke import Substructure, HierarchicalKripkeStructure
from expansion import flatten
from checknext import model_check
from visualize import draw_flat_structure
import time


def build_example_hks() -> HierarchicalKripkeStructure:
    """Construct the hierarchical message‑sending example (simplified)."""

    # --- K2: the inner attempt ---
    k2 = Substructure(
        index=2,
        nodes={"send", "wait", "ack", "timeout", "ok", "fail"},
        boxes=set(),
        entry="send",
        exit="ok",
        labeling={
            "send": set(),
            "wait": set(),
            "ack": {"ack"},
            "timeout": {"timeout"},
            "ok": {"ok"},
            "fail": {"fail"},
        },
        mapping={},
        edges={
            ("send", "wait"),
            ("wait", "ack"),
            ("wait", "timeout"),
            ("ack", "ok"),
            ("timeout", "fail"),
        },
    )

    # --- K1: top‑level ---
    k1 = Substructure(
        index=1,
        nodes={"start", "abort", "success"},
        boxes={"try1", "try2"},
        entry="start",
        exit="success",
        labeling={
            "start": {"start"},
            "abort": {"abort"},
            "success": {"success"},
        },
        mapping={"try1": 2, "try2": 2},
        edges={
            ("start", "try1"),
            (("try1", "fail"), "try2"),
            (("try2", "fail"), "abort"),
            (("try1", "ok"), "success"),
            (("try2", "ok"), "success"),
        },
    )

    return HierarchicalKripkeStructure(substructures=[k1, k2])


def main():
    print("Building hierarchical Kripke structure...")
    hks = build_example_hks()

    print("Flattening structure for visualisation...")
    flat_before = flatten(hks)

    draw_flat_structure(flat_before, title="Expanded structure (before model checking)")

    # CTL formula: ∃○ ack
    phi = ExistsNext(Atom("ack"))
    print(f"\nModel checking formula: {phi}")
    start_time = time.time()
    result = model_check(hks, phi)
    elapsed = time.time() - start_time
    print(f"Result: {result}  (time: {elapsed:.2f}s)")


if __name__ == "__main__":
    main()