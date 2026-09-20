# Pesquisa Dijkstra — Passo F2.1 (decrease_key vs lazy + casos-limite)

> Natureza: pesquisa registrada para guiar a implementação de `dijkstra.py`.
> Neste passo NENHUM código de `dijkstra.py` foi escrito/alterado (stub intacto).
> Modelo: `materiais/Trabalho_Heap_Arquivos_Alunos/dijkstra.py` (só stub).
> Interface dos heaps: `materiais/Trabalho_Heap_Arquivos_Alunos/heaps.py`.
> Enunciado integral: `materiais/Trabalho_Heap_Enunciado.md` (Parte 2, linhas 42-48 + Premissas).

## 0. Contratos rígidos (copiados do enunciado — não reinterpretar)

- Assinatura: `dijkstra(graph, source, heap_class) -> tuple[dist, pred]`.
- Deve instanciar `heap_class` e usar **exclusivamente** sua interface pública:
  `push(vertex, priority) -> handle`, `decrease_key(handle, new_priority) -> None`,
  `pop_min() -> tuple[vertex, priority]`, `__len__() -> int`.
- **Não duplicar** o algoritmo por heap (uma única função genérica; sem
  `if heap_class == ...`, sem acesso a internals do heap).
- Empate: qualquer árvore de caminhos mínimos válida é aceita.
- Premissas: grafos **direcionados** em lista de adjacência
  `graph[u] = [(v, w), ...]`; vértices `0..n-1`; pesos reais finitos `>= 0`;
  `n = |V|`, `m = |E|`.
- Peso negativo → `ValueError`. Inalcançável → `dist = math.inf`, `pred = None`.
- Parte 3 exige informar a complexidade do Dijkstra "com listas de adjacência
  e `decrease_key`, sem supor que o grafo é conexo" — o que amarra a variante
  (ver §1).

## 1. Variante decidida: decrease_key + handles (NÃO lazy) — justificada

### 1.1 As duas variantes (estado da arte)

- **(A) Com `decrease_key` + handles (CLRS cap. 24, Dijkstra 1959 adaptado a PQ
  moderna):** cada vértice tem exatamente uma entrada no heap, localizada via
  handle opaco; relaxamento que melhora `dist[v]` chama
  `decrease_key(handles[v], nd)`. Cada vértice é extraído exatamente uma vez;
  a primeira extração finaliza a distância (pesos `>= 0`).
- **(B) Lazy / preguiçosa com entradas obsoletas (sem `decrease_key`):** cada
  relaxamento que melhora faz `push(v, nd)` novo, gerando duplicatas; o loop
  descarta entradas obsoletas via teste `if popped_priority != dist[v]: continue`
  (e/ou conjunto `visitado/fechado`). Não usa `decrease_key` nem handles.

### 1.2 Decisão: variante (A), com `decrease_key` + handles

1. **Exigência do enunciado.** A Parte 3 pede explicitamente a análise "com
   listas de adjacência e `decrease_key`". A variante lazy tem outra contagem
   de operações (`n + m` pushes, zero decreases, `n + m` pops candidatos) e
   **não casa** com a tabela pedida (`n` inserts + `n` extract-min + até `m`
   decreases). Escolher lazy quebraria a coerência F2→F3 e arriscaria perder
   os pontos de análise.
2. **Interface disponível.** Os três heaps oferecem `decrease_key(handle, …)`
   com handle opaco justamente para esta variante. Ignorá-los e usar só
   `push`/`pop_min` deixaria um método contratado sem uso e sugeriria ao
   corretor que o aluno não domina handles.
3. **Complexidade e memória.** (A) mantém no máximo `n` entradas no heap;
   (B) pode acumular até `n + m` entradas (uma por relaxamento bem-sucedido),
   piorando memória para `O(n + m)` só na PQ e aumentando o `n` efetivo dos
   `pop_min` para além de `|V|`. A análise canônica `O((m+n) log n)` /
   `O(m + n log n)` supõe (A).
