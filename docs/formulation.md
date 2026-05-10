# CVRP Mathematical Formulation

This document presents the mixed-integer linear programming (MILP) formulation used in IndustrialOptimizer. The formulation follows the OR(1) "elements of a mathematical program" structure: sets, parameters, variables, objective, and constraints are each defined independently before being composed into the full model.

---

## §1 Elements of the Mathematical Program

### 1.1 Sets

| Symbol | Definition |
|--------|-----------|
| $N = \{0\} \cup C$ | All nodes — depot (index 0) plus customers |
| $C = \{1, \ldots, n\}$ | Customer nodes |
| $A = \{(i,j) \in N \times N : i \neq j\}$ | Directed arc set (no self-loops) |

### 1.2 Parameters

| Symbol | Definition |
|--------|-----------|
| $c_{ij}$ | Euclidean distance from node $i$ to node $j$, for $(i,j) \in A$ |
| $d_i$ | Demand of customer $i \in C$ (depot demand $d_0 = 0$) |
| $Q$ | Vehicle capacity (homogeneous fleet) |
| $K$ | Fleet size (maximum number of vehicles) |

### 1.3 Decision Variables

| Symbol | Domain | Interpretation |
|--------|--------|---------------|
| $x_{ij}$ | $\{0, 1\}$ for all $(i,j) \in A$ | 1 iff the solution uses arc $(i,j)$ |
| $u_i$ | $[d_i,\, Q]$ for all $i \in C$ | Accumulated load upon departing customer $i$ (MTZ auxiliary) |

### 1.4 Objective

$$
\min \sum_{(i,j) \in A} c_{ij}\, x_{ij}
$$

Minimise total Euclidean travel distance across all routes.

### 1.5 Constraints

Constraints are listed individually in §2 with their formal definitions and code-level labels.

---

## §2 Two-Index MTZ Formulation

This is the default formulation implemented in `milp.py:build_cvrp_model` (lines 42–131).

### Objective

$$
\min \sum_{(i,j) \in A} c_{ij}\, x_{ij} \tag{total\_distance}
$$

### Constraints

#### Leave each customer exactly once

$$
\sum_{j \in N \setminus \{i\}} x_{ij} = 1 \quad \forall\, i \in C \tag{leave\_i}
$$

Every customer must be departed from exactly once. Implemented in `milp.py:build_cvrp_model` lines 96–100.

#### Enter each customer exactly once

$$
\sum_{i \in N \setminus \{j\}} x_{ij} = 1 \quad \forall\, j \in C \tag{enter\_j}
$$

Every customer must be arrived at exactly once. Implemented in `milp.py:build_cvrp_model` lines 103–107.

#### Depot out-degree

$$
\sum_{j \in N \setminus \{0\}} x_{0j} \leq K \tag{depot\_out}
$$

At most $K$ vehicles leave the depot. Implemented in `milp.py:build_cvrp_model` lines 110–112.

#### Depot in-degree

$$
\sum_{i \in N \setminus \{0\}} x_{i0} \leq K \tag{depot\_in}
$$

At most $K$ vehicles return to the depot. Implemented in `milp.py:build_cvrp_model` lines 115–119.

#### MTZ subtour elimination and capacity coupling

$$
u_j \geq u_i + d_j - Q(1 - x_{ij}) \quad \forall\, i, j \in C,\; i \neq j \tag{mtz\_i\_j}
$$

This constraint simultaneously:

1. **Eliminates subtours** — if $x_{ij} = 1$ then $u_j \geq u_i + d_j$, imposing a strict ordering on customer visits within a route.
2. **Enforces capacity** — since $u_i \in [d_i, Q]$, the accumulated load can never exceed $Q$.

Implemented in `milp.py:build_cvrp_model` lines 122–128.

#### Variable bounds (implicit constraint)

$$
d_i \leq u_i \leq Q \quad \forall\, i \in C \tag{bounds\_u}
$$

Encoded directly as `lowBound` and `upBound` on the PuLP variable declarations (`milp.py` lines 80–86). The lower bound $d_i$ ensures that the first customer on a route starts with at least its own demand loaded.

---

## §3 Alternative Formulation: Three-Index Vehicle-Indexed

