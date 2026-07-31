# spec.md

**Status:** draft

## Purpose

Build a discrete-time, agent-based simulation that tests how an organization's
communication **structure** governs the **speed and quality** of knowledge
diffusion — and when the two trade off — by spreading tacit vs. explicit ideas
across a community-structured graph under absorptive-capacity and attention
constraints.

## Inputs / Outputs

**Input** — one `SimConfig` value (a typed, immutable config object). Fields and
shapes:

- `n_teams: int`, `team_size: int` — community count and size
- `topology: str` — one of `"planted_partition" | "er" | "ws" | "ba"`
- `intra_edge_weight: float`, `inter_edge_weight: float` — edge weights in
  `(0, 1]`; intra ≥ inter
- `n_bridges: int` — count of designated bridge nodes
- `n_ideas: int` — ideas seeded at start
- `tacit_fraction: float` — share of ideas typed tacit, in `[0, 1]`
  (`0` = all explicit, `1` = all tacit)
- `shelf_life_mean: int` — mean steps until an idea expires
- `attention_capacity: int` — max messages a node processes per step
- `absorptive_mean: float` — mean base absorption scalar in `[0, 1]`
- `tacit_threshold: int` — exposures required before a tacit idea can flip to
  held
- `strong_tie_cutoff: float` — minimum edge weight for tacit transfer
- `steps: int`, `seed: int` — run length and RNG seed

**Output** — a tidy `pandas.DataFrame`, one row per `(run_id, step)`. Columns:
the echoed `SimConfig` knobs plus, per step:

- `holding_convergence: float` — fraction of relevant nodes that **hold** the
  seeded ideas (mean over ideas), in `[0, 1]`
- `awareness_convergence: float` — fraction that are **aware of** the ideas
  (aware-or-held), in `[0, 1]`
- `freshness: float` — mean remaining shelf-life of held ideas, normalized to
  `[0, 1]`
- `cross_team_transmissions: int` — inter-team message deliveries this step
- `bridge_load: float` — mean demand/capacity ratio at bridge nodes
- (later milestones add `duplicate_work`, `conflicting_solutions`,
  `mean_decision_quality`)

Given the same `seed`, the output DataFrame is bit-for-bit reproducible.

## What we produce

library

## Where we persist

file — metrics are emitted as a DataFrame that callers write to CSV/Parquet;
per-run simulation state is otherwise in-memory (stateless between runs).

## Method

rules — an agent-based, network-science simulation. No ML or LLM anywhere; every
mechanism is pinned to an established knowledge-management / network-science
result (Cohen–Levinthal 1990; Hansen 1999; Centola & Macy 2007; Granovetter
1973; Cross et al. 2016; and others — see `spec-v0.2.md`).

## Done criteria

**Graph layer (`graph_builders.py`)**
- `build_graph` on a `planted_partition` config produces exactly
  `n_teams * team_size` nodes, each carrying a `team` attribute.
- Every intra-team edge has `weight == intra_edge_weight`; every inter-team edge
  has `weight == inter_edge_weight`; with `intra > inter`, the mean intra weight
  is strictly greater than the mean inter weight.
- Exactly `n_bridges` nodes are marked as bridges.
- A `topology` outside `{planted_partition, er, ws, ba}` raises `TopologyError`.

**Absorptive capacity (`absorption.py`, Cohen–Levinthal 1990)**
- For a receiver with no expertise in an idea's domain,
  `absorptive_capacity(receiver, idea) == receiver.absorptive * BASE`.
- `absorptive_capacity` is monotonically non-decreasing as the receiver's
  domain expertise rises from `0.0` to `1.0`, reaching `receiver.absorptive` at
  full expertise.

**Explicit contagion (`contagion.py`, Independent Cascade)**
- On one exposure, the receiver becomes `HELD` with probability
  `edge_weight * absorptive_capacity(receiver, idea) * idea.confidence`; when the
  probabilistic draw fails, the receiver becomes `AWARE` (weak ties still spread
  awareness).

**Tacit contagion (`contagion.py`, complex contagion)**
- Each exposure increments the receiver's `exposures` and sets it `AWARE`.
- The receiver can only become `HELD` when `exposures >= tacit_threshold` **and**
  `edge_weight >= strong_tie_cutoff`; below either bound it never becomes `HELD`
  no matter how many exposures accrue.

**Attention / congestion (`attention.py`, Cross et al. 2016)**
- `AttentionBudget(capacity).admit(messages)` returns at most `capacity`
  messages and drops the remainder; the dropped count is recoverable for the
  `bridge_load` metric.

**Model loop (`model.py`)**
- A step is two-phase: all intended messages are collected before any is
  resolved, so per-step outcomes do not depend on agent activation order.
- Ideas whose age exceeds their `shelf_life` are removed during the decay phase.
- `run(steps)` returns a DataFrame with one row per step and the columns listed
  under Outputs.

**Findings the model must be able to produce** (`spec-v0.2.md` §8)
1. **Bridges help explicit, fail tacit.** With all-explicit ideas, increasing
   `n_bridges` lowers the step at which `holding_convergence` crosses a fixed
   threshold; with all-tacit ideas, the same increase barely moves it.
2. **Faster convergence, worse decisions.** There exists a regime in which the
   fastest-converging topology yields the lowest `mean_decision_quality`.
3. **Bridge congestion.** With scarce attention, lowering bridge
   `attention_capacity` raises the step at which org-wide `holding_convergence`
   crosses a fixed threshold (adding load to bridges slows the org).
4. **Capability vs. communication.** There exists a regime where raising
   `absorptive_mean` improves convergence more than adding connectivity, and a
   regime where the reverse holds.

**Validation (`spec-v0.2.md` §9)**
- A Watts–Strogatz graph's average shortest-path length falls as the rewiring
  probability rises (small-world sanity check).
- Raising connectivity is *able* to lower `mean_decision_quality` in some
  regime — the metric can reproduce the connectivity→accuracy tradeoff (Reina
  et al. 2024).

## References

- `spec-v0.2.md` — the research spec: hypothesis, grounding citations, metrics,
  experimental variables, and the four target findings.
- `spec-code.md` — the engineering design: module layout, interface sketches,
  contagion/absorption/attention mechanics, config schema, and build milestones.
- `plan.md` — the recommended incremental build order (foundation first) and the
  framework decision.
