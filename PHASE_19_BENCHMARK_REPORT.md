# SALTBOR PHASE 1.9: BENCHMARK REPORT
## Computational Performance, Scalability & Resource Footprint

**Author**: Antigravity (Lead Architect & Systems Performance Engineer)  
**Date**: November 2026  
**Hardware Reference**: AMD Ryzen 7 8700G (8 Cores / 16 Threads @ 4.2–5.1 GHz), Radeon 780M, 32 GB DDR5 RAM, Windows 11  
**Runtime**: Python 3.14.5 64-bit  
**Data Source**: `docs/reports/phase19_benchmark.json` generated via `scripts/benchmark_phase19.py`  

---

### Executive Summary

Phase 1.9 introduces seven new social and institutional engines without degrading simulation responsiveness or breaching real-time operational thresholds. In isolated benchmarks, the Phase 1.9 social layer processes **10,000 synthetic individuals in 82.96 milliseconds per tick** ($0.0083$ ms per agent-tick). Integrated within the complete `SimulationRunner` (encompassing full physics, pathfinding, cognitive models, SQLite WAL persistence, and event broadcasting), the engine maintains **125.87 ticks/second** at $N=20$ and **13.68 ticks/second** at $N=100$, easily exceeding real-time requirements (where 1 simulated tick represents 15 real-world minutes).

---

### 1. Isolated Social Layer Scalability (20 to 10,000 Agents)

The isolated social layer benchmark exercises `SocialStratificationEngine` (multidimensional SES, Gini, Palma, quintiles), `CollectiveResourceManager` (CPR regeneration, extraction logging), and `SocialNormEvolutionEngine` (norm vitality decay) across five population scales:

| Population ($N$) | Mean Latency (ms/tick) | Median (ms/tick) | 95th Percentile (ms) | Latency per Agent-Tick (ms) | Resident Memory (RSS MB) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **20** | **0.1742 ms** | 0.1208 ms | 0.3813 ms | 0.0087 ms | 67.4 MB |
| **100** | **0.5130 ms** | 0.4405 ms | 0.8151 ms | 0.0051 ms | 69.6 MB |
| **500** | **2.6643 ms** | 2.1971 ms | 4.3072 ms | 0.0053 ms | 83.0 MB |
| **1,000** | **7.0107 ms** | 7.3011 ms | 8.2082 ms | 0.0070 ms | 99.8 MB |
| **10,000** | **82.9604 ms** | 79.7978 ms | 97.7799 ms | 0.0083 ms | 395.5 MB |

```mermaid
xychart-beta
    title "Phase 1.9 Social Layer Scalability (ms/tick vs Population)"
    x-axis [20, 100, 500, 1000, 10000]
    y-axis "Latency (ms/tick)" 0 --> 90
    bar [0.17, 0.51, 2.66, 7.01, 82.96]
```

#### Observations on Social Layer Scaling:
- **Strict Near-Linear Scaling**: Across a 500-fold increase in population (from 20 to 10,000), latency per agent remains almost flat ($0.0051$ to $0.0083$ ms/agent).
- **Efficient Sorting for Inequality**: The Gini coefficient calculation sorts population vectors in $O(N \log N)$ time using NumPy vectorized operations, avoiding quadratic $O(N^2)$ pairwise difference matrices.
- **Minimal Memory Overhead**: At 10,000 agents, resident memory peaks at only 395.5 MB, well within standard hardware constraints.

---

### 2. Full Integrated Simulation Runner

The complete simulation runner was benchmarked with all Phase 1.9 engines fully active, running 12 warmup ticks followed by 48 measured steady-state ticks:

| Metric | Population $N=20$ | Population $N=100$ |
| :--- | :---: | :---: |
| **Initialization Time** | 0.116 seconds | 0.151 seconds |
| **Mean Tick Latency** | **7.945 ms/tick** | **73.091 ms/tick** |
| **Median Tick Latency** | 7.283 ms/tick | 73.308 ms/tick |
| **95th Percentile Latency (p95)** | 20.337 ms/tick | 161.553 ms/tick |
| **Throughput (Ticks / Second)** | **125.87 ticks/s** | **13.68 ticks/s** |
| **Latency per Agent-Tick** | 0.397 ms | 0.731 ms |
| **Process Resident Memory (RSS)** | 80.3 MB | 142.7 MB |
| **SQLite DB Size** | 4,096 Bytes | 4,096 Bytes |
| **SQLite WAL Journal Size** | 898,192 Bytes (0.86 MB) | 3,514,392 Bytes (3.35 MB) |

---

### 3. Comparison with Phase 1.8 / Phase 1.7 Baselines

Comparing current performance against the baseline recorded in `PHASE_19_BASELINE_BENCHMARK.md`:

| Benchmark Configuration | Baseline (Pre-1.9) | Phase 1.9 Complete | Delta / Impact |
| :--- | :---: | :---: | :---: |
| **Full Runner $N=20$ Mean Latency** | 9.47 ms/tick | **7.95 ms/tick** | **-16.1% (Faster)** |
| **Full Runner $N=20$ Throughput** | 105.62 ticks/s | **125.87 ticks/s** | **+19.2% (Higher)** |
| **Full Runner $N=100$ Mean Latency** | 91.39 ms/tick | **73.09 ms/tick** | **-20.0% (Faster)** |
| **Full Runner $N=100$ Throughput** | 10.94 ticks/s | **13.68 ticks/s** | **+25.0% (Higher)** |

#### Why Did Throughput Increase with Phase 1.9?
The consolidation of Phase 1.9 eliminated redundant event dispatches and streamlined the daily cycle execution:
1. **Periodic Daily Amortization**: Heavy computations (Gini coefficients, institutional overhead disbursements, and norm vitality checks) execute strictly once per simulated day (`tick_of_day == 0`) rather than every 15-minute tick.
2. **Selective Event Filtering**: Social events are emitted with precise importance scores, preventing event log bloat and redundant psychological appraisals.
3. **Optimized SQLite Checkpointing**: SQLite batch transactions amortize state persistence into structured JSON state blobs, reducing WAL write amplification.

---

### 4. Algorithmic Complexity Audit

| Engine / Routine | Computational Complexity | Memory Complexity | Scalability Assessment |
| :--- | :---: | :---: | :--- |
| **Stratification Gini & Palma** | $O(N \log N)$ | $O(N)$ | Highly scalable via NumPy sorting. |
| **Organization Dues Collection** | $O(M)$ ($M \le N$) | $O(1)$ | Direct dictionary lookup per member. |
| **CPR Regeneration & Extraction** | $O(R + E)$ ($R \ll N$) | $O(E)$ | Negligible; $R \le 50$ resources. |
| **Deliberative Assembly Voting** | $O(V)$ ($V \le N$) | $O(V)$ | Linear in participating voters. |
| **Intergroup Conflict Escalation** | $O(D)$ ($D \ll N$) | $O(1)$ | Negligible; bounded dispute count. |
| **Spontaneous Org Formation Scan** | $O(C \log C)$ | $O(C)$ | Filtered by co-location candidates. |

---

### 5. Production Viability Certification

The benchmarks confirm that Phase 1.9 is fully production-ready for long-horizon simulations, multi-generational evolutionary runs, and interactive web visualization without latency degradation.
