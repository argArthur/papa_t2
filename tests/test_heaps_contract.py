"""Testes de contrato Parte 1 — F1.3 (NÃO entra no zip).

Cobre, para CADA classe (BinaryHeap, BinomialHeap, FibonacciHeap):
  - push/pop ordenado
  - decrease_key válido
  - ValueError em aumento
  - IndexError em pop_min vazio
  - __len__ correto
  - handles opacos reutilizáveis (mesmo vertex -> múltiplos handles independentes)
  - pop até esvaziar
  - decrease_key após pop deve falhar de forma definida
  - diferencial aleatório (N pushes + decreases válidos) vs sorted de referência

Escolha documentada (decrease após pop):
  Todas as 3 implementações invalidam o handle no pop_min
  (flag ``alive=False``; BinaryHeap também marca index=-1, as demais
  anulam o ponteiro ao nó). Qualquer ``decrease_key`` posterior com esse
  handle lança ``ValueError`` ("already removed"). Este arquivo fixa essa
  escolha com ``test_decrease_apos_pop_falha``.

Determinismo: todo aleatório usa ``random.Random(SEED)`` local com
seed fixa (SEED=20260301); nenhuma aleatoriedade global.
"""

import random
import sys

import pytest

# Importa os heaps do caminho absoluto dos materiais (sem instalar pacote,
# sem tocar na implementação).
sys.path.insert(
    0, "/home/arthur/projects/papa_t2/materiais/Trabalho_Heap_Arquivos_Alunos"
)

from heaps import BinaryHeap, BinomialHeap, FibonacciHeap  # noqa: E402

HEAP_CLASSES = [BinaryHeap, BinomialHeap, FibonacciHeap]
HEAP_IDS = ["BinaryHeap", "BinomialHeap", "FibonacciHeap"]

SEED = 20260301
N_DIFERENCIAL = 200


# ---------------------------------------------------------------------------
# 1. push/pop ordenado
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_push_pop_ordenado(HeapClass):
    h = HeapClass()
    dados = [(3, 30.0), (1, 10.0), (2, 20.0), (0, 5.0), (4, 15.0)]
    for v, p in dados:
        h.push(v, p)
    saida = [h.pop_min() for _ in range(len(dados))]
    # pop_min devolve tuplas (vertex, priority)
    assert all(isinstance(t, tuple) and len(t) == 2 for t in saida)
    prios = [p for _, p in saida]
    assert prios == sorted(prios)
    assert prios == [5.0, 10.0, 15.0, 20.0, 30.0]
    assert len(h) == 0


# ---------------------------------------------------------------------------
# 2. decrease_key válido torna o elemento mínimo
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_decrease_key_valido(HeapClass):
    h = HeapClass()
    h.push(0, 50.0)
    h.push(1, 40.0)
    alvo = h.push(2, 30.0)
    h.push(3, 20.0)
    h.decrease_key(alvo, 1.0)
    v, p = h.pop_min()
    assert (v, p) == (2, 1.0)
    # len não muda com decrease_key
    assert len(h) == 3
    # igualdade é no-op permitido (não deve lançar)
    resto = h.push(4, 99.0)
    h.decrease_key(resto, 99.0)
    assert len(h) == 4


# ---------------------------------------------------------------------------
# 3. aumento -> ValueError
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_decrease_key_aumento_valueerror(HeapClass):
    h = HeapClass()
    handle = h.push(0, 10.0)
    with pytest.raises(ValueError):
        h.decrease_key(handle, 11.0)
    with pytest.raises(ValueError):
        h.decrease_key(handle, 10.0 + 1e-9)
    # prioridade original preservada após tentativa de aumento
    assert h.pop_min() == (0, 10.0)


# ---------------------------------------------------------------------------
# 4. pop em vazio -> IndexError
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_pop_min_vazio_indexerror(HeapClass):
    h = HeapClass()
    assert len(h) == 0
    with pytest.raises(IndexError):
        h.pop_min()
    # continua vazio e reutilizável após a exceção
    h.push(7, 3.0)
    assert h.pop_min() == (7, 3.0)
    with pytest.raises(IndexError):
        h.pop_min()


# ---------------------------------------------------------------------------
# 5. __len__ correto
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_len_correto(HeapClass):
    h = HeapClass()
    assert len(h) == 0
    handles = [h.push(i, float(i)) for i in range(5)]
    assert len(h) == 5
    h.decrease_key(handles[4], -1.0)  # decrease não altera len
    assert len(h) == 5
    h.pop_min()
    assert len(h) == 4
    h.pop_min()
    h.pop_min()
    assert len(h) == 2


