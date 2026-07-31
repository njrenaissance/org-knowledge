# plan.md — OrgFlow Implementation Plan

Companion to `spec.md`, `spec-v0.2.md`, and `spec-code.md`. This is the
recommended **build order and framework decision** for turning the spec into
code. It is guidance for sequencing and inner-loop implementation — the
canonical contract is `spec.md`.

## Framework decision: lightweight ABM, no Mesa

`spec-code.md §2` names **Mesa** for agent scheduling. We recommend building a
**hand-rolled `Model`/`Agent` layer** plus a small pandas-backed collector
instead, and depending only on **NetworkX + pandas** (matplotlib enters with the
sweep/figures milestone).

Rationale:

- Every interesting mechanism — the two-phase step, per-receiver attention
  admission, the contagion strategy objects — is custom regardless of framework.
  Mesa would supply only `Agent`/`Model` base classes, `DataCollector`, and
  `batch_run`, all of which are a few dozen lines to replace.
- Mesa's API is version-sensitive (the 3.x rewrite removed schedulers and
  changed the agent lifecycle); pinning against it adds fragility on Python
  3.14 for little gain.
- Fewer heavy dependencies keeps `mypy --strict` and `ruff` clean.

This deviates from the spec's stack, so it is recorded as an **ADR**
(`docs/adr/0001-*.md`, authored via the `adr-authoring` skill) — context,
options weighed, decision, and what it rules out (Mesa's `batch_run` /
`DataCollector` conveniences, which we re-implement thinly).

## Package layout

Everything lands under **`src/orgflow/`** (the repo sets `pythonpath = ["src"]`
and `coverage source = ["src"]`), with a thin `src/run.py` / `src/analysis.py`
run layer added at the sweep milestone. Modules mirror `spec-code.md §3`:
`errors.py` (a project `OrgFlowError` hierarchy, per the error-handling
standard), `config.py`, `ideas.py`, `graph_builders.py`, `absorption.py`,
`attention.py`, `contagion.py`, `agents.py`, `metrics.py`, `model.py`.
Tests mirror module names under `tests/`.

Cross-cutting conventions the build must honor (from `CLAUDE.md` and
`.claude/standards/`): a single `OrgFlowError` root with domain subclasses and
no bare `except`; determinism via one seeded `random.Random`; type hints on all
`src/` code; `@pytest.mark.parametrize` for same-shape cases; `unit` vs.
`integration` markers with the 70% coverage floor measured on unit tests.

## Recommended build order

Follow the spec's own milestones (`spec-code.md §13`), each runnable and each
producing a metric:

| Milestone | Delivers | Findings testable |
|---|---|---|
| **M1 — Skeleton** | `ideas.py`, `config.py`, `errors.py`, `graph_builders.py` (planted-partition + weights + bridges), a build-only `Organization`. `test_small_world`. | validation sanity |
| **M2 — Explicit diffusion** | `EmployeeAgent`, two-phase loop, `ExplicitContagion`, `absorption.py`, holding/awareness metrics. First real runs. | — |
| **M3 — Tacit + attention** | `TacitContagion`, `AttentionBudget`, congestion + cross-team metrics. | **#1 bridges help explicit / fail tacit; #3 bridge congestion** |
| **M4 — Decision quality** | `Problem` sets, hidden fitness, `decision_quality`, conflicting/duplicate metrics. | **#2 fast convergence, worse decisions** |
| **M5 — Synthesis + sweep** | `synthesis.py`, `run.py` batch grid, `analysis.py` matplotlib figures. | **#4 capability vs. communication** |

**Suggested first slice = M1–M3.** It stands up the graph, both contagion
types, absorptive capacity, and the attention/congestion mechanism — enough to
make findings #1 and #3 reproducible — while deferring decision quality (M4) and
the sweep harness + figures (M5) to follow-up work. Sequencing may of course cut
the issues differently; this is the recommended ordering, not a constraint.

## Test strategy

Mirror `spec-code.md §12`, mostly `unit`-marked (pure computation — no external
boundary to fake):

- `test_validation.py::test_small_world` — WS avg shortest-path collapses as
  rewiring probability rises.
- `test_graph_builders.py` — node count, intra > inter weights, bridge count,
  unknown topology → `TopologyError`.
- `test_absorption.py` — `≈ absorptive * BASE` with no related expertise;
  monotonic in expertise.
- `test_contagion.py` — explicit sets held/aware via an injected RNG; tacit needs
  `exposures ≥ threshold` **and** `edge_weight ≥ cutoff`; plus
  `test_bridges_help_explicit_not_tacit` (finding #1).
- `test_attention.py` — `admit` caps/drops overflow; `test_bridge_congestion`
  (finding #3).
- `test_model.py` — `run()` returns the documented DataFrame columns; same seed
  ⇒ identical output.

Finding-reproduction tests use small graphs, short runs, and fixed seeds
(averaged over a handful of seeds for robustness) so they stay fast and
deterministic while still asserting the qualitative result.

## Documentation upkeep

Per `.claude/standards/wiki.md`, regenerate `openwiki/` (`openwiki code
--update`) alongside code changes once implementation begins. The `openwiki`
CLI is a paid, per-machine global tool not installed in every environment;
where it is unavailable, note the regeneration as a follow-up rather than
hand-editing generated Markdown.
