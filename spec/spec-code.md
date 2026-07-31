# Code Specification — Organizational Information Flow Simulation (v0.2)

Companion to `spec-v0.2.md`. This is the engineering design: what the software is, how it's structured, and the interfaces to build against. Illustrative signatures are Python; they're interface sketches, not final implementation.

---

## 1. What we're building

A discrete-time, agent-based simulation of knowledge diffusion on a community-structured graph. Each run:

1. builds an organization graph (teams as communities, weighted edges, designated bridges),
2. seeds a set of **ideas** (each tacit or explicit; some grouped into competing-solution **problems** with hidden fitness),
3. steps agents forward — they transmit, absorb, synthesize, and forget under attention limits,
4. records metrics per step,

and a **sweep harness** runs this across parameter grids to test the four target findings in `spec-v0.2.md §8`.

The whole thing is a library (`orgflow/`) plus a thin run/analysis layer. No UI, no AI, no network calls.

## 2. Stack

| Concern | Choice | Why |
|---|---|---|
| Graph | **NetworkX** | Community generators (SBM/planted-partition), edge weights, path-length checks for validation |
| Agent scheduling | **Mesa** | Standard ABM loop, `DataCollector`, `batch_run` for sweeps |
| Data | `dataclasses` + **pandas** | Typed models; tidy per-step frames |
| Plots | **matplotlib** | Sweep summaries, convergence curves |
| Tests | **pytest** | Validation + unit tests |

## 3. Module layout

```
orgflow/
  ideas.py          # Idea, KnowledgeItem, IdeaType, Problem
  agents.py         # EmployeeAgent
  model.py          # Organization(Model) — owns graph, schedule, collectors, loop
  graph_builders.py # community + ER/WS/BA topologies, edge weights, bridge assignment
  contagion.py      # ExplicitContagion, TacitContagion (strategy objects)
  absorption.py     # absorptive_capacity(receiver, idea) -> float
  attention.py      # per-node send/receive budgets (source of bridge congestion)
  synthesis.py      # combine held ideas -> new idea (exploration mechanism)
  metrics.py        # metric functions registered on the DataCollector
  config.py         # SimConfig dataclass (all knobs + defaults)
run.py              # single run + batch sweep entrypoints
analysis.py         # aggregate sweep output, produce figures
tests/
  test_contagion.py
  test_absorption.py
  test_attention.py
  test_validation.py   # WS small-world sanity; connectivity→accuracy tradeoff
```

## 4. Core data models (`ideas.py`)

```python
from dataclasses import dataclass, field
from enum import Enum

class IdeaType(Enum):
    EXPLICIT = "explicit"   # simple contagion
    TACIT    = "tacit"      # complex contagion

@dataclass
class Idea:
    id: int
    type: IdeaType
    domain: str                      # keys absorptive-capacity matching
    source: int                      # originating node id
    created_step: int
    shelf_life: int                  # steps until expiry
    confidence: float = 1.0          # provenance-weighted trust
    relevance: dict[str, float] = field(default_factory=dict)  # team -> value
    problem_id: int | None = None    # if part of a competing-solution set
    fitness: float | None = None     # HIDDEN quality; only for problem solutions

class Status(Enum):
    AWARE = "aware"   # knows it exists / where it lives (transactive memory)
    HELD  = "held"    # actually possesses it

@dataclass
class KnowledgeItem:
    idea_id: int
    status: Status
    acquired_step: int
    exposures: int = 0               # for tacit threshold rule
    confidence: float = 1.0

@dataclass
class Problem:
    """A question with several competing solution-ideas of differing hidden fitness.
    Lets 'decision quality' diverge from 'convergence speed'."""
    id: int
    solution_ids: list[int]
    best_fitness: float              # for normalizing quality
```

## 5. Agent (`agents.py`)

