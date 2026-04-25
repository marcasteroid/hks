# Hierarchical CTL Model Checker
A Python implementation of **CTL (Computation Tree Logic) model checking for hierarchical Kripke structures**, based on:
> Alur, R. & Yannakakis, M. (1998). *Model Checking of Hierarchical State Machines.*  
> FSE ’98 / SIGSOFT Software Engineering Notes.
The tool supports **single-exit hierarchical state machines**, flattens them for visualization, and evaluates a subset of CTL formulas using the `CheckNext` algorithm.
---
## Project Overview
```text
hks-ctl/
├── formula.py          # CTL formula AST (atoms, ¬, ∧, ∃○, ∃U, derived operators)
├── kripke.py           # Data structures for flat and hierarchical Kripke structures
├── expansion.py        # Flatten a hierarchical Kripke structure into an ordinary one
├── checknext.py        # CheckNext transformation + CTL model checking loop
├── parser.py           # DSL parser for hierarchical structures (.k files)
├── visualize.py        # Export the flat structure as a publication-quality PDF
├── main.py             # CLI: load a model, check a formula, save figure
├── examples/
│   ├── K1.k            # Top-level substructure
│   └── K2.k            # Inner attempt substructure
└── README.md

⸻

Installation & Dependencies

Use uv (recommended) or pip to manage the project:

cd hks-ctl
uv sync

Required Packages

* matplotlib
* networkx
* tqdm

⸻

Quick Start

1. Ensure the example files examples/K1.k and examples/K2.k exist.
2. Run the model checker:

uv run main.py examples

The script will:

* Parse the hierarchical Kripke structure from the .k files.
* Flatten it and save a PDF figure to:

viz/flat_structure.pdf

* Check the CTL formula ∃○ ack (existential next).
* Print the result:

True

or

False

Show Plot on Screen

uv run main.py examples --show

Change the Formula

Edit the phi variable in main.py, or build formulas directly using formula.py.

⸻

The .k File Format (DSL)

A hierarchical Kripke structure is described using plain-text .k files, one file per substructure.

Each file defines a single substructure Kᵢ.

Examples:

K1.k
K2.k
K3.k

⸻

Syntax

# comment
nodes: <node1, node2, ..., nodeN>
boxes: <box1, box2, ..., boxM>
entry: <entry_node>
exit: <exit_node>
label:
    <node>: <prop1, prop2, ...>
map:
    <box>: <index>
edges:
    <source> -> <target>

⸻

Field Meaning

nodes

Comma-separated node names.

* No spaces inside names.
* Use _ if needed.
* entry and exit are automatically included.

Example:

nodes: start, wait_state, done

⸻

boxes

Comma-separated list of boxes.

Boxes are placeholders for nested substructures.

Example:

boxes: try1, try2

May be empty:

boxes:

⸻

entry

Initial node of the substructure.

entry: start

⸻

exit

Single exit node (single-exit hypothesis).

exit: success

⸻

label

Assign atomic propositions to nodes.

label:
    start: init
    fail: error
    ok: success

A node may have no propositions:

wait:

⸻

map

Maps boxes to referenced substructure indices.

map:
    try1: 2
    try2: 2

Meaning:

* try1 expands into K2
* try2 expands into K2

⸻

edges

Transitions.

edges:
    start -> try1
    (try1, fail) -> abort

Sources may be:

* A node:

start

* A box-return pair:

(try1, fail)

Targets may be:

* node
* box

⸻

Example Files

K1.k

# K1.k
nodes: start, success, abort
boxes: try1, try2
entry: start
exit: success
label:
    start: start
    abort: abort
    success: success
map:
    try1: 2
    try2: 2
edges:
    start -> try1
    (try1, fail) -> try2
    (try2, fail) -> abort
    (try1, ok) -> success
    (try2, ok) -> success

⸻

K2.k

# K2.k
nodes: send, wait, ack, timeout, ok, fail
boxes:
entry: send
exit: ok
label:
    send:
    wait:
    ack: ack
    timeout: timeout
    ok: ok
    fail: fail
map:
edges:
    send -> wait
    wait -> ack
    wait -> timeout
    ack -> ok
    timeout -> fail

⸻

Important Constraints

* Hierarchy must be well-formed:

if K_i references K_j, then j > i

* Each substructure has exactly one exit node.
* Exit transitions are defined in the parent structure.
* All propositions used in CTL formulas must appear in some label.

⸻

CTL Formula Building (Python API)

All formulas are in formula.py.

⸻

Atomic Propositions

from formula import Atom
p = Atom("ok")

⸻

Boolean Connectives

from formula import Neg, And, Or, Implies, Atom
phi = And(Atom("start"), Neg(Atom("fail")))

⸻

Temporal Operators

from formula import ExistsNext, ExistsUntil, Atom
phi = ExistsNext(Atom("ack"))              # ∃○ ack
psi = ExistsUntil(Atom("ack"), Atom("ok")) # ∃(ack U ok)

⸻

Derived Operators

from formula import (
    ExistsEventually,
    ExistsAlways,
    ForallAlways,
    ForallEventually,
    Atom
)
phi = ExistsEventually(Atom("ok"))   # ∃◇ ok
psi = ForallAlways(Atom("safe"))     # ∀□ safe

⸻

Standalone Example

from formula import Atom, ExistsEventually
from parser import load_hierarchical_kripke_structure
from checknext import model_check
hks = load_hierarchical_kripke_structure("examples")
result = model_check(hks, ExistsEventually(Atom("ok")))
print(result)

Output:

True

⸻

Understanding the Output

The model_check() function returns:

* True → top-level initial node satisfies the formula.
* False → it does not.

⸻

Visualization

The flattened structure is exported as a PDF.

Default behavior:

* States satisfying ack are colored green
* Others are light blue

⸻

Advanced Usage

Model Visualization

Use:

visualize.draw_flat_structure()

with a custom formula string.

⸻

Add New Temporal Operators

1. Extend formula.py
2. Add handling inside:

checknext.model_check()

⸻

Notes

Current implementation supports:

* ∃○
* Boolean connectives
* Derived CTL operators

A full ∃U implementation would require a more advanced fixpoint procedure.

⸻

References

* Alur, R., & Yannakakis, M. (1998). Model Checking of Hierarchical State Machines. FSE ’98.
* Baier, C., & Katoen, J.-P. (2008). Principles of Model Checking. MIT Press.

⸻

License

This project is provided for educational and research purposes.

Feel free to reuse and adapt.