# ---------------------------------------------------------------------------
# 6. handles opacos reutilizáveis: mesmo vertex, múltiplos handles independentes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_handles_opacos_reutilizaveis(HeapClass):
    h = HeapClass()
    ha = h.push(0, 10.0)
    hb = h.push(0, 20.0)  # mesmo vertex, segunda entrada independente
    # handles opacos: nunca int bruto, e distintos por push
    assert not isinstance(ha, int)
    assert not isinstance(hb, int)
    assert ha is not hb
    assert len(h) == 2
    # decrease num deles não afeta o outro
    h.decrease_key(hb, 5.0)
    assert h.pop_min() == (0, 5.0)
    assert h.pop_min() == (0, 10.0)
    assert len(h) == 0


# ---------------------------------------------------------------------------
# 7. pop até esvaziar (ordem total + Heap vazio e reutilizável)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_pop_ate_esvaziar(HeapClass):
    h = HeapClass()
    n = 50
    for i in range(n):
        h.push(i, float(n - i))  # ordem reversa de inserção
    assert len(h) == n
    prios = [h.pop_min()[1] for _ in range(n)]
    assert prios == sorted(prios)
    assert len(h) == 0
    with pytest.raises(IndexError):
        h.pop_min()
    # reutilizável após esvaziar
    h.push(99, 1.0)
    assert len(h) == 1
    assert h.pop_min() == (99, 1.0)


# ---------------------------------------------------------------------------
# 8. decrease após pop deve falhar de forma definida (ValueError)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_decrease_apos_pop_falha(HeapClass):
    """Documenta a escolha: handle removido por pop_min é invalidado
    (``alive=False``) e qualquer ``decrease_key`` posterior lança
    ``ValueError`` — nunca sucesso silencioso, nunca IndexError/KeyError.
    """
    h = HeapClass()
    handle = h.push(0, 10.0)
    assert h.pop_min() == (0, 10.0)
    with pytest.raises(ValueError):
        h.decrease_key(handle, 1.0)
    with pytest.raises(ValueError):
        h.decrease_key(handle, 10.0)  # nem mesmo no-op de igualdade
    assert len(h) == 0


# ---------------------------------------------------------------------------
# 9. diferencial aleatório: N pushes + decreases válidos vs sorted (seed fixa)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_diferencial_aleatorio_vs_sorted(HeapClass):
    rng = random.Random(SEED)
    h = HeapClass()
    handles = []
    esperado = {}  # id(handle) -> [vertex, prioridade atual]
    n = N_DIFERENCIAL
    for i in range(n):
        p = rng.uniform(0.0, 1000.0)
        hd = h.push(i, p)
        handles.append(hd)
        esperado[id(hd)] = [i, p]
    assert len(h) == n
    # ~n/2 decreases válidos: new = old - delta positivo (nunca aumento)
    idxs = rng.sample(range(n), n // 2)
    for i in idxs:
        hd = handles[i]
        old = esperado[id(hd)][1]
        new = old - rng.uniform(0.0, 50.0) - 0.001  # garante new < old
        h.decrease_key(hd, new)
        esperado[id(hd)][1] = new
    assert len(h) == n
    referencia = sorted((v for v, _ in esperado.values()), reverse=False)
    # referência por prioridade: multiconjunto ordenado de prioridades
    ref_prios = sorted(p for _, p in esperado.values())
    got = [h.pop_min() for _ in range(n)]
    got_prios = [p for _, p in got]
    assert got_prios == pytest.approx(ref_prios)
    assert sorted(got_prios) == sorted(ref_prios)
    # vértices: o multiconjunto deve coincidir (cada push i distinto)
    assert sorted(v for v, _ in got) == list(range(n))
    assert referencia == sorted(v for v, _ in esperado.values())
    assert len(h) == 0
    with pytest.raises(IndexError):
        h.pop_min()


# ---------------------------------------------------------------------------
# 10. sanidade extra: handle de outro heap / tipo inválido -> ValueError
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("HeapClass", HEAP_CLASSES, ids=HEAP_IDS)
def test_handle_invalido_valueerror(HeapClass):
    h = HeapClass()
    outro = HeapClass()
    bom = h.push(0, 5.0)
    estranho = outro.push(0, 5.0)
    with pytest.raises(ValueError):
        h.decrease_key(estranho, 1.0)  # handle de outro heap
    with pytest.raises(ValueError):
        h.decrease_key(12345, 1.0)  # int bruto não é handle opaco
    with pytest.raises(ValueError):
        h.decrease_key(object(), 1.0)
    # handle válido continua funcional
    h.decrease_key(bom, 2.0)
    assert h.pop_min() == (0, 2.0)
