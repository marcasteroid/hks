"""
ctl/formula.py
==============
Abstract Syntax Tree for Computation Tree Logic (CTL) formulae.

Syntax (state formulae Φ):
    Φ ::= true | a | Φ₁ ∧ Φ₂ | ¬Φ | ∃φ | ∀φ

Path formulae φ:
    φ ::= ○Φ | Φ U Φ

Derived operators are provided as convenience functions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────────────────────────────────────

class Formula(ABC):
    """Abstract base class for all CTL formulae."""

    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    def subformulas(self) -> List["Formula"]: ...

    # ── size / ordering ──────────────────────────────────────────────────────

    def size(self) -> int:
        """Number of nodes in the syntax tree."""
        return 1 + sum(f.size() for f in self.subformulas())

    def all_subformulas_ordered(self) -> List["Formula"]:
        """All sub-formulae (including self) in non-decreasing size order.

        Atomic formulae appear first; the formula itself appears last.
        Duplicates are removed while preserving order.
        """
        seen:      dict          = {}
        collected: List[Formula] = []

        def _visit(f: Formula) -> None:
            for sf in f.subformulas():
                _visit(sf)
            key = str(f)
            if key not in seen:
                seen[key] = True
                collected.append(f)

        _visit(self)
        return collected

    # ── equality / hashing (structural, by string representation) ────────────

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Formula) and str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        return str(self)


# ─────────────────────────────────────────────────────────────────────────────
# Propositional connectives
# ─────────────────────────────────────────────────────────────────────────────

class Atom(Formula):
    """Atomic proposition  a ∈ AP."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:          return self.name
    def subformulas(self) -> List:     return []


class Top(Formula):
    """Tautology  ⊤."""
    def __str__(self) -> str:          return "⊤"
    def subformulas(self) -> List:     return []


class Bot(Formula):
    """Contradiction  ⊥."""
    def __str__(self) -> str:          return "⊥"
    def subformulas(self) -> List:     return []


class Neg(Formula):
    """Negation  ¬Φ."""

    def __init__(self, sub: Formula) -> None:
        self.sub = sub

    def __str__(self) -> str:          return f"¬({self.sub})"
    def subformulas(self) -> List:     return [self.sub]


class And(Formula):
    """Conjunction  Φ₁ ∧ Φ₂."""

    def __init__(self, left: Formula, right: Formula) -> None:
        self.left, self.right = left, right

    def __str__(self) -> str:          return f"({self.left} ∧ {self.right})"
    def subformulas(self) -> List:     return [self.left, self.right]


# ─────────────────────────────────────────────────────────────────────────────
# Temporal operators
# ─────────────────────────────────────────────────────────────────────────────

class ExistsNext(Formula):
    """Existential next  ∃○Φ.

    Asserts that there exists a path on which Φ holds in the next state.
    """

    def __init__(self, sub: Formula) -> None:
        self.sub = sub

    def __str__(self) -> str:          return f"∃○({self.sub})"
    def subformulas(self) -> List:     return [self.sub]


class ExistsUntil(Formula):
    """Existential until  ∃(Φ U Ψ).

    Asserts that there exists a path on which Φ holds until Ψ becomes true.
    """

    def __init__(self, left: Formula, right: Formula) -> None:
        self.left, self.right = left, right

    def __str__(self) -> str:          return f"∃({self.left} U {self.right})"
    def subformulas(self) -> List:     return [self.left, self.right]


# ─────────────────────────────────────────────────────────────────────────────
# Derived operators  (syntactic sugar)
# ─────────────────────────────────────────────────────────────────────────────

def Or(a: Formula, b: Formula) -> Formula:
    """Disjunction  Φ ∨ Ψ  ≡  ¬(¬Φ ∧ ¬Ψ)."""
    return Neg(And(Neg(a), Neg(b)))

def Implies(a: Formula, b: Formula) -> Formula:
    """Implication  Φ → Ψ  ≡  ¬Φ ∨ Ψ."""
    return Or(Neg(a), b)

def ForallNext(sub: Formula) -> Formula:
    """Universal next  ∀○Φ  ≡  ¬∃○(¬Φ)."""
    return Neg(ExistsNext(Neg(sub)))

def ExistsEventually(sub: Formula) -> Formula:
    """Existential eventually  ∃◇Φ  ≡  ∃(⊤ U Φ)."""
    return ExistsUntil(Top(), sub)

def ForallAlways(sub: Formula) -> Formula:
    """Universal always  ∀□Φ  ≡  ¬∃◇(¬Φ)."""
    return Neg(ExistsEventually(Neg(sub)))

def ExistsAlways(sub: Formula) -> Formula:
    """Existential always  ∃□Φ  ≡  ¬∀◇(¬Φ)."""
    return Neg(Neg(ExistsEventually(Neg(sub))))

def ForallEventually(sub: Formula) -> Formula:
    """Universal eventually  ∀◇Φ  ≡  ¬∃□(¬Φ)."""
    return Neg(ExistsAlways(Neg(sub)))