In the three-index formulation, arcs are explicitly assigned to individual vehicles.

### Additional Sets

| Symbol | Definition |
|--------|-----------|
| $V = \{1, \ldots, K\}$ | Vehicle index set |

### Decision Variables

| Symbol | Domain | Interpretation |
|--------|--------|---------------|
| $x_{ijk}$ | $\{0, 1\}$ for all $(i,j) \in A,\; k \in V$ | 1 iff vehicle $k$ traverses arc $(i,j)$ |
| $u_{ik}$ | $[0,\, Q]$ for all $i \in C,\; k \in V$ | Accumulated load on vehicle $k$ upon departing $i$ |

### Objective

$$
\min \sum_{k \in V} \sum_{(i,j) \in A} c_{ij}\, x_{ijk}
$$

### Constraints

#### Each customer visited by exactly one vehicle

$$
\sum_{k \in V} \sum_{j \in N \setminus \{i\}} x_{ijk} = 1 \quad \forall\, i \in C
$$

#### Flow conservation per vehicle

$$
\sum_{j \in N \setminus \{i\}} x_{ijk} = \sum_{j \in N \setminus \{i\}} x_{jik} \quad \forall\, i \in N,\; k \in V
$$

Each vehicle that enters a node must also leave it.

#### Each vehicle departs the depot at most once

$$
\sum_{j \in N \setminus \{0\}} x_{0jk} \leq 1 \quad \forall\, k \in V
$$

#### Each vehicle returns to the depot at most once

$$
\sum_{i \in N \setminus \{0\}} x_{i0k} \leq 1 \quad \forall\, k \in V
$$

#### Capacity per vehicle

$$
\sum_{i \in C} d_i \sum_{j \in N \setminus \{i\}} x_{ijk} \leq Q \quad \forall\, k \in V
$$

#### Subtour elimination (MTZ variant, per vehicle)

$$
u_{jk} \geq u_{ik} + d_j - Q(1 - x_{ijk}) \quad \forall\, i, j \in C,\; i \neq j,\; k \in V
$$

With bounds $d_i \leq u_{ik} \leq Q$.

---

## §4 Trade-Off Discussion

**Variable count.** The two-index MTZ formulation uses $O(n^2)$ binary arc variables and $O(n)$ continuous load variables. The three-index formulation uses $O(n^2 \cdot K)$ binary variables and $O(n \cdot K)$ continuous variables. For a 50-customer, 10-vehicle instance, this means roughly 2,500 binaries (two-index) versus 25,000 binaries (three-index) — an order-of-magnitude difference that directly impacts solver memory and node-processing time.

**LP-relaxation tightness.** The MTZ constraints are known to produce a relatively weak LP relaxation compared to formulations based on capacity cuts or set-partitioning. However, the three-index formulation with MTZ subtour elimination per vehicle does not inherently produce a tighter relaxation — the per-vehicle MTZ constraints are structurally equivalent to the two-index version once the vehicle-assignment is relaxed. Tighter relaxations require cutting-plane methods (e.g., rounded capacity inequalities) regardless of indexing scheme.

**Symmetry.** The three-index formulation introduces vehicle-permutation symmetry: any permutation of vehicle labels $k$ yields an equivalent solution. This symmetry dramatically increases the branch-and-bound search tree, as the solver explores permutations that do not improve the objective. Symmetry-breaking constraints (e.g., lexicographic ordering of vehicle loads) can mitigate this but add complexity. The two-index formulation avoids this problem entirely — vehicles are implicit, distinguished only by the connected components leaving the depot.

**Why MTZ was chosen for v1.** The two-index MTZ formulation offers the best trade-off for an initial implementation: compact model size, straightforward implementation (no cutting-plane callbacks), no vehicle symmetry, and sufficient performance for the small-to-medium instances targeted in Weeks 3–4. A tighter relaxation can be pursued later via valid inequalities layered on top of this base formulation.

---

## §5 Forward References

- **Modelling assumptions and constraint-level commentary**: see [`docs/modeling_note.md`](modeling_note.md).
- **Benchmark results** (solving the MILP, B&B trajectory logging, heuristic comparison): Week 3–4 deliverables.
- **Heuristic formulations** (greedy construction, local search): Week 5–6.
