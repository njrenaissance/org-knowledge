"""Attention budgets — the scarcity that makes bridges congest.

Each node processes at most ``capacity`` messages per step; anything beyond that
is dropped. The dropped count is the raw congestion signal the ``bridge_load``
metric is computed from, so congestion emerges mechanically from the cap rather
than being imposed by fiat (see ``spec/spec-code.md`` §8, finding #3).
"""

from collections.abc import Sequence

__all__ = ["AttentionBudget"]


class AttentionBudget:
    """Caps how many messages a node admits per step.

    ``admit`` processes at most ``capacity`` messages and drops the remainder,
    exposing the drop count from the most recent call via :attr:`dropped` for use
    in the ``bridge_load`` metric. Which specific messages are dropped is not this
    class's concern — it only enforces the cap.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError(f"capacity must be non-negative, got {capacity}")
        self._capacity = capacity
        self._dropped = 0

    @property
    def capacity(self) -> int:
        """The per-step processing limit."""
        return self._capacity

    @property
    def dropped(self) -> int:
        """Messages dropped by the most recent :meth:`admit` call (``0`` before the first)."""
        return self._dropped

    def admit[T](self, messages: Sequence[T]) -> list[T]:
        """Return at most ``capacity`` of ``messages``, recording the overflow as dropped.

        The returned messages are a subset of the input. When ``len(messages)``
        exceeds ``capacity``, exactly ``len(messages) - capacity`` are dropped;
        otherwise all are admitted and :attr:`dropped` is ``0``.
        """
        admitted = list(messages[: self._capacity])
        self._dropped = len(messages) - len(admitted)
        return admitted
