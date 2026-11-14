# SALTBOR Phase 1.13 Performance & Scalability Benchmarks

**Generated**: 2026-11-14T22:19:26Z | **Python**: 3.14.5 | **OS**: win32

## 1. Executive Summary

- **Storage Footprint Reduction**: Achieved **95.55%** reduction in experiment record database size (**22.4× space savings**) by eradicating duplicate source code blobs and adopting the 5-part compact schema with on-demand retrieval.
- **Discrete Stepping Throughput**: Sustained **3043213.6 steps/second** (**0.0003 ms/step**) with all 6 core domains actively executing simultaneously.
- **Bounded-Rational Decision Engine**: Evaluated **18148.2 decisions/second** (**55.1 µs/decision**) across liquidity thresholds and distance decay penalties.
- **Spatial Layering**: Verified zero overhead Layer A immutability guard (**3060912.0 checks/sec**) and high-throughput Layer B authoring (**222326.0 features/sec**).
- **Memory RSS Stability**: Net change across 1,000 tick steps was **93.61 KB** (leak detected: `False`).

## 2. Benchmark Tables

### Multi-Domain Stepping Latency

| Active Domains | Discrete Steps | Total Duration (s) | Latency (ms/step) | Throughput (steps/s) |
| :--- | :--- | :--- | :--- | :--- |
| 1 Domains | 500 | 0.0001s | 0.0001 ms | 9208102.1 steps/s |
| 2 Domains | 500 | 0.0004s | 0.0007 ms | 1352447.9 steps/s |
| 4 Domains | 500 | 0.0002s | 0.0003 ms | 3082613.8 steps/s |
| 6 Domains | 500 | 0.0002s | 0.0003 ms | 3043213.6 steps/s |

### Compact Experiment Database vs. Legacy Bloat

| Metric | Legacy Architecture | Phase 1.13 Compact 5-Part | Improvement |
| :--- | :--- | :--- | :--- |
| Storage per 200 Records | ~7154.6 KB | 318.7 KB | **-95.55%** |
| Code Bloat in DB | Monolithic 1,000-line Blobs | Zero (On-demand Filesystem) | **100% Eradicated** |
| SUMMARY Query Latency | Monolithic Deserialization | Fast Index Filter | **0.92 µs** |
| EVIDENCE Query Latency | Monolithic Deserialization | Metrics Extraction | **0.83 µs** |
| TECHNICAL Query Latency | Monolithic Deserialization | Traceability Schema | **7.93 µs** |

### Contextual Behavior & Spatial Subsystems

| Subsystem Benchmark | Workload | Latency | Throughput |
| :--- | :--- | :--- | :--- |
| Domain Registration | 1,000 domains | 5.26 µs/op | 190038.2 ops/s |
| Activity Catalog Filtering | 5,000 queries | 0.45 µs/query | 2209651.8 queries/s |
| Bounded-Rational Choice | 2,000 decisions | 55.1 µs/decision | 18148.2 decisions/s |
| Layer A Immutability Guard | 1,000 violations | ~0.3 µs/check | 3060912.0 checks/s |
| Layer B Feature Authoring | 1,000 features | 4.5 µs/insert | 222326.0 inserts/s |
| Spatial Bounding Box Filter | Spatial Scan | 149.9 µs | Single Pass Bounding Box |
