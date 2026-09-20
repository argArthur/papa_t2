"""Implemente as três filas de prioridade sem usar heapq."""

from __future__ import annotations


class _BinaryHandle:
    """Handle opaco de uma entrada do :class:`BinaryHeap`.

    Guarda o índice atual da entrada no array interno, uma flag de
    validade (``alive``) e o heap dono (``owner``). O índice é mutável:
    cada troca no array atualiza o ``index`` dos dois handles
    envolvidos, de modo que ``decrease_key`` localize a entrada em
    O(1) sem busca linear. Nunca usar um ``int`` bruto como handle:
    inteiros copiam por valor e congelam o índice, ficando obsoletos
    após qualquer troca (ver docs/pesquisa_heaps_F11.md, §§1 e 5).
    """

    __slots__ = ("index", "alive", "owner")

    def __init__(self, index: int, owner: BinaryHeap) -> None:
        self.index = index
        self.alive = True
        self.owner = owner

    def __repr__(self) -> str:
        return f"_BinaryHandle(index={self.index}, alive={self.alive})"


class BinaryHeap:
    """Fila de prioridade mínima em array (heap binário).

    Padrão CLRS cap. 6 (Heapsort): heap mínimo indexado em 0 com
    ``parent(i) = (i-1)//2`` e filhos ``2*i+1`` / ``2*i+2``;
    ``sift_up``/``sift_down`` iterativos. A comparação usa apenas a
    prioridade; empates resolvem-se em ordem arbitrária (qualquer
    árvore de caminhos mínimos válida é aceita pelo enunciado).

    Política de handles e exceções (conforme pesquisa §5):
    - ``push`` devolve um handle opaco por entrada; cada ``push``
      gera um handle distinto, mesmo para o mesmo vértice.
    - ``decrease_key`` com aumento (``new > atual``) → ``ValueError``;
      igualdade é no-op permitido; ``NaN`` → ``ValueError``.
    - ``decrease_key`` com handle removido, estranho ou de outro
      heap → ``ValueError``; ``pop_min`` em heap vazio → ``IndexError``.
    """

    def __init__(self) -> None:
        """Cria um heap vazio. Complexidade: O(1)."""
        self._data: list[list] = []  # cada entrada: [vertex, priority, handle]
        self._n: int = 0  # contador para __len__ em O(1)

    def push(self, vertex: int, priority: float) -> _BinaryHandle:
        """Insere ``(vertex, priority)`` e devolve seu handle opaco.

        Complexidade: O(log n) pior caso (append + ``sift_up``).
        Lança ``ValueError`` se ``priority`` for ``NaN``.
        """
        if priority != priority:  # NaN nunca é igual a si mesmo
            raise ValueError("priority must not be NaN")
        handle = _BinaryHandle(len(self._data), self)
        self._data.append([vertex, priority, handle])
        self._n += 1
        self._sift_up(len(self._data) - 1)
        return handle

    def decrease_key(self, handle, new_priority: float) -> None:
        """Reduz a prioridade da entrada de ``handle`` para ``new_priority``.

        Complexidade: O(log n) pior caso (atualização + ``sift_up``).
        Lança ``ValueError`` se o handle for inválido/removido/estranho,
        se ``new_priority`` for ``NaN`` ou se for aumento
        (``new > atual``). Igualdade (``new == atual``) é no-op.
        """
        if not isinstance(handle, _BinaryHandle):
            raise ValueError("invalid handle: not a BinaryHeap handle")
        if handle.owner is not self:
            raise ValueError("invalid handle: from another heap")
        if not handle.alive:
            raise ValueError("invalid handle: already removed")
        if new_priority != new_priority:  # NaN
            raise ValueError("new_priority must not be NaN")
        i = handle.index
        if i < 0 or i >= len(self._data) or self._data[i][2] is not handle:
            raise ValueError("invalid handle: stale index")
        old = self._data[i][1]
        if new_priority > old:
            raise ValueError(f"decrease_key refuses increase: {new_priority} > {old}")
        if new_priority == old:
            return  # no-op permitido
        self._data[i][1] = new_priority
        self._sift_up(i)

    def pop_min(self) -> tuple[int, float]:
        """Remove e devolve ``(vertex, priority)`` da menor prioridade.

        Complexidade: O(log n) pior caso (mover último + ``sift_down``).
        Lança ``IndexError`` se o heap estiver vazio.
        """
        if self._n == 0:
            raise IndexError("pop_min from empty BinaryHeap")
        root = self._data[0]
        last = self._data.pop()
        self._n -= 1
        root[2].alive = False  # invalida o handle da entrada removida
        root[2].index = -1
        if last is not root:
            # Move o último para a raiz e restaura a ordem do heap.
            self._data[0] = last
            last[2].index = 0
            self._sift_down(0)
        return (root[0], root[1])

    def __len__(self) -> int:
        """Número de entradas. Complexidade: O(1) via contador."""
        return self._n

    def _swap(self, i: int, j: int) -> None:
        """Troca as entradas ``i``/``j`` atualizando os handles. O(1)."""
        a = self._data
        a[i], a[j] = a[j], a[i]
        a[i][2].index = i
        a[j][2].index = j

    def _sift_up(self, i: int) -> None:
        """Borbulha a entrada ``i`` até a posição de heap. O(log n)."""
        a = self._data
        while i > 0:
            p = (i - 1) // 2
            if a[i][1] < a[p][1]:
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i: int) -> None:
        """Desce a entrada ``i`` até a posição de heap. O(log n)."""
        a = self._data
        n = len(a)
        while True:
            l = 2 * i + 1
            r = 2 * i + 2
            smallest = i
            if l < n and a[l][1] < a[smallest][1]:
                smallest = l
            if r < n and a[r][1] < a[smallest][1]:
                smallest = r
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest


class _BinomialNode:
    """Nó de árvore binomial (representação filho-irmão, CLRS cap. 19).

    Guarda ``vertex``/``priority`` (conteúdo trocável no ``bubble-up``),
    ``degree`` (ordem da árvore B_degree), ``parent``/``child``/``sibling``
    (filho-irmão CLRS; a lista de raízes do heap é ``list`` Python
    ordenada por grau) e ``handle`` (ponteiro reverso para o handle
    opaco dono desta entrada — permite ao ``bubble-up`` acompanhar o
    handle junto do conteúdo, preservando ``handle → vertex``).
    """

    __slots__ = ("vertex", "priority", "degree", "parent", "child", "sibling", "handle")

    def __init__(self, vertex: int, priority: float) -> None:
        self.vertex = vertex
        self.priority = priority
        self.degree = 0
        self.parent: _BinomialNode | None = None
        self.child: _BinomialNode | None = None
        self.sibling: _BinomialNode | None = None
        self.handle: _BinomialHandle | None = None

    def __repr__(self) -> str:
        return (
            f"_BinomialNode(vertex={self.vertex}, priority={self.priority}, "
            f"degree={self.degree})"
        )


class _BinomialHandle:
    """Handle opaco do :class:`BinomialHeap` (ponteiro para o nó).

    Envolve o ponteiro ``node`` com flag ``alive`` e ``owner``, como no
    padrão da pesquisa F1.1 §5 (``wrapper com .node``). Cada ``push``
    gera um handle distinto. O ``bubble-up`` de ``decrease_key`` troca
    o conteúdo entre nós **e** os vínculos ``handle ↔ node``, de modo
    que cada handle continue representando o mesmo ``vertex`` (estável
    para usos repetidos, como Dijkstra com vários ``decrease``).
    """

    __slots__ = ("node", "alive", "owner")

    def __init__(self, node: _BinomialNode, owner: BinomialHeap) -> None:
        self.node: _BinomialNode | None = node
        self.alive = True
        self.owner = owner

    def __repr__(self) -> str:
        return f"_BinomialHandle(alive={self.alive})"