4. **Simplicidade de correção.** Em (A) não há entradas obsoletas: vale o
   invariante `prioridade_no_heap(v) == dist[v]` para todo `v` ainda não
   extraído, e `pop_min` devolve sempre um vértice não finalizado com a menor
   distância provisória — a prova clássica (argumento do corte / "a primeira
   extração é definitiva" para pesos não-negativos) aplica-se sem cláusula
   extra de descarte. Em (B) é preciso provar que o descarte de obsoletas é
   completo (conjunto visitado + comparação de prioridades), um passo a mais
   sem nenhum benefício pedido.
5. **Determinismo do corretor.** (A) extrai exatamente `n` vezes (ou `n`
   vezes salvo interrupção — ver §2); (B) extrai um número dependente dos
   dados (entre `n` e `n + m`), o que dificulta o invariante de teste
   `len(heap) == 0` ao fim e instrumentação de contagem de operações no
   benchmark (Fase 4 relaciona operações dominantes por família).

Conclusão: implementar exclusivamente a variante (A). É vedado introduzir
push duplicado do mesmo vértice, teste de "stale entry" ou conjunto
visitado como mecanismo de correção — com (A) eles são desnecessários
(ver pseudocódigo §4).

## 2. Decisão: push de TODOS os vértices (vs sob demanda) — justificada

### 2.1 As duas opções

- **(P1) Push de todos (`eager`):** antes do loop, `handles[v] = pq.push(v, inf)`
  para todo `v`, depois `decrease_key(handles[source], 0)` — ou
  `push(v, 0 if v == source else inf)` direto. `n` inserts sempre.
- **(P2) Sob demanda (`lazy insertion`):** `push` só do `source`; ao relaxar
  `(u, v)`, se `v` nunca entrou no heap faz `push(v, nd)` e guarda o handle,
  senão faz `decrease_key`. Exige estrutura auxiliar de pertinência
  (`handles[v] is None` / dicionário / conjunto) e, em algumas formulações,
  conjunto fechado para ignorar re-extrações.

### 2.2 Decisão: (P1) push de todos

1. **Casa com a análise pedida.** A derivação canônica conta `n` inserts
   (ver §5). Com (P2) o número de inserts é `|alcançáveis| ≤ n`, e a fórmula
   continuaria válida como cota superior, mas a correspondência direta
   "n pushes" usada no relatório/benchmark ficaria imprecisa. (P1) simplifica
   e casa com `n` inserts.
2. **Simplicidade e robustez.** (P1) elimina toda a lógica de pertinência:
   `handles` é uma lista de tamanho `n` totalmente preenchida antes do loop;
   o relaxamento é sempre `if nd < dist[v]: dist[v] = nd; pred[v] = u;
   decrease_key(handles[v], nd)` — sem ramificação push-vs-decrease, sem risco
   de esquecer um vértice isolado/inalcançável em `dist`/`pred`.
3. **Pós-condição `len(heap) == 0`.** Com (P1) o loop `while len(pq) > 0`
   extrai exatamente `n` vezes e termina com heap vazio sem drenagem extra —
   invariante que os testes F2.3 verificarão. Com (P2), terminar com heap
   vazio também é possível, mas vértices inalcançáveis nunca entram no heap,
   de modo que "extraiu `n` vezes" deixa de valer e o teste precisa de dois
   casos — complexidade gratuita.
4. **Custo assintótico idêntico.** (P1) paga `n` pushes a mais; (P2) economiza
   pushes de inalcançáveis. Ambos são dominados pelo mesmo termo: binário/
   binomial `O(n log n)` de pushes está contido em `O((m+n) log n)`; Fibonacci
   push é `O(1)` amortizado, de modo que (P1) custa só `O(n)` extra — irrelevante
   face a `O(m + n log n)`. Sem supor conexidade (exigência da Parte 3), o termo
   `n` deve permanecer explícito de qualquer forma; (P1) o materializa.
5. **Compatibilidade com `inf` como prioridade inicial.** Os heaps implementados
   (F1.2) aceitam `inf` em `push` (só `NaN` é rejeitado com `ValueError`) —
   ponto aberto de F1.1 §5, aqui **fechado**: `push(v, math.inf)` é permitido e
   será exercitado por (P1). `decrease_key(handle, 0)` a partir de `inf` é uma
   diminuição legítima (não aumento). Nenhuma mudança nos heaps é necessária.
6. **Sem conjunto visitado/fechado.** Com (P1)+(A), cada vértice sai do heap
   uma única vez e em ordem não-decrescente de distância final (pesos `>= 0`);
   não há re-extração a ignorar. Um `if du != dist[u]: continue` de estilo lazy
   seria código morto que mascara bugs (ex.: `decrease` esquecido) — não incluir.

### 2.3 Contraponto registrado (por que não sob demanda)

- (P2) seria preferível se o objetivo fosse economizar pushes em grafos com
  grande fração inalcançável (ex.: `m ≪ n` com fonte isolada) ou se `push`
  fosse caro e `decrease` barato de forma assimétrica extrema. Não é o caso:
  Fibonacci tem push `O(1)`; binário/binomial têm push e decrease no mesmo
  `O(log n)`. A economia de (P2) não muda a classe assintótica e complica o
  código e os testes. Decisão comunicada ao humano conforme WORKFLOW_HEAP.md §
  Orquestrador item 5 (escolha push-todos vs sob demanda).

## 3. Casos-limite mapeados + tratamento decidido

Convenções: `n = len(graph)`; `dist = [math.inf]*n`, `pred = [None]*n`,
`dist[source] = 0`. Comparação de relaxamento estrita: `if nd < dist[v]`
(nunca `<=` — empate mantém o primeiro predecessor, §3.9).

| # | Caso-limite | Exemplo | Tratamento decidido (F2.2 implementará) |
|---|---|---|---|
| 1 | `source` fora de `[0, n-1]` (negativo, `>= n`, não-`int`) | `dijkstra(g, -1, H)`, `dijkstra(g, n, H)` | `ValueError` imediato, antes de instanciar o heap. Justificativa: índice inválido é argumento inválido; `ValueError` mantém a mesma categoria de "argumento inválido" usada para peso negativo e evita colisão com `IndexError` (reservado a `pop_min` em heap vazio). `bool` é subclasse de `int` — aceitar `True` como `1` segue a semântica Python, sem regra especial. |
| 2 | Grafo vazio (`n = 0`, `graph = []`) | `dijkstra([], 0, H)` | `ValueError` (qualquer `source` é inválida quando `n == 0`). Não retornar `([], [])`: sem fonte válida não há origem para `dist[source] = 0`. Checar `n == 0` primeiro. |
| 3 | Fonte isolada (sem arestas de saída; possivelmente grafo sem arestas) | `graph = [[], [], []]`, `source = 1` | Retorno normal: `dist = [inf, 0, inf]`, `pred = [None, None, None]`. O loop extrai os `n` vértices; nenhum relaxamento melhora. |
| 4 | Vértices inalcançáveis em grafo conexo parcial | componente desconexa | Preservar inicialização: `dist[v] = math.inf`, `pred[v] = None`. Nunca chamar `decrease` para eles (handles continuam com `inf`). |
| 5 | Pesos zero | `(v, 0)`, `(v, 0.0)` | **Aceitar.** Dijkstra é correto com zeros (não-negativos). Relaxamento com `nd == dist[v]` não dispara (`<` estrito), evitando decreases inúteis. Cadeias de zeros terminam porque cada vértice é extraído uma vez. |
| 6 | Arestas paralelas (múltiplas `(v, w)` do mesmo `u`) | `[(2, 5), (2, 3)]` | Sem código especial: iterar todas; cada uma é relaxada independentemente; a menor vence pelo `<` estrito. Complexidade conta cada paralela em `m`. |
| 7 | Self-loops `(u, u, w)` | `graph[u] = [(u, 2)]` | Sem código especial: `nd = dist[u] + w >= dist[u]` para `w >= 0`, logo nunca `nd < dist[u]` — no-op correto. Se `w < 0` → `ValueError` (caso 8). |
| 8 | Peso negativo em **qualquer** aresta | `(v, -1)`, `(v, -1e-12)` | `ValueError`. **Varredura completa de validação antes do loop principal** (percorre todas as `n` listas e `m` arestas; custo `O(n + m)`, não muda a classe). Determinístico: falha antes de qualquer `push`, independente da alcançabilidade. Inclui arestas de vértices inalcançáveis — o enunciado diz "o uso de pesos negativos deve ser rejeitado", sem exceção para inalcançável. |
| 9 | `-0.0` | `(v, -0.0)` | **Aceitar** (`-0.0 == 0` em Python, e `-0.0 < 0` é `False`). O teste de validação deve ser `if w < 0: raise`, nunca `if w <= 0` nem teste de sinal por `math.copysign`. Documentar no código. |
| 10 | Peso `math.inf` / `math.nan` / `None` / não-numérico | `(v, inf)`, `(v, nan)`, `(v, None)` | `ValueError` (violam "pesos reais finitos"). Implementação: rejeitar se `not isinstance(w, (int, float))` ou `w != w` (`NaN`) ou `w == inf/-inf` (via `math.isinf`). `None` e strings caem no `isinstance`. `bool` como peso: `True == 1` — aceitar por consistência Python (é `int`), sem regra especial. |
| 11 | Peso `int` vs `float` mistos | `(v, 3)` e `(v, 2.5)` | **Aceitar ambos** sem conversão forçada; `nd = dist[u] + w` e `nd < dist[v]` funcionam em aritmética mista Python. Não usar tolerância epsilon: `1e-12` a mais continua sendo aumento real e `nd < dist` decide sem margem. |
| 12 | Vértice destino inválido (`v` fora de `[0, n-1]`) ou entrada malformada | `(v, w)` com `v = 99`, `v = -1`, `v = "a"` | `ValueError` (grafo malformado) durante a varredura de validação. Motivo: sem essa checagem, o relaxamento causaria `IndexError` obscuro ou corrupção de `dist`. Validar `v` junto com `w` no mesmo passe. |
| 13 | `graph` malformado (não-sequência, linha `None`, tupla sem 2 elementos) | `graph = None`, `graph[u] = None` | `ValueError` ou `TypeError` com mensagem clara — decisão: `ValueError` para uniformizar "entrada inválida" do corretor, exceto `graph` não-iterável que naturalmente levanta `TypeError`. O essencial é **não** retornar resultado silenciosamente errado; falhar rápido. |
| 14 | `dist`/`pred` para inalcançáveis | — | `math.inf` (float, via `math.inf`, não string `"inf"` nem `float('1e999')`) e `None` (singleton, não `-1` nem `float('nan')`). Listas de tamanho exatamente `n`, mutáveis, na ordem dos vértices. |
| 15 | Empate de caminhos (dois predecessores com mesmo custo) | losango `0→1 (1), 0→2 (1), 1→3 (1), 2→3 (1)` | Qualquer `pred[3] ∈ {1, 2}` com `dist[3] == 2`. Implementação usa `<` estrito (primeiro vence, sem churn). Testes F2.3 devem validar **custo** (recalcular `dist` pela cadeia de `pred` ou comparar `dist` com referência), nunca igualdade exata de `pred`. |
| 16 | Cola do heap observa `inf` | `push(v, inf)` inicial | Permitido (heaps aceitam `inf`; só `NaN` é `ValueError`). `pop_min` pode devolver `(v, inf)` para inalcançáveis no fim — correto; **não** interromper o loop cedo (ver §4) para preservar `len(heap) == 0` ao fim. |

Ordem de validação decidida (determinística, F2.2 seguirá):
1. `n = len(graph)`; se `n == 0` → `ValueError`.
2. `source` em `[0, n-1]` (int) → senão `ValueError`.
3. Varredura `u, v, w` de **todas** as arestas: forma de `v`, finitude e
   `w >= 0` → senão `ValueError`. (Custo `O(n + m)`.)
4. Só então inicializar `dist`/`pred`, instanciar o heap e executar Dijkstra.

## 4. Pseudocódigo genérico (só interface pública)

Usa **exclusivamente** `push / decrease_key / pop_min / len`. Nenhum acesso a
atributo interno do heap, nenhuma ramificação por classe de heap, nenhum
`import heapq`.

```text
dijkstra(graph, source, heap_class):
    n = len(graph)
    if n == 0: raise ValueError("empty graph")
    if not isinstance(source, int) or not (0 <= source < n):
        raise ValueError("invalid source")
    for u in range(n):
        for (v, w) in graph[u]:                      # O(n + m)
            if not isinstance(v, int) or not (0 <= v < n):
                raise ValueError("invalid endpoint")
            if not isinstance(w, (int, float))        # bool passa como int
               or w != w                              # NaN
               or w == inf or w == -inf:              # via math.isinf
                raise ValueError("non-finite weight")
            if w < 0:                                # -0.0 passa (== 0)
                raise ValueError("negative weight")

    dist = [inf] * n
    pred = [None] * n
    dist[source] = 0

    pq = heap_class()                                # sem argumentos
    handles = [None] * n
    for v in range(n):                               # n pushes (push-todos, §2)
        handles[v] = pq.push(v, dist[v])             # source→0, demais→inf

    while len(pq) > 0:                               # n iterações, sem early-break
        u, du = pq.pop_min()                         # menor provisório
        # SEM teste de stale/visitado: invariante
        #   du == dist[u]  (variante A+P1 garante; ver nota abaixo)
        for (v, w) in graph[u]:                      # relaxamento
            nd = du + w
            if nd < dist[v]:                         # estrito: empate mantém 1º
                dist[v] = nd
                pred[v] = u
                pq.decrease_key(handles[v], nd)      # nd < antigo ⇒ nunca ValueError

    return (dist, pred)
```

Notas de correção do pseudocódigo:

- **Por que `du == dist[u]` sempre:** indução sobre a extração. Inicialmente
  `prioridade(v) == dist[v]` por construção. Hipótese: antes de cada `pop`,
  `prioridade(x) == dist[x]` para todo `x` no heap. `pop_min` remove o `u` de
  menor prioridade = menor `dist` provisório. Cada relaxamento atualiza
  `dist[v]` e a prioridade atomizadamente via `decrease_key`, preservando a
  igualdade. Logo nenhum `u` extraído precisa de re-exame e nenhum teste de
  obsoleto é necessário. (A prova de otimalidade — "extração em ordem =
  distância final" — usa `w >= 0`, garantido pela validação.)
- **Por que sem `early-break` em `du == inf`:** quando o mínimo é `inf`, todos
  os restantes são inalcançáveis e `dist`/`pred` já estão finais; interromper
  seria correto quanto ao resultado, mas deixaria o heap não-vazio e quebraria
  o invariante de teste `len(pq) == 0` ao fim. Extrai-se tudo (custo extra de
  `pop`s de `inf`, ainda `O(n log n)`, já contabilizado).
- **`decrease_key` nunca levanta por aumento aqui:** só é chamado sob
  `nd < dist[v]`, e `dist[v]` é sempre igual à prioridade corrente do handle
  (argumento acima), logo `nd < prioridade_atual` — diminuição estrita.
  Igualdade (`nd == dist[v]`) não chama nada (no-op evitado no chamador).
- **Empates no heap:** comparação só por prioridade; ordem entre iguais é
  arbitrária — aceita pelo enunciado ("qualquer árvore válida").
- **`len` é `O(1)`** (contador nos heaps F1.2); o `while` não adiciona custo
  assintótico.

## 5. Análise antecipada (para guiar F2.2/F3 — sem implementar aqui)

Contagem de operações de PQ na formulação (A)+(P1), lista de adjacência,
grafo **não necessariamente conexo**:

- Validação prévia: `O(n + m)` tempo, `O(1)` extra — não muda a classe.
- Inicialização `dist`/`pred`/`handles`: `O(n)` tempo e espaço.
- Heap: exatamente `n` × `push`, `n` × `pop_min`, e **até** `m` ×
  `decrease_key` (no máximo um por aresta, pois cada aresta é relaxada uma vez
  — quando sua origem é extraída — e dispara no máximo um `decrease`).
- Espaço do heap: `O(n)` entradas simultâneas (máximo, logo após os pushes).

Custos por heap (convenção do enunciado: pior caso para binário/binomial,
amortizado para Fibonacci — cf. pesquisa F1.1 §4):

| Heap | pushes | pops | decreases | Dijkstra total |
|---|---|---|---|---|
| Binary (pior caso `O(log n)`/op) | `n·O(log n)` | `n·O(log n)` | `≤ m·O(log n)` | `O((m + n) log n)` |
| Binomial (pior caso `O(log n)`/op) | idem | idem | idem | `O((m + n) log n)` |
| Fibonacci (amortizado: push `O(1)`, decrease `O(1)`, pop `O(log n)`) | `n·O(1)` | `n·O(log n)` | `≤ m·O(1)` | `O(m + n log n)` |

Detalhes que a implementação F2.2 deve preservar para a análise valer:

1. **Sem supor conexidade:** manter a forma `m + n` explícita. Em grafo conexo
   `m ≥ n − 1` permitiria simplificar para `O(m log n)` / `O(m + n log n)`,
   mas o enunciado veda a suposição (vale para esparso, denso e desconexo).
2. **Adjacência é essencial:** cada aresta é visitada exatamente uma vez no
   relaxamento (`O(m)` varredura) — com matriz de adjacência seria `O(n²)`.
3. **Casos extremos coerentes:** grafo sem arestas (`m = 0`): `O(n log n)`
   (só pushes+pops) em binário/binomial; `O(n log n)` em Fibonacci (dominado
   pelos pops) — a fórmula geral cobre. Grafo denso (`m = Θ(n²)`): binário
   `O(n² log n)` vs Fibonacci `O(n²)` — a vantagem do Fibonacci aparece nos
   decreases, o que o benchmark F4 deverá exercitar com família densa.
4. **Sem `O(n²)` acidental:** não buscar handle por vértice em lista (`handles`
   indexada por `v` é `O(1)`), não usar `decrease` com busca linear, não
   re-varrer `dist` para achar mínimo. `__len__` é `O(1)` por contador.
5. **Espaço total:** `O(n + m)` do grafo (entrada) + `O(n)` de
   `dist`/`pred`/`handles` + `O(n)` do heap = `O(n + m)`.

## 6. Proibições e armadilhas para F2.2 (registro preventivo)

- Não ramificar por heap (`if heap_class == BinaryHeap…`), não duplicar o
  algoritmo, não importar `heapq`, não acessar `pq._data / pq._roots / pq._min`.
- Não fazer `push` duplicado do mesmo vértice (variante lazy) nem manter
  conjunto `visitado` como mecanismo de correção.
- Não usar `<=` no relaxamento (causa decreases inúteis e troca de `pred` em
  empate; testes validarão custo, mas churn mascara estabilidade).
- Não usar epsilon em floats (`abs(nd - dist[v]) < 1e-9`): corrompe a semântica
  de "aumento" e de `ValueError` em pesos minúsculos, além de decidir empates
  errado.
- Não converter `int → float` à força: `dist` pode conter `int`s e `float`s
  mistos; `math.inf + w` não ocorre no caminho quente (só `du` finito relaxa
  para valor finito; `du == inf ⇒ nd == inf ⇒ nd < dist[v]` falso).
- Não esquecer que `graph` é `Sequence` (pode ser tupla de tuplas) — usar só
  `len()` e indexação/iteração, sem `.append` no grafo.
- Mensagens de `ValueError` devem distinguir "invalid source", "negative
  weight", "non-finite weight", "invalid endpoint" para depuração.

## 7. Decisões congeladas (resumo executável para F2.2)

- [ ] Variante (A) `decrease_key` + handles; nenhum push duplicado, nenhum
  teste de stale, nenhum conjunto visitado.
- [ ] (P1) push de todos os `n` vértices (`source→0`, demais→`inf`); `handles`
  lista de tamanho `n`; loop `while len(pq) > 0` com `n` pops, sem early-break.
- [ ] Validação em 4 passos (§3, ordem fixa): `n == 0` → `source` → varredura
  total `(v, w)` (`ValueError` em endpoint inválido, não-finito ou `w < 0`) →
  inicialização+heap+loop. `-0.0` aceito; `inf`/`NaN`/`None` como peso → `ValueError`.
- [ ] Relaxamento estrito `nd < dist[v]` + `decrease_key` imediato; empate
  mantém primeiro `pred`.
- [ ] Retorno `(dist, pred)` listas de tamanho `n`; inalcançável `inf`/`None`;
  heap vazio ao fim.
- [ ] Complexidades-alvo: binário/binomial `O((m+n) log n)`; Fibonacci
  amortizado `O(m + n log n)`; sem supor conexidade.

## 8. Fontes (sem código copiado — apenas padrões algorítmicos)

- Dijkstra, E. W. (1959). *A note on two problems in connexion with graphs*.
  Numerische Mathematik, 1, 269–271. — algoritmo original; variante com PQ e
  `decrease_key` é a formulação moderna padrão.
- Cormen et al. (CLRS): cap. 24 (*Single-Source Shortest Paths* — Dijkstra com
  PQ, análise `O((m+n) log n)` binário / `O(m + n log n)` Fibonacci); caps. 6,
  19, 20 (heaps binário/binomial/Fibonacci — custos usados em §5).
- Fredman, M. L., & Tarjan, R. E. (1987). *Fibonacci heaps and their uses in
  improved network optimization algorithms*. JACM 34(3). — base do
  `O(m + n log n)`.
- Vuillemin, J. (1978). *A data structure for manipulating priority queues*.
  CACM 21(4). — base do binomial `O((m+n) log n)`.
- Pesquisa anterior: `docs/pesquisa_heaps_F11.md` §§4–5 (tabela de complexidades
  e política de handles/`inf` em `push` — ponto aberto lá, fechado aqui: `inf`
  aceito em `push`, `NaN` rejeitado).

## 9. Rastreabilidade do passo

- Comandos executados (apenas leitura; nenhum código de `dijkstra.py` tocado):
  - Leitura de `materiais/Trabalho_Heap_Enunciado.md` (linhas 42–48 + Premissas),
    `materiais/Trabalho_Heap_Arquivos_Alunos/dijkstra.py` (stub, 14 linhas),
    `materiais/Trabalho_Heap_Arquivos_Alunos/heaps.py` (contratos de
    `push/decrease_key/pop_min/len`, política `NaN→ValueError`/`inf` aceito),
    `docs/pesquisa_heaps_F11.md` (tabela §4 + ponto aberto `inf` §5),
    `WORKFLOW_HEAP.md` (Fase 2.1 + revisão R2.1).
- Arquivo criado neste passo: `docs/pesquisa_dijkstra_F21.md` (este arquivo).
- Arquivos propositalmente NÃO alterados: `materiais/Trabalho_Heap_Arquivos_Alunos/dijkstra.py`,
  `materiais/Trabalho_Heap_Arquivos_Alunos/heaps.py`, nenhum `aluno/*`, nenhum teste.
- DoD: este arquivo existe com decisão justificada (decrease_key+handles §1,
  push-todos §2), casos-limite mapeados + tratamento (§3), pseudocódigo
  genérico só com `push`/`decrease`/`pop`/`len` (§4) e análise antecipada (§5).
