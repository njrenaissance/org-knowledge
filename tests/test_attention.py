"""Unit tests for the attention budget (``src/orgflow/attention.py``).

These are the approved "done" criteria for issue #12: they pin the congestion
*contract* — the cap, the recoverable drop count, and admitted-is-a-subset — but
deliberately avoid asserting *which* messages are dropped, since any drop-selection
policy beyond the capacity cap is out of scope for this issue.
"""

import pytest

from orgflow.attention import AttentionBudget


@pytest.mark.unit
@pytest.mark.parametrize(
    ("capacity", "n_messages", "expected_admitted", "expected_dropped"),
    [
        pytest.param(5, 8, 5, 3, id="over_capacity_drops_overflow"),
        pytest.param(5, 5, 5, 0, id="exactly_at_capacity_drops_none"),
        pytest.param(5, 2, 2, 0, id="under_capacity_admits_all"),
        pytest.param(5, 0, 0, 0, id="no_messages"),
        pytest.param(0, 4, 0, 4, id="zero_capacity_drops_all"),
        pytest.param(1, 1, 1, 0, id="single_message_fits"),
    ],
)
def test_admit_enforces_capacity(capacity: int, n_messages: int, expected_admitted: int, expected_dropped: int) -> None:
    """``admit`` caps admissions and records the overflow as dropped."""
    messages = list(range(n_messages))
    budget = AttentionBudget(capacity)

    admitted = budget.admit(messages)

    assert len(admitted) == expected_admitted
    assert budget.dropped == expected_dropped
    assert len(admitted) + budget.dropped == n_messages


@pytest.mark.unit
@pytest.mark.parametrize("n_messages", [3, 10, 100])
def test_admit_never_exceeds_capacity(n_messages: int) -> None:
    """The admitted count is capped by ``capacity`` regardless of demand."""
    capacity = 5
    budget = AttentionBudget(capacity)

    admitted = budget.admit(list(range(n_messages)))

    assert len(admitted) <= capacity


@pytest.mark.unit
def test_admitted_messages_are_a_subset_of_the_input() -> None:
    """Admitted messages come from the input — nothing is fabricated."""
    messages = ["a", "b", "c", "d", "e", "f"]
    budget = AttentionBudget(3)

    admitted = budget.admit(messages)

    assert all(message in messages for message in admitted)


@pytest.mark.unit
def test_dropped_count_is_recoverable_for_bridge_load() -> None:
    """The overflow count is exactly ``len(messages) - capacity`` when over capacity."""
    budget = AttentionBudget(4)

    budget.admit(list(range(10)))

    assert budget.dropped == 10 - 4


@pytest.mark.unit
def test_dropped_reflects_only_the_most_recent_admit() -> None:
    """A later ``admit`` overwrites the recorded drop count; it does not accumulate."""
    capacity = 2
    budget = AttentionBudget(capacity)

    budget.admit(list(range(5)))
    assert budget.dropped == 5 - capacity

    budget.admit(list(range(capacity)))  # fits exactly; must not stay at the prior drop count

    assert budget.dropped == 0


@pytest.mark.unit
def test_dropped_is_zero_before_any_admit() -> None:
    """No messages have been seen yet, so nothing has been dropped."""
    assert AttentionBudget(5).dropped == 0


@pytest.mark.unit
def test_admit_treats_messages_as_opaque() -> None:
    """Elements are passed through untouched — the budget never inspects them."""
    sentinels = [object(), object(), object()]
    budget = AttentionBudget(2)

    admitted = budget.admit(sentinels)

    assert all(admitted[i] is sentinels[i] for i in range(len(admitted)))


@pytest.mark.unit
def test_capacity_is_exposed() -> None:
    """The configured capacity is readable."""
    capacity = 7
    assert AttentionBudget(capacity).capacity == capacity


@pytest.mark.unit
@pytest.mark.parametrize("capacity", [-1, -5])
def test_negative_capacity_is_rejected(capacity: int) -> None:
    """A negative capacity is a programmer error and fails loudly at construction."""
    with pytest.raises(ValueError, match="non-negative"):
        AttentionBudget(capacity)