class BinomialHeap:
    """Fila de prioridade mínima como floresta de árvores binomiais.

    Padrão CLRS cap. 19 (Heaps Binomiais; origem Vuillemin 1978):
    floresta min-heap-ordered com no máximo uma árvore de cada grau
    (invariante restaurado por ``merge`` + ``union`` após cada
    ``push``/``pop_min``). Lista de raízes como ``list`` Python ordenada
    por ``degree``; filhos em representação filho-irmão
    (``child``/``sibling``). Comparação só por ``priority``.

    Política de handles e exceções (conforme pesquisa §5):
    - ``push`` devolve um handle opaco (wrapper com ponteiro ao nó);
      cada ``push`` gera um handle distinto, mesmo para o mesmo vértice.
    - ``decrease_key`` com aumento (``new > atual``) → ``ValueError``;
      igualdade é no-op; ``NaN`` → ``ValueError``.
    - ``decrease_key`` com handle removido, estranho ou de outro
      heap → ``ValueError``; ``pop_min`` em heap vazio → ``IndexError``.
    """

    def __init__(self) -> None:
        """Cria um heap binomial vazio. Complexidade: O(1)."""
        self._roots: list[_BinomialNode] = []
        self._size: int = 0  # contador para __len__ em O(1)

    def push(self, vertex: int, priority: float) -> _BinomialHandle:
        """Insere ``(vertex, priority)`` como singleton e une à floresta.

        Complexidade: O(log n) pior caso (``merge`` + ``union``).
        Lança ``ValueError`` se ``priority`` for ``NaN``.
        """
        if priority != priority:  # NaN nunca é igual a si mesmo
            raise ValueError("priority must not be NaN")
        node = _BinomialNode(vertex, priority)
        handle = _BinomialHandle(node, self)
        node.handle = handle
        self._union_with([node])
        self._size += 1
        return handle

    def decrease_key(self, handle, new_priority: float) -> None:
        """Reduz a prioridade da entrada de ``handle`` para ``new_priority``.

        Borbulha trocando o **conteúdo** (``vertex``, ``priority``) com o
        pai e acompanhando os vínculos ``handle ↔ node``, de modo que
        cada handle continue dono do mesmo ``vertex`` (borbulhar que move
        o nó logicamente). Complexidade: O(log n) pior caso
        (altura ≤ log n).

        Lança ``ValueError`` se o handle for inválido/removido/estranho,
        se ``new_priority`` for ``NaN`` ou se for aumento
        (``new > atual``). Igualdade (``new == atual``) é no-op.
        """
        if not isinstance(handle, _BinomialHandle):
            raise ValueError("invalid handle: not a BinomialHeap handle")
        if handle.owner is not self:
            raise ValueError("invalid handle: from another heap")
        if not handle.alive or handle.node is None:
            raise ValueError("invalid handle: already removed")
        node = handle.node
        if node.handle is not handle:
            raise ValueError("invalid handle: stale handle")
        if new_priority != new_priority:  # NaN
            raise ValueError("new_priority must not be NaN")
        old = node.priority
        if new_priority > old:
            raise ValueError(f"decrease_key refuses increase: {new_priority} > {old}")
        if new_priority == old:
            return  # no-op permitido
        node.priority = new_priority
        # Borbulha: troca conteúdo com o pai e acompanha os handles,
        # para que cada handle siga seu vertex heap acima.
        y = node
        z = y.parent
        while z is not None and y.priority < z.priority:
            y.vertex, z.vertex = z.vertex, y.vertex
            y.priority, z.priority = z.priority, y.priority
            hy = y.handle
            hz = z.handle
            # Troca os vínculos: cada handle segue seu conteúdo.
            y.handle, z.handle = hz, hy
            if hy is not None:
                hy.node = z
            if hz is not None:
                hz.node = y
            y = z
            z = y.parent
        while z is not None and y.priority < z.priority:
            y.vertex, z.vertex = z.vertex, y.vertex
            y.priority, z.priority = z.priority, y.priority
            y = z
            z = y.parent

    def pop_min(self) -> tuple[int, float]:
        """Remove e devolve ``(vertex, priority)`` da menor prioridade.

        Varre as raízes (≤ log n + 1), remove a mínima, reverte a cadeia
        de filhos (grau decrescente → crescente) e faz ``union``.
        Complexidade: O(log n) pior caso.
        Lança ``IndexError`` se o heap estiver vazio.
        """
        if self._size == 0 or not self._roots:
            raise IndexError("pop_min from empty BinomialHeap")
        idx = self._find_min_index()
        min_root = self._roots.pop(idx)
        # Coleta os filhos (cadeia child/sibling em grau decrescente).
        children: list[_BinomialNode] = []
        kid = min_root.child
        while kid is not None:
            nxt = kid.sibling
            kid.parent = None
            kid.sibling = None
            children.append(kid)
            kid = nxt
        min_root.child = None
        children.reverse()  # crescente por grau, pronto para union
        vertex, priority = min_root.vertex, min_root.priority
        victim = min_root.handle  # handle da entrada mínima removida
        if victim is not None:
            victim.alive = False  # invalida o handle removido
            victim.node = None
        min_root.handle = None
        self._size -= 1
        self._union_with(children)
        return (vertex, priority)

    def __len__(self) -> int:
        """Número de entradas. Complexidade: O(1) via contador."""
        return self._size

    @staticmethod
    def _link(y: _BinomialNode, z: _BinomialNode) -> None:
        """Torna ``y`` filho de ``z`` (mesmo grau, ``z`` menor). O(1).

        Pré-condição: ``y.degree == z.degree`` e
        ``z.priority <= y.priority``.
        """
        y.parent = z
        y.sibling = z.child
        z.child = y
        z.degree += 1

    @staticmethod
    def _merge_roots(
        a: list[_BinomialNode], b: list[_BinomialNode]
    ) -> list[_BinomialNode]:
        """Intercala duas listas de raízes ordenadas por grau. O(log n)."""
        out: list[_BinomialNode] = []
        i = j = 0
        while i < len(a) and j < len(b):
            if a[i].degree <= b[j].degree:
                out.append(a[i])
                i += 1
            else:
                out.append(b[j])
                j += 1
        out.extend(a[i:])
        out.extend(b[j:])
        return out

    def _union_with(self, other: list[_BinomialNode]) -> None:
        """Funde ``other`` (ordenado por grau) à floresta. O(log n).

        ``merge`` + passada de consolidação ligando raízes de mesmo grau
        (três casos CLRS: graus distintos; três iguais seguidos; dois
        iguais com próximo diferente).
        """
        roots = self._merge_roots(self._roots, other)
        if not roots:
            self._roots = []
            return
        i = 0
        while i < len(roots) - 1:
            curr = roots[i]
            nxt = roots[i + 1]
            if curr.degree != nxt.degree or (
                i + 2 < len(roots) and roots[i + 2].degree == curr.degree
            ):
                i += 1
            elif curr.priority <= nxt.priority:
                # curr vence: remove nxt e liga sob curr; reavalia em i.
                del roots[i + 1]
                self._link(nxt, curr)
            else:
                # nxt vence: remove curr e liga sob nxt; reavalia em i.
                del roots[i]
                self._link(curr, nxt)
                # roots[i] agora é nxt ligado (grau+1); sem ++i.
                # Sem retrocesso: anterior tem grau < novo grau.
        self._roots = roots

    def _find_min_index(self) -> int:
        """Índice da raiz de menor prioridade. O(log n) (varre raízes)."""
        best = 0
        for i in range(1, len(self._roots)):
            if self._roots[i].priority < self._roots[best].priority:
                best = i
        return best


