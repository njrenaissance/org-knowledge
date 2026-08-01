"""Core data models: the shared vocabulary of every OrgFlow mechanic.

Contagion reads :class:`Idea` and :class:`Message`, agents hold
:class:`KnowledgeItem`s keyed by idea id, and decision quality reads
:class:`Problem`. Defining these once keeps their shapes from diverging
across the contagion, attention, agent, and model layers.

These types are pure data — no behavior. Knowledge-state transitions live on
the agent, the contagion rules live in ``contagion.py``, and idea seeding
lives in the model.
"""

from dataclasses import dataclass, field
from enum import Enum


class IdeaType(Enum):
    """How an idea spreads."""

    EXPLICIT = "explicit"  # simple contagion
    TACIT = "tacit"  # complex contagion


class Status(Enum):
    """A node's relationship to an idea it has encountered."""

    AWARE = "aware"  # knows it exists / where it lives (transactive memory)
    HELD = "held"  # actually possesses it


@dataclass
class Idea:
    """A unit of information that flows through the organization."""

    id: int
    type: IdeaType
    domain: str  # keys absorptive-capacity matching
    source: int  # originating node id
    created_step: int
    shelf_life: int  # steps until expiry
    confidence: float = 1.0  # provenance-weighted trust
    relevance: dict[str, float] = field(default_factory=dict)  # team -> value
    problem_id: int | None = None  # if part of a competing-solution set
    fitness: float | None = None  # HIDDEN quality; only for problem solutions


@dataclass
class KnowledgeItem:
    """One node's holding of a single idea, keyed elsewhere by ``idea_id``."""

    idea_id: int
    status: Status
    acquired_step: int
    exposures: int = 0  # for tacit threshold rule
    confidence: float = 1.0


@dataclass
class Problem:
    """A question with several competing solution-ideas of differing hidden fitness.

    Lets 'decision quality' diverge from 'convergence speed'.
    """

    id: int
    solution_ids: list[int]
    best_fitness: float  # for normalizing quality


@dataclass
class Message:
    """A single idea transmission across one edge.

    Produced by an agent's ``propose_transmissions`` and consumed by a
    contagion rule. ``sender`` and ``receiver`` are node ids (not agents), so
    this record stays free of an ``agents`` import and the contagion, agent,
    and model layers can all depend on it without a cycle.
    """

    idea: Idea
    edge_weight: float
    sender: int  # node id
    receiver: int  # node id
