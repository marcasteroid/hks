"""
main.py
=======
Load a hierarchical structure from ``.k`` files, model check a CTL formula,
and save an expanded flat structure figure as PDF.
"""

import argparse
from pathlib import Path
import time

from formula import Atom, ExistsNext
from expansion import flatten
from checknext import model_check
from visualize import draw_flat_structure
from parser import load_hierarchical_kripke_structure


def main():
    parser = argparse.ArgumentParser(description="CTL model checker for hierarchical Kripke structures")
    parser.add_argument(
        "directory",
        nargs="?",
        default="examples",
        help="Directory containing K1.k, K2.k, ... files",
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Also display the plot interactively (default: save PDF only)",
    )
    args = parser.parse_args()

    dir_path = Path(args.directory)
    if not dir_path.is_dir():
        print(f"Error: '{dir_path}' is not a directory")
        return

    print(f"Loading hierarchical structure from '{dir_path}' ...")
    try:
        hks = load_hierarchical_kripke_structure(dir_path)
    except Exception as e:
        print(f"Failed to load: {e}")
        return

    print("Flattening for visualisation...")
    flat_before = flatten(hks)

    # Save expanded structure figure as PDF
    draw_flat_structure(
        flat_before,
        title="Expanded Hierarchical Kripke Structure (before model checking)",
        output_path="viz/flat_structure.pdf",
        show=args.show,
    )

    # CTL formula: ∃○ ack
    phi = ExistsNext(Atom("ack"))
    print(f"\nModel checking formula: {phi}")

    start_time = time.time()
    result = model_check(hks, phi)
    elapsed = time.time() - start_time
    print(f"Result: {result}  (time: {elapsed:.2f}s)")


if __name__ == "__main__":
    main()