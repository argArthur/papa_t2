"""Dijkstra parametrizado pela classe da fila de prioridade.

Implementa o algoritmo de E. W. Dijkstra (1959) na formulacao moderna
com fila de prioridade e ``decrease_key`` (cf. Cormen et al., CLRS,
cap. 24, "Single-Source Shortest Paths"): cada vertice possui exatamente
uma entrada no heap, localizada via handle opaco; o relaxamento que
melhora ``dist[v]`` propaga-se com ``decrease_key``.

Segue a pesquisa ``docs/pesquisa_dijkstra_F21.md``: variante (A)
``decrease_key`` + handles, (P1) push de TODOS os vertices, loop ate o
heap esvaziar (sem early-break, sem teste de stale/visitado).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Type

Graph = Sequence[Sequence[tuple[int, float]]]


def dijkstra(
    graph: Graph, source: int, heap_class: Type[Any]
) -> tuple[list[float], list[int | None]]:
    """Retorne (distancias, predecessores) usando heap_class.

    Usa exclusivamente a interface publica do heap (``push`` /
    ``decrease_key`` / ``pop_min`` / ``__len__``); generica em
    ``heap_class`` (sem ramificacao por classe, sem acesso a internals).

    Referencias: Dijkstra, E. W. (1959). *A note on two problems in
    connexion with graphs*. Numer. Math. 1, 269-271; Cormen et al.,
    CLRS, cap. 24 (Dijkstra com PQ) e caps. 6/19/20 (heaps).
    """
    # 1. Tamanho do grafo (Sequence: so len() + indexacao/iteracao).
    n = len(graph)
    if n == 0:
        raise ValueError("invalid graph: empty graph (n == 0)")
    # 2. Fonte valida: int (bool aceito como int, por semantica Python)
    #    em [0, n-1].
    if not isinstance(source, int) or not (0 <= source < n):
        raise ValueError(f"invalid source: {source!r}")

    # 3. Varredura completa de validacao O(n + m), antes de qualquer push:
    #    endpoint em [0, n-1], peso numerico finito, rejeita negativo.
    for u in range(n):
        try:
            adj = graph[u]
        except (IndexError, KeyError, TypeError) as exc:
            raise ValueError(f"invalid graph: bad adjacency at {u}: {exc}") from exc
        try:
            iterator = iter(adj)
        except TypeError as exc:
            raise ValueError(f"invalid graph: adjacency {u} not iterable") from exc
        for edge in iterator:
            try:
                v, w = edge  # type: ignore[misc]
            except (ValueError, TypeError) as exc:
                raise ValueError(f"invalid edge at {u}: {edge!r}") from exc
            if not isinstance(v, int) or not (0 <= v < n):
                raise ValueError(f"invalid endpoint at {u}: {v!r}")
            if not isinstance(w, (int, float)) or w != w or math.isinf(w):
                raise ValueError(f"non-finite weight at ({u}, {v}): {w!r}")
            if w < 0:  #NB: -0.0 < 0 e False, logo -0.0 e aceito (== 0).
                raise ValueError(f"negative weight at ({u}, {v}): {w!r}")

    dist: list[float] = [math.inf] * n
    pred: list[int | None] = [None] * n
    dist[source] = 0

    pq = heap_class()
    handles = [None] * n
    for v in range(n):  # P1: push de todos (source->0, demais->inf).
        handles[v] = pq.push(v, dist[v])

    while len(pq) > 0:  # n pops, sem early-break (heap vazio ao fim).
        u, du = pq.pop_min()
        # Sem teste de stale/visitado: invariante prioridade(v)==dist[v]
        # para v ainda no heap (variante A+P1, pesos >= 0).
        for v, w in graph[u]:
            nd = du + w
            if nd < dist[v]:  # estrito: empate mantem o primeiro pred.
                dist[v] = nd
                pred[v] = u
                pq.decrease_key(handles[v], nd)

    return (dist, pred)
