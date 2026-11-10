"""Automated performance and memory benchmarks for Phase 0.6 Knowledge Architecture."""

import time
import tracemalloc
import pytest
from saltbor.knowledge.graph.node import NodeType
from saltbor.knowledge.graph.relationship import RelationshipType
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.reasoning.causal import CausalReasoningEngine


def test_knowledge_graph_scalability_and_memory_budget():
    """Ensure graph construction and per-agent memory consumption remain within strict computational bounds."""
    tracemalloc.start()
    t0 = time.perf_counter()

    # 1. Global World Graph: 500 canonical concepts & 1,500 relationships
    global_kg = GlobalKnowledgeGraph()
    for i in range(500):
        global_kg.register_concept(f"concept_{i}", f"Concept {i}", NodeType.CONCEPT)
    for i in range(1500):
        global_kg.register_relationship(
            f"rel_{i}",
            f"concept_{i % 500}",
            f"concept_{(i * 3 + 1) % 500}",
            RelationshipType.CAUSES,
        )

    t_build_global = (time.perf_counter() - t0) * 1000
    mem_global = tracemalloc.get_traced_memory()[0] / 1024
    tracemalloc.stop()

    assert t_build_global < 250.0  # Must build in under 250ms
    assert mem_global < 5000.0     # Must take under 5MB

    # 2. Epistemic Overlays for 50 Agents
    tracemalloc.start()
    t0 = time.perf_counter()
    agents = []
    for p in range(50):
        ind = IndividualKnowledgeGraph(f"agent_{p}", global_kg)
        for c in range(30):
            ind.learn_concept(f"concept_{(p * 5 + c) % 500}", confidence=0.80)
        agents.append(ind)

    t_build_pop = (time.perf_counter() - t0) * 1000
    mem_pop = tracemalloc.get_traced_memory()[0] / 1024
    tracemalloc.stop()

    mem_per_agent = mem_pop / 50.0
    assert mem_per_agent < 100.0  # Under 100KB per agent overlay
    assert t_build_pop < 200.0    # 50 agents initialized in under 200ms

    # 3. Neighborhood Query Latency
    t0 = time.perf_counter()
    for q in range(2000):
        _ = agents[q % 50].get_neighbors(f"concept_{(q * 5) % 500}")
    t_queries = (time.perf_counter() - t0) * 1000
    avg_query_us = (t_queries / 2000.0) * 1000.0

    assert avg_query_us < 50.0  # Sub-50-microsecond local query latency
