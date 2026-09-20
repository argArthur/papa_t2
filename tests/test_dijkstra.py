"""Testes Parte 2 — F2.3: dijkstra genérico nas 3 heaps (NÃO entra no zip).

Cobre, para CADA heap_class (BinaryHeap, BinomialHeap, FibonacciHeap):
  - grafo pequeno com resposta manual
  - desconexo (inf/None)
  - peso zero
  - empates (valida custo recalculando, não igualdade exata de pred)
  - fonte única / isolada
  - ValueError em peso negativo
  - ValueError em fonte inválida
  - invariante len(heap)==0 ao fim (via heap instrumentado)
  - diferencial ~200 grafos aleatórios n<=12 vs referência ingênua O(n^2)
    sem heap (só no teste), mesma instância para as 3 heaps, seed fixa.

Determinismo: todo aleatório usa ``random.Random(SEED)`` local com seed
fixa; nenhuma aleatoriedade global.
"""

import math
import random
import sys

import pytest

# Importa do caminho absoluto dos materiais (sem instalar pacote,
# sem tocar na implementação).
sys.path.insert(
    0, "/home/arthur/projects/papa_t2/materiais/Trabalho_Heap_Arquivos_Alunos"
)

from dijkstra import dijkstra  # noqa: E402
from heaps import BinaryHeap, BinomialHeap, FibonacciHeap  # noqa: E402

HEAP_CLASSES = [BinaryHeap, BinomialHeap, FibonacciHeap]
HEAP_IDS = ["BinaryHeap", "BinomialHeap", "FibonacciHeap"]

SEED_DIFF = 20260302
N_DIFF = 200


# ---------------------------------------------------------------------------
# Utilidades (só no teste)
# ---------------------------------------------------------------------------
def _edge_weight(graph, u, v):
    """Peso da aresta (u, v); None se não existe. Se mult, menor peso."""
    best = None
    for vv, w in graph[u]:
        if vv == v and (best is None or w < best):
            best = w
    return best


def _path_cost(graph, pred, source, target):
    """Recalcula o custo do caminho source->target seguindo pred.

    Retorna (custo, ok): ok=False se cadeia inválida (None no meio,
    aresta inexistente, ciclo, não termina em source).
    """
    if target == source:
        return (0.0, pred[target] is None)
    cost = 0.0
    seen = set()
    cur = target
    while cur is not None and cur != source:
        if cur in seen:
            return (math.inf, False)
        seen.add(cur)
        p = pred[cur]
        if p is None:
            return (math.inf, False)
        w = _edge_weight(graph, p, cur)
        if w is None:
            return (math.inf, False)
        cost += w
        cur = p
    if cur != source:
        return (math.inf, False)
    return (cost, True)


def _assert_valid_pred(graph, dist, pred, source):
    """Valida o vetor pred recalculando custos (tolera empates)."""
    n = len(graph)
    assert len(dist) == n
    assert len(pred) == n
    assert pred[source] is None
    assert dist[source] == pytest.approx(0.0)
    for v in range(n):
        if v == source:
            continue
        if math.isinf(dist[v]):
            assert pred[v] is None, f"pred[{v}] deve ser None se inalcançável"
        else:
            assert pred[v] is not None, f"pred[{v}] não pode ser None se alcançável"
            cost, ok = _path_cost(graph, pred, source, v)
            assert ok, f"cadeia de pred até {v} inválida"
            assert cost == pytest.approx(dist[v]), (
                f"custo recalculado {cost} != dist[{v}]={dist[v]}"
            )


def reference_dijkstra(graph, source):
    """Referência ingênua O(n^2) sem heap (só para o teste).

    Seleção linear do não-visitado de menor dist a cada iteração.
    Usada apenas como oráculo de distâncias; preds podem divergir
    em empates (o teste valida preds por custo, não por igualdade).
    """
    n = len(graph)
    if n == 0:
        raise ValueError("empty graph")
    if not isinstance(source, int) or not (0 <= source < n):
        raise ValueError(f"invalid source: {source!r}")
    dist = [math.inf] * n
    pred = [None] * n
    visited = [False] * n
    dist[source] = 0.0
    for _ in range(n):
        u = -1
        best = math.inf
        for i in range(n):
            if not visited[i] and dist[i] < best:
                best = dist[i]
                u = i
        if u == -1:  # resto inalcançável
            break
        visited[u] = True
        for v, w in graph[u]:
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                pred[v] = u
    return dist, pred


