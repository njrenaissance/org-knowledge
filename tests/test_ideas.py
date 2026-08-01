"""Unit tests for the core data models in ``orgflow.ideas``.

These pin the shapes downstream layers depend on: the two enums, the four
dataclasses, their required fields, and their defaults.
"""

import pytest

from orgflow.ideas import (
    Idea,
    IdeaType,
    KnowledgeItem,
    Message,
    Problem,
    Status,
)


@pytest.mark.unit
def test_idea_type_has_exactly_explicit_and_tacit() -> None:
    """``IdeaType`` is exactly the two contagion regimes."""
    assert [member.value for member in IdeaType] == ["explicit", "tacit"]


@pytest.mark.unit
def test_status_has_exactly_aware_and_held() -> None:
    """``Status`` is exactly the two knowledge relationships."""
    assert [member.value for member in Status] == ["aware", "held"]


def _make_idea(**overrides: object) -> Idea:
    """Build an ``Idea`` with all required fields, overriding as needed."""
    defaults: dict[str, object] = {
        "id": 1,
        "type": IdeaType.EXPLICIT,
        "domain": "sales",
        "source": 7,
        "created_step": 3,
        "shelf_life": 10,
    }
    return Idea(**{**defaults, **overrides})  # type: ignore[arg-type]


@pytest.mark.unit
def test_idea_stores_required_fields() -> None:
    """An ``Idea`` round-trips its required attributes."""
    idea = _make_idea()

    assert idea.id == 1
    assert idea.type is IdeaType.EXPLICIT
    assert idea.domain == "sales"
    assert idea.source == 7
    assert idea.created_step == 3
    assert idea.shelf_life == 10


@pytest.mark.unit
def test_idea_optional_fields_default() -> None:
    """Unset optional fields fall back to their documented defaults."""
    idea = _make_idea()

    assert idea.confidence == 1.0
    assert idea.relevance == {}
    assert idea.problem_id is None
    assert idea.fitness is None


@pytest.mark.unit
def test_idea_optional_fields_are_overridable() -> None:
    """Every optional field accepts an explicit value."""
    idea = _make_idea(
        confidence=0.4,
        relevance={"engineering": 0.9},
        problem_id=2,
        fitness=0.75,
    )

    assert idea.confidence == 0.4
    assert idea.relevance == {"engineering": 0.9}
    assert idea.problem_id == 2
    assert idea.fitness == 0.75


@pytest.mark.unit
def test_idea_relevance_defaults_are_not_shared() -> None:
    """Each ``Idea`` gets its own ``relevance`` dict (guards default_factory)."""
    first = _make_idea()
    second = _make_idea()

    first.relevance["engineering"] = 1.0

    assert second.relevance == {}


@pytest.mark.unit
def test_knowledge_item_stores_required_fields() -> None:
    """A ``KnowledgeItem`` round-trips its required attributes."""
    item = KnowledgeItem(idea_id=5, status=Status.HELD, acquired_step=2)

    assert item.idea_id == 5
    assert item.status is Status.HELD
    assert item.acquired_step == 2


@pytest.mark.unit
def test_knowledge_item_optional_fields_default() -> None:
    """Unset optional fields fall back to their documented defaults."""
    item = KnowledgeItem(idea_id=5, status=Status.AWARE, acquired_step=2)

    assert item.exposures == 0
    assert item.confidence == 1.0


@pytest.mark.unit
def test_knowledge_item_exposures_is_mutable() -> None:
    """The agent increments ``exposures`` in place under the tacit rule."""
    item = KnowledgeItem(idea_id=5, status=Status.AWARE, acquired_step=2)

    item.exposures += 1

    assert item.exposures == 1


@pytest.mark.unit
def test_problem_stores_fields() -> None:
    """A ``Problem`` round-trips its competing solutions and best fitness."""
    problem = Problem(id=9, solution_ids=[1, 2, 3], best_fitness=0.8)

    assert problem.id == 9
    assert problem.solution_ids == [1, 2, 3]
    assert problem.best_fitness == 0.8


@pytest.mark.unit
def test_message_stores_transmission_fields() -> None:
    """A ``Message`` carries the idea and edge context contagion reads."""
    idea = _make_idea()
    message = Message(idea=idea, edge_weight=0.6, sender=7, receiver=4)

    assert message.idea is idea
    assert message.edge_weight == 0.6
    assert message.sender == 7
    assert message.receiver == 4


@pytest.mark.unit
def test_message_exposes_idea_accessors_used_by_contagion() -> None:
    """Contagion reaches ``msg.idea.type`` and ``msg.idea.confidence``."""
    message = Message(
        idea=_make_idea(type=IdeaType.TACIT, confidence=0.3),
        edge_weight=0.6,
        sender=7,
        receiver=4,
    )

    assert message.idea.type is IdeaType.TACIT
    assert message.idea.confidence == 0.3