class _FibNode:
    """Nó do :class:`FibonacciHeap` (padrão CLRS cap. 20 / Fredman–Tarjan 1987).

    Guarda ``vertex``/``priority``, ``degree`` (nº de filhos), ``mark``
    (perdeu um filho sendo não-raiz — arma o corte em cascata),
    ``parent`` (``None`` se raiz), ``children`` (``list`` Python) e
    ``handle`` (ponteiro reverso ao handle opaco dono desta entrada).
    """

    __slots__ = ("vertex", "priority", "degree", "mark", "parent", "children", "handle")

    def __init__(self, vertex: int, priority: float) -> None:
        self.vertex = vertex
        self.priority = priority
        self.degree = 0
        self.mark = False
        self.parent: _FibNode | None = None
        self.children: list[_FibNode] = []
        self.handle: _FibHandle | None = None

    def __repr__(self) -> str:
        return (
            f"_FibNode(vertex={self.vertex}, priority={self.priority}, "
            f"degree={self.degree}, mark={self.mark})"
        )


class _FibHandle:
    """Handle opaco do :class:`FibonacciHeap` (ponteiro para o nó).

    Envolve o ponteiro ``node`` com flag ``alive`` e ``owner``, como no
    padrão da pesquisa F1.1 §5 (``wrapper com .node``). Cada ``push``
    gera um handle distinto. Ao contrário do BinomialHeap, o
    ``decrease_key`` aqui move o próprio nó (corte para a root-list),
    sem trocar conteúdo: o ``node`` do handle permanece estável.
    """

    __slots__ = ("node", "alive", "owner")

    def __init__(self, node: _FibNode, owner: FibonacciHeap) -> None:
        self.node: _FibNode | None = node
        self.alive = True
        self.owner = owner

    def __repr__(self) -> str:
        return f"_FibHandle(alive={self.alive})"