def _make_tracked(base):
    """Subclasse instrumentada que registra a instância criada."""
    registry = []

    class Tracked(base):
        def __init__(self):
            super().__init__()
            registry.append(self)

    Tracked._registry = registry  # type: ignore[attr-defined]
    return Tracked


# Casos diferenciais gerados UMA vez no import (mesma instância p/ 3 heaps).
def _gen_diff_cases(n_cases=N_DIFF, seed=SEED_DIFF):
    rng = random.Random(seed)
    cases = []
    for _ in range(n_cases):
        n = rng.randint(1, 12)
        p_edge = rng.choice([0.2, 0.3, 0.4, 0.5])
        graph = []
        for u in range(n):
            adj = []
            for v in range(n):
                if u == v and rng.random() < 0.05:
                    pass  # raramente self-loop; cai no fluxo normal abaixo
                if rng.random() < p_edge:
                    r = rng.random()
                    if r < 0.10:
                        w = 0.0  # peso zero explícito
                    elif r < 0.13:
                        w = -0.0  # zero negativo == 0, aceito pelo contrato
                    else:
                        w = round(rng.uniform(0.0, 20.0), 3)
                    adj.append((v, float(w)))
            graph.append(adj)
        source = rng.randrange(n)
        cases.append((graph, source))
    return cases


_DIFF_CASES = _gen_diff_cases()


# ---------------------------------------------------------------------------
# 1. Grafo pequeno, resposta manual exata
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_grafo_pequeno_resposta_manual(HeapClass):
    # 0->1 (4), 0->2 (1), 2->1 (2), 1->3 (1), 2->3 (5)
    # dist[0]=0; dist[2]=1 via 0; dist[1]=3 via 2; dist[3]=4 via 1.
    graph = [
        [(1, 4.0), (2, 1.0)],
        [(3, 1.0)],
        [(1, 2.0), (3, 5.0)],
        [],
    ]
    dist, pred = dijkstra(graph, 0, HeapClass)
    assert dist == pytest.approx([0.0, 3.0, 1.0, 4.0])
    assert pred == [None, 2, 0, 1]


# ---------------------------------------------------------------------------
# 2. Desconexo: inalcançáveis com inf/None
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_desconexo_inf_none(HeapClass):
    graph = [
        [(1, 2.0)],
        [],
        [(3, 1.0)],
        [],
    ]
    dist, pred = dijkstra(graph, 0, HeapClass)
    assert dist[0] == pytest.approx(0.0)
    assert dist[1] == pytest.approx(2.0)
    assert math.isinf(dist[2]) and math.isinf(dist[3])
    assert pred == [None, 0, None, None]


# ---------------------------------------------------------------------------
# 3. Peso zero (inclui -0.0, que o contrato aceita como 0)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_peso_zero(HeapClass):
    graph = [
        [(1, 0.0), (2, 5.0)],
        [(2, 0.0)],
        [],
    ]
    dist, pred = dijkstra(graph, 0, HeapClass)
    assert dist == pytest.approx([0.0, 0.0, 0.0])
    assert pred == [None, 0, 1]
    _assert_valid_pred(graph, dist, pred, 0)

    # -0.0 deve ser aceito (não é negativo: -0.0 < 0 é False)
    graph_neg0 = [[(1, -0.0)], []]
    dist2, pred2 = dijkstra(graph_neg0, 0, HeapClass)
    assert dist2 == pytest.approx([0.0, 0.0])
    assert pred2 == [None, 0]


# ---------------------------------------------------------------------------
# 4. Empates: validar custo recalculando, não igualdade exata de pred
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_empates_valida_custo(HeapClass):
    # Diamante: dois caminhos mínimos 0-1-3 e 0-2-3, ambos custo 2.
    graph = [
        [(1, 1.0), (2, 1.0)],
        [(3, 1.0)],
        [(3, 1.0)],
        [],
    ]
    dist, pred = dijkstra(graph, 0, HeapClass)
    assert dist == pytest.approx([0.0, 1.0, 1.0, 2.0])
    # Qualquer árvore de caminhos mínimos válida é aceita:
    assert pred[0] is None
    assert pred[1] == 0
    assert pred[2] == 0
    assert pred[3] in (1, 2), f"pred[3]={pred[3]} deve ser 1 ou 2"
    cost, ok = _path_cost(graph, pred, 0, 3)
    assert ok
    assert cost == pytest.approx(dist[3])
    _assert_valid_pred(graph, dist, pred, 0)


