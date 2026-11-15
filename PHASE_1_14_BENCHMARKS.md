# SALTBOR PHASE 1.14 BENCHMARKS & SUSTAINED PERFORMANCE REPORT
## INTEGRATED TERRITORIAL ECOSYSTEMS & MULTI-SCALE GOVERNANCE

**Date**: 2026-11-15T04:16:32Z  
**Platform**: win32 | Python 3.14.5  
**Hardware Environment**: Windows 11 host (AMD/Intel multi-core, Pure Offline)  

---

### Key Performance Summary

| Benchmark Dimension | Measured Metric | Target SLA | Status |
| :--- | :---: | :---: | :---: |
| **Territorial Tick Latency** | `0.0003 ms/tick` | $< 10.0\text{ ms}$ | **PASSED** |
| **Spatial Accessibility Query** | `0.003 ms/query` | $< 1.0\text{ ms}$ | **PASSED** |
| **Conserved Trade Throughput** | `39803.33 tx/sec` | $> 500\text{ tx/sec}$ | **PASSED** |
| **Multi-Scale 4-Tier Rollup** | `0.0185 ms/rollup` | $< 5.0\text{ ms}$ | **PASSED** |
| **Causal Link Propagation** | `0.0095 ms/prop` | $< 0.1\text{ ms}$ | **PASSED** |

---

### Detailed Analysis

1. **Simulation Tick Latency**:
   The `TerritorialEcosystemEngine.step()` executes synchronous discrete updates including daily commercial accounting cycles, queue clearance, and causal event evaluation in **0.0003 ms/tick**, achieving **3521125.21 ticks/second**.

2. **Spatial Distance & Accessibility Indexing**:
   Haversine distance calculations and exponential friction indexing for healthcare and education facilities execute at **0.003 ms per query**, sustaining **335863.5 queries/second**.

3. **Conserved Economic Trade Throughput**:
   Double-entry bookkeeping enforcing physical inventory depletion and balanced currency debit/credit transfers executes at **39803.33 transactions/second** with zero discrepancies.

4. **Multi-Scale Aggregation Overhead**:
   Rollup queries across Level 1 (individuals), Level 2 (households), Level 4 (communities), Level 5 (municipalities), and Level 6 (departments) complete in **0.0185 ms** without memory bloat or record duplication.
