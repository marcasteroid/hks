"""
parser.py
=========
Parse a single substructure definition from a ``.k`` file.
Syntax is line‑based and deliberately Python‑like.

Grammar (informal)
------------------
# comment
nodes: <node1, node2, ...>
boxes: <box1, box2, ...>
entry: <entry_node>
exit: <exit_node>
label:
    <node>: <prop1, prop2, ...>
    ...
map:
    <box>: <index>
    ...
edges:
    <source> -> <target>
    ...

* source may be a simple name, or (box, exit_node)
* target is a name (node or box)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from kripke import Substructure, HierarchicalKripkeStructure


# ── helper for stripping inline comments and blank lines ────────────────────
def _strip_comment(line: str) -> str:
    """Remove inline comment (from ``#`` until end of line) and strip."""
    idx = line.find("#")
    if idx != -1:
        line = line[:idx]
    return line.strip()


# ── main parser ─────────────────────────────────────────────────────────────
def parse_substructure(text: str, index: int) -> Substructure:
    """Parse a single substructure from *text* and assign it the given *index*."""
    lines = text.splitlines()

    # First pass: extract blocks
    # We'll read line by line, maintaining a "current section"
    nodes: Set[str] = set()
    boxes: Set[str] = set()
    entry: str = ""
    exit_: str = ""
    labeling: Dict[str, Set[str]] = {}
    mapping: Dict[str, int] = {}
    edges: Set[Tuple] = set()

    current_section = None

    for raw_line in lines:
        line = _strip_comment(raw_line)
        if not line:
            continue

        # Check if we are entering a block (label:, map:, edges:)
        # The block indicator is a line ending with ':' and not containing '->'
        # We'll do a simple check: if line matches a known section name exactly
        # with optional whitespace before colon.
        known_sections = {"label", "map", "edges"}
        line_lower = line.lower().rstrip(":")
        # Actually, we can just check if line starts with a keyword followed by ':'
        m = re.match(r'^(label|map|edges)\s*:', line)
        if m:
            current_section = m.group(1).lower()
            # the line might also contain a definition on the same line? We'll forbid that.
            # We'll assume keywords are alone on the line (with optional trailing comment)
            continue

        # Also handle top-level fields: nodes, boxes, entry, exit
        # These are key: value lines
        if ":" in line and "->" not in line and current_section is None:
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip().rstrip(",")  # allow trailing comma
            if key == "nodes":
                nodes = {n.strip() for n in value.split(",") if n.strip()}
            elif key == "boxes":
                boxes = {b.strip() for b in value.split(",") if b.strip()}
            elif key == "entry":
                entry = value.strip()
            elif key == "exit":
                exit_ = value.strip()
            else:
                # unknown top-level field – ignore or error
                pass
            continue

        # In a section
        if current_section == "label":
            # syntax: node_name: prop1, prop2, ...
            if ":" in line:
                node_name, _, props_str = line.partition(":")
                node_name = node_name.strip()
                props_str = props_str.strip().rstrip(",")
                props = {p.strip() for p in props_str.split(",") if p.strip()}
                labeling[node_name] = props
        elif current_section == "map":
            # syntax: box_name: index
            if ":" in line:
                box_name, _, idx_str = line.partition(":")
                box_name = box_name.strip()
                idx_str = idx_str.strip()
                try:
                    idx = int(idx_str)
                except ValueError:
                    raise ValueError(f"Invalid index in map: {line}")
                mapping[box_name] = idx
        elif current_section == "edges":
            # syntax: source -> target
            if "->" in line:
                left, _, right = line.partition("->")
                left = left.strip()
                right = right.strip()
                # Parse source: it could be a simple name or (box, exit_node)
                src = _parse_edge_end(left)
                tgt = _parse_edge_end(right)
                edges.add((src, tgt))
        else:
            # unknown section – ignore
            pass

    # Validate entry/exit
    if not entry:
        raise ValueError("Missing 'entry' specification")
    if not exit_:
        raise ValueError("Missing 'exit' specification")

    # Ensure entry/exit nodes are in nodes set
    nodes.add(entry)
    nodes.add(exit_)

    # Ensure all nodes mentioned in labeling are in nodes set (add them if not)
    for n in labeling:
        nodes.add(n)

    return Substructure(
        index=index,
        nodes=nodes,
        boxes=boxes,
        entry=entry,
        exit=exit_,
        labeling=labeling,
        mapping=mapping,
        edges=edges,
    )


def _parse_edge_end(text: str) -> str | Tuple[str, str]:
    """Parse a source or target endpoint.
    - simple: 'node' or 'box' → return as is
    - compound: '(box, exit_node)' → return tuple (box, exit_node)
    """
    text = text.strip()
    m = re.match(r'^\((.+),\s*(.+)\)$', text)
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    return text


# ── loader for a whole hierarchical structure from a directory ──────────────
def load_hierarchical_kripke_structure(directory: str | Path) -> HierarchicalKripkeStructure:
    """
    Read all ``.k`` files in *directory*.
    Filename must start with ``K`` followed by an index number, e.g. ``K1.k``, ``K2.k``.
    The index determines the ordering.
    """
    directory = Path(directory)
    substructures = []

    for file_path in sorted(directory.glob("K*.k")):
        # Extract index: e.g., 'K1.k' -> 1
        stem = file_path.stem  # 'K1'
        if not stem.startswith("K") or len(stem) < 2:
            continue
        try:
            index = int(stem[1:])
        except ValueError:
            continue

        text = file_path.read_text(encoding="utf-8")
        ki = parse_substructure(text, index)
        substructures.append(ki)

    if not substructures:
        raise FileNotFoundError(f"No 'K*.k' files found in {directory}")

    return HierarchicalKripkeStructure(substructures=substructures)