# ---------------------------------------------------------------------------
# 5. Fonte única / isolada
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_fonte_unica_grafo_unitario(HeapClass):
    dist, pred = dijkstra([[]], 0, HeapClass)
    assert dist == pytest.approx([0.0])
    assert pred == [None]


@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_fonte_isolada(HeapClass):
    # Fonte 0 sem arestas de saída; componente 1->2 existe mas é
    # inalcançável a partir de 0.
    graph = [[], [(2, 3.0)], []]
    dist, pred = dijkstra(graph, 0, HeapClass)
    assert dist[0] == pytest.approx(0.0)
    assert math.isinf(dist[1]) and math.isinf(dist[2])
    assert pred == [None, None, None]


# ---------------------------------------------------------------------------
# 6. Peso negativo -> ValueError
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_peso_negativo_valueerror(HeapClass):
    graph = [[(1, -1.0)], []]
    with pytest.raises(ValueError):
        dijkstra(graph, 0, HeapClass)
    # Negativo em aresta distante da fonte também deve falhar
    # (validação completa antes de qualquer push).
    graph2 = [[(1, 1.0)], [], [(0, -0.5)]]
    with pytest.raises(ValueError):
        dijkstra(graph2, 0, HeapClass)


# ---------------------------------------------------------------------------
# 7. Fonte inválida -> ValueError (ou exceção)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
@pytest.mark.parametrize(
    "bad_source", [-1, 3, 99, -100, None, "0", 1.5, 2.0, True + 10]
)
def test_fonte_invalida_valueerror(HeapClass, bad_source):
    graph = [[(1, 1.0)], [(2, 1.0)], []]
    with pytest.raises(Exception):  # contrato: ValueError
        dijkstra(graph, bad_source, HeapClass)
    # Reforça que é ValueError nos casos inteiros fora do intervalo
    if isinstance(bad_source, int) and not isinstance(bad_source, bool):
        with pytest.raises(ValueError):
            dijkstra(graph, bad_source, HeapClass)


@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_fonte_invalida_grafo_vazio(HeapClass):
    with pytest.raises(ValueError):
        dijkstra([], 0, HeapClass)


# ---------------------------------------------------------------------------
# 8. Invariante: heap vazio ao fim (via heap instrumentado)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_heap_vazio_ao_fim(HeapClass):
    Tracked = _make_tracked(HeapClass)
    graph = [
        [(1, 4.0), (2, 1.0)],
        [(3, 1.0)],
        [(1, 2.0), (3, 5.0)],
        [],
    ]
    dist, pred = dijkstra(graph, 0, Tracked)
    assert len(Tracked._registry) == 1
    assert len(Tracked._registry[0]) == 0
    assert dist == pytest.approx([0.0, 3.0, 1.0, 4.0])

    # Também no caso desconexo / isolado o heap deve esvaziar.
    Tracked2 = _make_tracked(HeapClass)
    dist2, _ = dijkstra([[], [(2, 3.0)], []], 0, Tracked2)
    assert len(Tracked2._registry) == 1
    assert len(Tracked2._registry[0]) == 0
    assert dist2[0] == pytest.approx(0.0)
    assert math.isinf(dist2[1])


# ---------------------------------------------------------------------------
# 9. Diferencial: ~200 grafos aleatórios n<=12 vs referência O(n^2)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_diferencial_vs_referencia_ingenua(HeapClass):
    assert len(_DIFF_CASES) == N_DIFF
    for idx, (graph, source) in enumerate(_DIFF_CASES):
        assert 1 <= len(graph) <= 12
        ref_dist, _ref_pred = reference_dijkstra(graph, source)
        dist, pred = dijkstra(graph, source, HeapClass)
        # Distâncias devem coincidir (inf incluído).
        assert len(dist) == len(graph)
        for v in range(len(graph)):
            if math.isinf(ref_dist[v]):
                assert math.isinf(dist[v]), f"caso {idx}: dist[{v}] diverge (inf)"
            else:
                assert dist[v] == pytest.approx(ref_dist[v]), (
                    f"caso {idx}: dist[{v}]={dist[v]} != ref={ref_dist[v]}"
                )
        # Preds validados por custo recalculado (tolera empates).
        _assert_valid_pred(graph, dist, pred, source)
