# ADR-0001: Lightweight hand-rolled ABM layer instead of Mesa

## Status
accepted

## Context
`spec/spec-code.md §2` (the "Stack" table) names **Mesa** as the agent-scheduling
framework, for its standard ABM loop plus the `DataCollector` and `batch_run`
conveniences. Committing the whole model/agent layer to a framework is a
subsystem-wide dependency decision that would be expensive to unwind later, so it
is recorded here per `.claude/standards/decisions.md`.

The constraints that force the choice:

- Every interesting mechanism in this simulation is custom regardless of
  framework — the two-phase step, per-receiver attention admission, and the
  contagion strategy objects. Mesa would supply only `Agent`/`Model` base
  classes, `DataCollector`, and `batch_run`, each a few dozen lines to replace.
- Mesa's API is version-sensitive: the 3.x rewrite removed schedulers and
  changed the agent lifecycle. The project targets **Python 3.14**
  (`requires-python = ">=3.14"`), where pinning against Mesa adds fragility for
  little gain.
- Fewer heavy dependencies keeps `mypy` and `ruff` clean across `src/`.

## Options considered
- **(a) Adopt Mesa as specced (`spec-code.md §2`).** Gains the standard ABM
  loop, `DataCollector`, and `batch_run` off the shelf. Costs: a heavyweight,
  version-sensitive dependency on Python 3.14, for base classes the custom
  mechanisms largely bypass anyway.
- **(b) Hand-roll a lightweight `Model`/`Agent` layer on NetworkX + pandas
  (chosen).** A small pandas-backed collector and batch harness replace Mesa's
  conveniences; the runtime dependency surface stays just NetworkX (graphs) and
  pandas (per-step frames). Costs: those conveniences must be re-implemented
  ourselves, and this is a documented deviation from the spec's stack.

## Decision
Build a hand-rolled lightweight `Model`/`Agent` layer plus a small pandas-backed
metrics collector, depending only on **NetworkX + pandas**. Do not add Mesa as a
dependency. (matplotlib enters later, with the sweep/figures milestone.)

## Consequences
- **Easier:** a smaller, well-understood dependency surface keeps `mypy` and
  `ruff` clean and removes exposure to Mesa's version churn on Python 3.14; the
  model/agent layer is shaped entirely to this simulation's mechanics rather
  than to a framework's lifecycle.
- **Harder / ruled out:** Mesa's `DataCollector` and `batch_run` conveniences are
  no longer available and must be re-implemented thinly — the pandas-backed
  collector lands with the two-phase model loop, and the batch-sweep harness
  with the run layer. This is an intentional, documented deviation from
  `spec/spec-code.md §2`, not a hidden coupling (see `spec/build-order.md`).