class FibonacciHeap:
    """Fila de prioridade mínima como heap de Fibonacci.

    Padrão Fredman–Tarjan 1987 / CLRS cap. 20: lista de raízes
    (``list`` Python) + ponteiro ``_min`` + ``mark``/``degree`` por nó.
    Comparação só por ``priority``; empates resolvem-se em ordem
    arbitrária.

    Política de handles e exceções (conforme pesquisa §5):
    - ``push`` devolve um handle opaco (wrapper com ponteiro ao nó);
      cada ``push`` gera um handle distinto, mesmo para o mesmo vértice.
    - ``decrease_key`` com aumento (``new > atual``) → ``ValueError``;
      igualdade é no-op; ``NaN`` → ``ValueError``.
    - ``decrease_key`` com handle removido, estranho ou de outro
      heap → ``ValueError``; ``pop_min`` em heap vazio → ``IndexError``.
    """

    def __init__(self) -> None:
        """Cria um heap de Fibonacci vazio. Complexidade: O(1)."""
        self._roots: list[_FibNode] = []
        self._min: _FibNode | None = None
        self._n: int = 0  # contador para __len__ em O(1)

    def push(self, vertex: int, priority: float) -> _FibHandle:
        """Insere ``(vertex, priority)`` na lista de raízes.

        Cria nó com ``degree=0, mark=False``, anexa às raízes e atualiza
        ``_min`` se preciso. Complexidade: O(1) amortizado (O(1) pior
        caso nesta simplificação). Lança ``ValueError`` se ``priority``
        for ``NaN``.
        """
        if priority != priority:  # NaN nunca é igual a si mesmo
            raise ValueError("priority must not be NaN")
        node = _FibNode(vertex, priority)
        handle = _FibHandle(node, self)
        node.handle = handle
        self._roots.append(node)
        if self._min is None or priority < self._min.priority:
            self._min = node
        self._n += 1
        return handle

    def decrease_key(self, handle, new_priority: float) -> None:
        """Reduz a prioridade da entrada de ``handle`` para ``new_priority``.

        Atualiza a prioridade; se o nó for não-raiz e violar a ordem
        min-heap (``new < parent.priority``), aplica ``_cut`` +
        ``_cascading_cut`` iterativo e atualiza ``_min`` se preciso.
        Complexidade: O(1) amortizado (pior caso O(n) na cascata).

        Lança ``ValueError`` se o handle for inválido/removido/estranho,
        se ``new_priority`` for ``NaN`` ou se for aumento
        (``new > atual``). Igualdade (``new == atual``) é no-op.
        """
        if not isinstance(handle, _FibHandle):
            raise ValueError("invalid handle: not a FibonacciHeap handle")
        if handle.owner is not self:
            raise ValueError("invalid handle: from another heap")
        if not handle.alive or handle.node is None:
            raise ValueError("invalid handle: already removed")
        node = handle.node
        if node.handle is not handle:
            raise ValueError("invalid handle: stale handle")
        if new_priority != new_priority:  # NaN
            raise ValueError("new_priority must not be NaN")
        old = node.priority
        if new_priority > old:
            raise ValueError(f"decrease_key refuses increase: {new_priority} > {old}")
        if new_priority == old:
            return  # no-op permitido
        node.priority = new_priority
        parent = node.parent
        if parent is not None and node.priority < parent.priority:
            self._cut(node)
            self._cascading_cut(parent)
        if self._min is None or node.priority < self._min.priority:
            self._min = node

    def pop_min(self) -> tuple[int, float]:
        """Remove e devolve ``(vertex, priority)`` da menor prioridade.

        Move os filhos de ``_min`` para a lista de raízes (limpando
        ``parent``/``mark``), remove ``_min``, invalida seu handle e, se
        restarem nós, executa ``_consolidate`` para refundir graus iguais
        e reencontrar o mínimo. Complexidade: O(log n) amortizado
        (pior caso O(n) se a root-list degenerar). Lança ``IndexError``
        se o heap estiver vazio.
        """
        if self._n == 0 or self._min is None:
            raise IndexError("pop_min from empty FibonacciHeap")
        z = self._min
        # Move cada filho de z para a root-list.
        for child in z.children:
            child.parent = None
            child.mark = False
            self._roots.append(child)
        z.children = []
        # Remove z da root-list por identidade.
        for i, r in enumerate(self._roots):
            if r is z:
                del self._roots[i]
                break
        vertex, priority = z.vertex, z.priority
        victim = z.handle
        if victim is not None:
            victim.alive = False  # invalida o handle removido
            victim.node = None
        z.handle = None
        self._n -= 1
        if self._n == 0:
            self._roots = []
            self._min = None
        else:
            self._min = None
            self._consolidate()
        return (vertex, priority)

    def __len__(self) -> int:
        """Número de entradas. Complexidade: O(1) via contador."""
        return self._n

    def _link(self, y: _FibNode, x: _FibNode) -> None:
        """Torna ``y`` filho de ``x`` (``x`` menor). O(1).

        Pré-condição: ``x.priority <= y.priority``. Remove ``y`` da
        lógica de raízes (o chamador reconstrói a root-list), anexa aos
        filhos de ``x``, incrementa ``x.degree`` e limpa ``y.mark``.
        """
        y.parent = x
        x.children.append(y)
        x.degree += 1
        y.mark = False

    def _cut(self, x: _FibNode) -> None:
        """Corta ``x`` do pai e move para a root-list. O(1) amortizado.

        Remove ``x`` dos filhos do pai, decrementa ``parent.degree``,
        limpa ``x.parent``/``x.mark`` e anexa ``x`` às raízes.
        Pré-condição: ``x.parent`` não é ``None``.
        """
        p = x.parent
        if p is not None:
            try:
                p.children.remove(x)
            except ValueError:
                pass
            p.degree -= 1
        x.parent = None
        x.mark = False
        self._roots.append(x)

    def _cascading_cut(self, y: _FibNode | None) -> None:
        """Cascata iterativa de cortes subindo aos avôs. O(1) amortizado.

        Enquanto ``y`` for não-raiz marcada, corta ``y`` e sobe ao avô;
        se ``y`` for não-raiz não-marcada, marca e para; se for raiz,
        para. Iterativo (``while``) para evitar ``RecursionError`` em
        cadeias longas.
        """
        while y is not None:
            if y.parent is None:
                break  # y é raiz: nada a fazer
            if not y.mark:
                y.mark = True
                break
            z = y.parent
            self._cut(y)
            y = z

    def _consolidate(self) -> None:
        """Funde raízes de mesmo grau via array por grau. O(n) pior caso.

        Padrão CLRS ``FIB-HEAP-CONSOLIDATE``: array ``A`` indexado por
        grau (dimensionado por ``n.bit_length()*2``, estendido sob
        demanda); para cada raiz ``x`` (sobre cópia da lista), enquanto
        ``A[d]`` ocupado por ``y``, faz ``link`` (menor vira pai) e
        ``d += 1``; reconstrói a root-list a partir de ``A`` e reencontra
        ``_min`` por varredura. Amortizado O(log n).
        """
        if not self._roots:
            self._min = None
            return
        size = max(16, self._n.bit_length() * 2 + 1)
        A: list[_FibNode | None] = [None] * size
        for x in list(self._roots):
            d = x.degree
            while True:
                if d >= len(A):
                    A.extend([None] * (d - len(A) + 1))
                if A[d] is None:
                    break
                y = A[d]
                assert y is not None
                A[d] = None
                # Menor vira pai; empate: x permanece pai (estável).
                if y.priority < x.priority:
                    x, y = y, x
                self._link(y, x)
                d += 1
            if d >= len(A):
                A.extend([None] * (d - len(A) + 1))
            A[d] = x
        self._roots = [node for node in A if node is not None]
        self._min = self._find_min()

    def _find_min(self) -> _FibNode | None:
        """Raiz de menor prioridade (varredura). O(nº de raízes)."""
        best: _FibNode | None = None
        for r in self._roots:
            if best is None or r.priority < best.priority:
                best = r
        return best