```python
class EmployeeAgent(Agent):
    def __init__(self, uid, model, team, expertise, attention, absorptive):
        self.team = team
        self.expertise: dict[str, float] = expertise   # domain -> competence (Cohen–Levinthal)
        self.attention = attention                     # send/receive budget per step
        self.absorptive = absorptive                   # base absorption scalar
        self.knowledge: dict[int, KnowledgeItem] = {}
        self.is_bridge: bool = False

    # Two-phase step (see §6): propose, then apply.
    def propose_transmissions(self) -> list["Message"]: ...
    def synthesize(self) -> list[Idea]: ...            # SECI combination, gated by expertise
```

Agents never see `Idea.fitness` — decision quality is measured by the model, not chosen by agents.

## 6. Model & the loop (`model.py`) — the important part

Order-of-activation must not bias diffusion, so each step is **two-phase** (collect all intended messages, then resolve simultaneously):

```python
class Organization(Model):
    def step(self):
        # Phase 0: synthesis (nodes combine held ideas into new ones)
        new_ideas = [i for a in self.agents for i in a.synthesize()]
        self.register_ideas(new_ideas)

        # Phase A: COLLECT — every node proposes sends, bounded by outgoing attention
        messages = []
        for a in self.agents:
            messages += a.propose_transmissions()      # respects send budget

        # Phase B: RESOLVE — group by receiver, bound by incoming attention (← congestion)
        for receiver, msgs in group_by_receiver(messages):
            for msg in receiver.attention.admit(msgs):  # drops overflow -> bridge bottleneck
                rule = self.contagion_for(msg.idea.type)
                rule.apply(msg, receiver, self)          # exposure++, maybe AWARE->HELD

        # Phase C: DECAY — expire ideas past shelf_life
        self.expire_stale()

        # Phase D: MEASURE
        self.datacollector.collect(self)
```

`contagion_for(type)` returns the matching strategy from `contagion.py`. `attention.admit()` is where a bridge that everyone routes through starts dropping messages once demand exceeds its process budget — that's finding #3 emerging mechanically, not by fiat.

## 7. Contagion strategies (`contagion.py`)

```python
class ExplicitContagion:              # simple contagion / independent cascade
    def apply(self, msg, receiver, model):
        p = msg.edge_weight * absorptive_capacity(receiver, msg.idea) * msg.idea.confidence
        if model.rng.random() < p:
            receiver.set_held(msg.idea, model.step_count)
        else:
            receiver.set_aware(msg.idea, model.step_count)   # weak ties still spread awareness

class TacitContagion:                 # complex contagion: threshold + strong-tie gate
    def __init__(self, threshold: int, strong_tie_cutoff: float):
        self.threshold = threshold
        self.cutoff = strong_tie_cutoff
    def apply(self, msg, receiver, model):
        ki = receiver.expose(msg.idea, model.step_count)     # exposures += 1, becomes AWARE
        eligible = ki.exposures >= self.threshold and msg.edge_weight >= self.cutoff
        if eligible:
            p = msg.edge_weight * absorptive_capacity(receiver, msg.idea)
            if model.rng.random() < p:
                receiver.set_held(msg.idea, model.step_count)
```

Consequence built in: thin cross-team bridges (low `edge_weight`) can raise **awareness** of tacit ideas but never flip them to **held** — Hansen 1999 / Centola & Macy 2007, i.e. finding #1.

## 8. Absorption & attention

```python
# absorption.py  (Cohen & Levinthal 1990)
def absorptive_capacity(receiver, idea) -> float:
    related = receiver.expertise.get(idea.domain, 0.0)     # overlap with prior knowledge
    return receiver.absorptive * (BASE + (1 - BASE) * related)   # ~0 if no related knowledge
```

```python
# attention.py  — the scarcity that makes bridges costly
class AttentionBudget:
    def __init__(self, capacity: int):
        self.capacity = capacity
    def admit(self, messages) -> list:      # process at most `capacity`; drop/queue the rest
        return messages[: self.capacity]    # overflow = congestion signal, logged for metrics
```

