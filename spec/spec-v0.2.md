# Organizational Information Flow Simulation — Spec v0.2

**Change from v0.1:** AI removed entirely. Every mechanism is now pinned to an established theory of knowledge management or network science. The model is a knowledge-diffusion process on a community-structured graph, where contagion type respects the tacit/explicit split and uptake is gated by absorptive capacity.

---

## Research question

How does organizational **structure** govern the **speed and quality** of information flow — and when do the two trade off against each other?

## Core hypothesis

Communication structure, not node capability, is the primary constraint on organizational performance — **but only for explicit knowledge.** For tacit knowledge, capability and tie strength dominate, and additional bridges do little. The model must be able to show *both* regimes.

---

## 1. Graph model

| Element | Meaning | Grounded in |
|---|---|---|
| Node | One employee | — |
| Edge | Communication channel | — |
| Edge weight | Transmission rate / inverse "stickiness" | Szulanski 1996 |
| Communities | Departments (Finance, Legal, Tech, Ops) | Newman 2003 (modularity) |
| Intra- vs. inter-team weight gap | Knowledge boundary | Carlile 2004 |
| Bridge nodes | PMs, architects, senior leaders | Granovetter 1973; Burt 2004 |

Direction is symmetric in v0.2 (asymmetric deferred).

## 2. Node attributes

| Attribute | Role in model | Grounded in |
|---|---|---|
| Team membership | Community assignment | — |
| Knowledge held | Set of idea IDs the node possesses | — |
| **Absorptive capacity** | Prob. of successfully absorbing a new idea, scaled by overlap with knowledge already held | **Cohen & Levinthal 1990** — this is the "capability" variable that replaces AI |
| Attention capacity | Max transmissions processed per step (scarcity → bridge congestion) | Cross, Rebele & Grant 2016 |
| Domain expertise | Weights which ideas a node can absorb/synthesize | Cohen & Levinthal 1990 |

## 3. Idea attributes

| Attribute | Meaning |
|---|---|
| Unique ID | — |
| **Type: tacit or explicit** | **The key v0.2 addition** — sets the contagion rule (see §4) |
| Initial owner(s) | Seed nodes |
| Business relevance (per node) | Value of the idea to each node/team |
| Shelf life | Steps until expiry (information decay) |
| Confidence | Provenance-weighted trust |
| Source | For trust/provenance |

## 4. Propagation rule (the decision that makes it KM-consistent)

**Two mechanisms, chosen per idea by its type:**

- **Explicit idea → simple contagion (Independent Cascade).**
  One exposure across any edge can transmit, subject to edge weight × receiver's absorptive capacity. Travels fine over weak cross-team bridges.
  *Grounded in:* Kempe–Kleinberg–Tardos 2003; Hansen 1999 (weak ties suffice to transfer explicit knowledge).

- **Tacit idea → complex contagion (threshold + strong-tie requirement).**
  Adoption requires (a) multiple exposures from already-holding neighbors AND (b) sufficiently high edge weight (strong tie). Thin bridges fail to transmit it.
  *Grounded in:* Centola & Macy 2007; Hansen 1999 (strong ties needed for complex transfer); Nonaka 1994 (tacit knowledge resists codified transfer).

**Absorptive-capacity gate (both types):** transmission succeeds with probability proportional to the receiver's related prior knowledge. A node with no adjacent expertise rarely absorbs. *(Cohen & Levinthal 1990.)*

## 5. Simulation cycle

Per time step:
1. Each node evaluates current knowledge.
2. Nodes attempt transmission along edges, **bounded by attention capacity** (a saturated node drops excess — this is where bridges congest).
3. Ideas propagate per §4 (type-appropriate rule, gated by absorptive capacity).
4. Expired ideas (past shelf life) disappear.
5. Nodes may **synthesize** held ideas into new ideas, gated by absorptive capacity and domain expertise (SECI combination step; Nonaka 1994).

## 6. Metrics

**Speed**
- Time to information convergence — split into two, per transactive-memory theory (Wegner 1987):
  - *Holding convergence:* fraction of relevant nodes that **hold** idea X.
  - *Awareness convergence:* fraction that **know where X lives.** (Converges faster; often what orgs actually need.)
- Information freshness (avg. age of held ideas vs. shelf life).

**Quality / cost**
- Duplicate work (independent rediscovery of the same idea in separate communities).
- Number of conflicting solutions coexisting.
- **Decision quality** — wire this so it can *diverge* from convergence speed (see §8).

**Structure use**
- Cross-team transmission frequency.
- Bridge load / congestion (transmissions demanded of bridge nodes vs. their attention capacity).

## 7. Experimental variables

- Team size and number of teams
- Number of bridge nodes
- Communication speed (edge-weight distribution)
- Information shelf life
- **Tacit/explicit mix of ideas** (new — the most important sweep)
- **Absorptive-capacity distribution** (new — the capability knob)
- Attention capacity (scarce vs. abundant)
- Topology (Erdős–Rényi / Watts–Strogatz / Barabási–Albert / planted-community)

## 8. Findings the model must be *capable* of producing

If the model can't produce these even in principle, it can only decorate the hypothesis, not test it:

1. **Bridges help explicit, fail tacit.** More bridges cut convergence time for explicit ideas but barely move tacit ideas (Hansen 1999; Centola & Macy 2007).
2. **Faster convergence, worse decisions.** In some regimes the fastest-converging topology makes the worst collective decisions (Bikhchandani et al. 1992; Lazer & Friedman 2007; Reina et al. 2024).
3. **Bridge congestion.** Under scarce attention, adding load to a few bridge nodes *slows* the org rather than speeding it (Cross et al. 2016).
4. **Capability vs. communication.** A regime where raising absorptive capacity beats improving connectivity — and a regime where the reverse holds.

## 9. Validation plan

- Reproduce Watts–Strogatz small-world path-length collapse as a **sanity check** (known result).
- Reproduce the connectivity → accuracy tradeoff (Reina et al. 2024) in the decision-quality metric.
- Hold to Epstein & Axtell's "grow the phenomenon" standard; document assumptions per Fagiolo et al. 2006 to avoid confirming priors.

## 10. Deferred (future extensions)

Asymmetric communication · trust between nodes · organizational politics · information distortion · incentives · dynamic reorganization. *(AI augmentation intentionally out of scope.)*

---

### Suggested build stack
Python · **NetworkX** (graph + communities) · **Mesa** (agent scheduling) · pandas/matplotlib for metrics. Start with a planted-community graph and an explicit/tacit idea mix; sweep bridge count × tacit fraction × attention capacity first — that 3-way sweep exercises findings 1–3 directly.
