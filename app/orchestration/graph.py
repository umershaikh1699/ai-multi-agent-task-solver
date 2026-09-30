from __future__ import annotations

from typing import Dict, List, Tuple

from app.models.workflow import WorkflowSpec


def create_adjacency_and_indegree(workflow: WorkflowSpec) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    adjacency: Dict[str, List[str]] = {node.id: [] for node in workflow.nodes}
    indegree: Dict[str, int] = {node.id: 0 for node in workflow.nodes}
    for edge in workflow.edges:
        if edge.source not in adjacency or edge.target not in adjacency:
            raise ValueError(f"Node not found: {edge.source} -> {edge.target}")
        if edge.source == edge.target:
            raise ValueError(f"Self-loop detected: {edge.source}")
        adjacency[edge.source].append(edge.target)
        indegree[edge.target] += 1
    return adjacency, indegree


def layered_toposort(adjacency: Dict[str, List[str]], indegree: Dict[str, int]) -> List[List[str]]:
    current_layer = [node for node, deg in indegree.items() if deg == 0]
    layers: List[List[str]] = []
    processed = 0

    while current_layer:
        layer = current_layer[:]
        layers.append(layer)
        current_layer = []
        for node in layer:
            processed += 1
            for neighbor in adjacency[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    current_layer.append(neighbor)

    if processed != len(indegree):
        unresolved = [node for node, deg in indegree.items() if deg > 0]
        raise ValueError(f"Cycle detected; unresolved nodes: {unresolved}")
    return layers