## 9. Decision quality — how speed and quality decouple

For each `Problem`, the org's current **decision** = the solution its relevant nodes most hold (plurality). Quality = `fitness(decision) / best_fitness`. Because agents adopt on transmission dynamics (who reached them first, how strong the ties) and *cannot see fitness*, a highly connected org can lock onto an early low-fitness solution fast — reproducing Bikhchandani et al. 1992 / Lazer & Friedman 2007 (finding #2). Metric:

```python
def decision_quality(model, problem) -> float:
    counts = model.plurality_counts(problem.solution_ids)  # over relevant nodes
    winner = argmax(counts)
    return model.idea(winner).fitness / problem.best_fitness
```

## 10. Config schema (`config.py`)

```python
@dataclass
class SimConfig:
    # structure
    n_teams: int = 4
    team_size: int = 25
    topology: str = "planted_partition"   # or "er" | "ws" | "ba"
    intra_edge_weight: float = 0.8
    inter_edge_weight: float = 0.2
    n_bridges: int = 4                     # SWEEP
    # ideas
    n_ideas: int = 40
    tacit_fraction: float = 0.5            # SWEEP  (0=all explicit, 1=all tacit)
    n_problems: int = 5                    # competing-solution sets for decision quality
    shelf_life_mean: int = 30
    # agents
    attention_capacity: int = 5            # SWEEP  (scarce vs abundant)
    absorptive_mean: float = 0.6           # SWEEP  (the capability knob)
    tacit_threshold: int = 3
    strong_tie_cutoff: float = 0.5
    # run
    steps: int = 200
    seed: int = 0
```

The primary sweep (`run.py`) is the 3-way grid **`n_bridges × tacit_fraction × attention_capacity`**, which exercises findings 1–3; add `absorptive_mean` vs. connectivity for finding 4.

## 11. Output schema

`DataCollector` emits one tidy row per (run_id, step):

```
run_id, step, seed, <all config knobs>,
holding_convergence, awareness_convergence, freshness,
duplicate_work, conflicting_solutions, cross_team_transmissions,
bridge_load, mean_decision_quality
```

`analysis.py` aggregates across seeds (report medians + IQR, not single runs) and plots each finding.

## 12. Test / validation plan (`tests/`)

- **`test_validation.py::test_small_world`** — build WS graph, assert average shortest-path length drops as rewiring probability rises. Sanity: your graph layer reproduces Watts–Strogatz.
- **`test_validation.py::test_connectivity_accuracy`** — raising connectivity must be *able* to lower `decision_quality` in some regime (reproduces Reina et al. 2024). If it can't, the metric is miswired.
- **`test_contagion.py::test_bridges_help_explicit_not_tacit`** — with all-explicit ideas, more bridges cut convergence time; with all-tacit, they barely move it (finding #1).
- **`test_attention.py::test_bridge_congestion`** — lowering attention capacity on bridges slows org-wide convergence (finding #3).
- Unit tests for `absorptive_capacity` (≈0 with no related expertise) and the tacit threshold gate.

## 13. Build order (milestones)

1. **M1 – Skeleton:** `ideas.py`, `graph_builders.py` (planted-partition + weights + bridges), a no-op `Organization` that builds and renders the graph. Ship `test_small_world`.
2. **M2 – Explicit diffusion:** `EmployeeAgent`, two-phase loop, `ExplicitContagion`, `absorption.py`, holding/awareness metrics. First real runs.
3. **M3 – Tacit + attention:** `TacitContagion`, `AttentionBudget`, congestion logging. Findings 1 & 3 become testable.
4. **M4 – Decision quality:** `Problem` sets, hidden fitness, `decision_quality`. Finding 2 becomes testable.
5. **M5 – Synthesis + sweep:** `synthesis.py`, `run.py` batch grid, `analysis.py` figures. Finding 4; full results.

Each milestone is runnable and produces a metric, so you're never more than one step from a sanity check.
