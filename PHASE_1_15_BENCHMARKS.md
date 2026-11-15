# SALTBOR PHASE 1.15 BENCHMARKS & SUSTAINED PERFORMANCE REPORT
## GENERALIZED TERRITORIAL SCENARIOS, CAUSAL VALIDATION & REAL ENGINE INTEGRATION

**Date**: 2026-11-15T04:58:33Z  
**Platform**: win32 | Python 3.14.5  
**Runtime Architecture**: Pure Offline, Local-First, Zero Remote Dependencies  
**Hardware Environment**: Windows 11 host (AMD/Intel Multi-Core)  

---

### 1. Key Performance Summary

| Benchmark Dimension | Measured Metric | Target SLA | Status |
| :--- | :---: | :---: | :---: |
| **Generalized Scenario Run Latency** | `0.32 ms/run` | $< 25.0\text{ ms}$ | **PASSED** |
| **Scenario Throughput** | `3089.9 runs/sec` | $> 40\text{ runs/sec}$ | **PASSED** |
| **Causal Trace DAG Traversal** | `0.0101 ms/query` | $< 0.10\text{ ms}$ | **PASSED** |
| **DAG Traversal Throughput** | `98965.8 queries/sec` | $> 10,000\text{ q/s}$ | **PASSED** |
| **Economic Ledger Posting** | `152401.4 tx/sec` | $> 20,000\text{ tx/sec}$ | **PASSED** |
| **Ledger Audit Latency (5k tx)** | `0.01 ms` | $< 10.0\text{ ms}$ | **PASSED** |
| **Entity Consistency (5,000 Ind)** | `9.41 ms` | $< 50.0\text{ ms}$ | **PASSED** |
| **Behavioral Coping Evaluation** | `308527.7 evals/sec` | $> 10,000\text{ ev/s}$ | **PASSED** |
| **Multi-Seed 5-Draw Execution** | `2.34 ms/seed` | $< 25.0\text{ ms}$ | **PASSED** |

---

### 2. Scalability Across Population Sizes

The `SharedEntityConsistencyValidator` validates single-source-of-truth invariants and double-entry synchronization without quadratic slowdowns:

| Scale (Individuals) | Households | Businesses | Validation & Sync Time | Throughput | Invariant Check |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **100** | 25 | 2 | `0.15 ms` | `671592.0 ind/sec` | **PASSED** |
| **500** | 125 | 10 | `0.67 ms` | `741620.0 ind/sec` | **PASSED** |
| **1,000** | 250 | 20 | `1.38 ms` | `725795.0 ind/sec` | **PASSED** |
| **5,000** | 1250 | 100 | `9.41 ms` | `531197.0 ind/sec` | **PASSED** |

---

### 3. Detailed Architectural Profiling

1. **Generalized Scenario Execution**:
   A declarative 5-stage scenario running across 6 real subsystems (transport, retail commerce, public education, primary healthcare, household finance, and municipal governance) with causal DAG recording and double-entry ledger settlement executes in **0.32 ms**, enabling interactive web-based counterfactual explorations at **3089.9 scenarios/sec**.

2. **Causal Trace DAG Traversal**:
   Graph path searching, forward impact projection, and backward root-cause tracing with 4-tier epistemic validation execute at **0.0101 ms per query**, sustaining over **98966 traversals/second**.

3. **Verifiable Double-Entry Economic Ledger**:
   Transaction entry processing and real-time ledger accounting maintain conservation with zero currency leakage. Across 5,000 transactions, the ledger achieved **152401.4 tx/second**, and full multi-party conservation auditing completed in **0.01 ms**.

4. **Offline & Deterministic Guarantee**:
   All benchmarks were executed in an isolated local environment with 0 external network requests, 0 telemetry calls, and strictly reproducible fixed-seed pseudorandom generation.
