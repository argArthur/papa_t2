# Pesquisa Heaps — Passo F1.1 (guia de implementação, sem código final)

> Natureza: pesquisa registrada para guiar a implementação de `heaps.py`.
> Neste passo NENHUM código de `heaps.py` foi escrito/alterado.
> Modelo preservado em `materiais/Trabalho_Heap_Arquivos_Alunos/heaps.py`.
> Enunciado integral em `materiais/Trabalho_Heap_Enunciado.md`.

## 0. Contratos rígidos (copiados do enunciado — não reinterpretar)

- Python ≥ 3.11 (ambiente verificado: `.venv` com Python 3.12.3).
- Grafos direcionados em lista de adjacência `graph[u] = [(v, w), ...]`.
- Vértices `0..n-1`; `n = |V|`, `m = |E|`; pesos reais finitos `>= 0`.
- Peso negativo → `ValueError`; inalcançável → `dist = inf`, `pred = None`.
- Parte 1 (`heaps.py`): classes `BinaryHeap`, `BinomialHeap`, `FibonacciHeap` com:
  ```python
  push(vertex, priority) -> handle
  decrease_key(handle, new_priority) -> None
  pop_min() -> tuple[vertex, priority]
  __len__() -> int
  ```
- `push` retorna `handle` opaco, aceito depois por `decrease_key`.
- Só diminuem: tentativa de aumento → `ValueError`.
- `pop_min` em estrutura vazia → `IndexError`.
- Proibido `heapq` ou PQ pronta nas 3 classes; auxiliares `list`/`dict` permitidos.
- Código deve ser autoral + referências. Não copiar código externo.

## 1. BinaryHeap — padrão CLRS cap. 6

### Estrutura decidida
- Array-based (lista Python `self._a: list[Entry]`), heap mínimo indexado em 0.
- `Entry = [priority, vertex, handle]` ou objeto equivalente; `handle` é **objeto mutável opaco** com campo `index`, nunca índice bruto (`int`).
- Mapa implícito: `handle.index` → posição em `self._a`. Não usar `dict vertex→índice` como fonte única, porque Dijkstra + testes podem ter `push` duplicado do mesmo `vertex` (cada `push` = entrada distinta, cada uma com seu `handle`). Se for mantido `dict` auxiliar, chavear por `id(handle)`, não por `vertex`.
- Contador `self._n` para `__len__` em O(1). Alternativa `len(self._a)` também é O(1), mas contador explícito evita ambiguidade durante `pop_min`.
- Comparação só por `priority`; empate: qualquer ordem é válida (enunciado aceita qualquer árvore de caminhos mínimos válida). Não desempatar por `vertex` a menos que se queira determinismo para testes — se desempatar, documentar.

### Operações (padrão CLRS: `HEAP-INCREASE` invertido / `MIN-HEAPIFY`)
- `push(vertex, priority)`: append no fim + `sift_up`. O(log n) pior caso.
- `decrease_key(handle, new_priority)`:
  1. validar handle (ver §5);
  2. se `new_priority > entry.priority` → `ValueError` (aumento). `==` é no-op permitido (não é aumento);
  3. atualizar `entry.priority`, `sift_up(handle.index)`. O(log n) pior caso.
- `pop_min()`:
  1. se vazio → `IndexError`;
  2. salvar raiz; mover último para raiz (se só havia 1, só remover);
  3. `sift_down(0)`; invalidar handle da raiz removida (ver §5); decrementar contador. O(log n) pior caso.
- `sift_up(i)`: enquanto `i>0` e `a[i] < a[parent(i)]`, troca e atualiza `handle.index` dos dois lados.
- `sift_down(i)`: enquanto existir filho menor, troca com o menor filho e atualiza índices.
- `parent(i) = (i-1)//2`, `left = 2*i+1`, `right = 2*i+2`. Iterativo, sem recursão.

### Por que handle = objeto mutável com índice
- Permite `decrease_key` O(log n) sem busca linear.
- Cada `swap` atualiza `handle.index` — esquecer uma atualização corrompe o heap silenciosamente (principal bug).
- Nunca expor/aceitar `int` como handle: `int` copia por valor e congela o índice; após qualquer `swap`/`pop` ele fica obsoleto sem como detectar.

## 2. BinomialHeap — padrão CLRS cap. 19 / Vuillemin 1978

### Estrutura decidida
- Floresta de árvores binomiais min-heap-ordered. Cada nó:
  - `vertex, priority, degree, parent, child, sibling` (representação filho-irmão CLRS) **ou** `children: list` (mais idiomático em Python, igualmente correto se `merge`/`link` preservarem grau e ordem).
  - Decisão recomendada: `child/sibling` se fidelidade máxima ao CLRS; `children: list` se legibilidade (custo de `merge` continua O(log n)). Registrar a escolha no relatório.
- Lista de raízes mantida como lista Python (`self._roots: list[Node]`).
- `handle = ponteiro para o Node` (objeto opaco). Não é índice, não é `vertex`.
- Invariante: no máximo uma árvore de cada grau na floresta (restaurado por `merge`/`union` após cada `push`/`pop_min`).
- Contador `self._n` para `__len__` O(1).

### Operações (padrão CLRS `BINOMIAL-HEAP-MERGE` + `UNION`)
- `link(y, z)`: torna `y` filho de `z` (assume mesma `degree` e `z.priority <= y.priority`); `z.degree += 1`. O(1).
- `merge(h1_roots, h2_roots)`: intercala duas listas de raízes ordenadas por `degree`. O(log n).
- `union`: `merge` + passada de consolidação ligando raízes de mesmo grau (três casos CLRS: graus distintos; três iguais seguidos; dois iguais com próximo diferente). O(log n).
- `push(vertex, priority)`: cria singleton (`degree=0`) e faz `union` com a floresta. O(log n) pior caso.
- `decrease_key(handle, new_priority)`:
  1. validar handle (ver §5);
  2. se aumento → `ValueError`;
  3. atualizar prioridade e borbulhar (`bubble-up`): enquanto `node.parent` e `node.priority < parent.priority`, trocar **conteúdo** (`vertex, priority`) entre nó e pai — ou trocar ponteiros, mas trocar conteúdo preserva identidade do `handle` (o chamador segura o mesmo objeto). Recomendado: trocar conteúdo + manter `handle→Node` estável. O(log n) pior caso (altura ≤ log n).
  4. Decisão: após `bubble-up`, o `handle` continua apontando para o mesmo objeto `Node` (agora mais acima). Alternativa (trocar objetos) exige re-mapear handles — mais frágil. Documentar a opção.
- `pop_min()`:
  1. se vazio → `IndexError`;
  2. varrer raízes para achar mínimo O(log n) (nº de árvores ≤ log n + 1);
  3. remover a raiz mínima da lista de raízes; coletar seus filhos, reverter a ordem (filhos estão em grau decrescente; reversão deixa crescente para `union`) e fazer `union`;
  4. invalidar handle do nó removido; `self._n -= 1`. O(log n) pior caso.

### Notas de fidelidade
- Vuillemin 1978 introduz a árvore binomial como estrutura de PQ; CLRS formaliza `merge`/`union`/`extract-min`/`decrease-key` usados aqui.
- `push` como `merge singleton` (não inserção direta ordenada) é o que garante o invariante de graus únicos.

## 3. FibonacciHeap — padrão Fredman–Tarjan 1987 / CLRS cap. 20

### Estrutura decidida
- `Node`: `vertex, priority, degree, mark: bool, parent, children: list | child-pointer, left/right` (lista circular duplamente ligada CLRS) **ou** simplificação segura: `root-list` como `list[Node]` Python + `children` como `list[Node]` Python.
- Simplificação segura em Python (permitida pela tarefa): lista Python para `root-list` é OK **se** `consolidate` estiver correta (array por grau + `link`) e `min` for mantido/atualizado. Não simplificar: lógica de `mark`, `cut`/`cascading-cut`, `link` por grau, nem o varrimento de `consolidate`.
- `handle = ponteiro para o Node`.
- Campos por heap: `self._min: Node | None`, `self._n: int` (contador → `__len__` O(1)), `self._roots: list`.
- `mark=False` em raiz; `mark` só faz sentido para não-raiz.

### Operações (padrão CLRS `FIB-HEAP-*`)
- `push(vertex, priority)`: cria nó (`degree=0, mark=False`), adiciona à `root-list`, atualiza `min` se menor, `n+=1`. O(1) amortizado (O(1) pior caso nesta simplificação).
- `decrease_key(handle, new_priority)` O(1) amortizado:
  1. validar handle;
  2. se aumento → `ValueError`;
  3. atualizar prioridade; se `node` é raiz, só atualizar `min` se preciso;
  4. senão, se viola ordem (`node.priority < parent.priority`): `cut(node)` + `cascading_cut(parent)`:
     - `cut(x)`: remove `x` da lista de filhos do pai, decrementa `parent.degree`, move `x` para `root-list`, `x.parent=None`, `x.mark=False`;
     - `cascading_cut(y)`: se `y` é raiz → nada; se `y.mark==False` e não-raiz → `y.mark=True`; senão → `cut(y)` + recursão/loop no avô.
  5. atualizar `min` se `new_priority < min.priority`.
  - Implementar cascata com `while`, não recursão (profundidade pode ser O(n) em caso degenerado; limite de recursão Python + overhead).
- `pop_min()` O(log n) amortizado:
  1. se `_min is None` → `IndexError`;
  2. mover cada filho de `_min` para `root-list` (limpar `parent`, `mark=False`);
  3. remover `_min` da `root-list`; invalidar seu handle; `n-=1`;
  4. se heap ficou vazio → `_min=None`, retornar;
  5. senão → `consolidate()`: array `A` indexado por grau (tamanho ≈ O(log n), alocar `n.bit_length()+extra` ou redimensionar sob demanda); para cada raiz `x`, enquanto `A[d]` ocupado por `y`: `link` (menor vira pai, maior vira filho, `degree+=1`, `mark=False` no filho), `d+=1`; reconstruir `root-list` a partir de `A` e reachar `min` por varredura.
- `__len__`: retorna `self._n`. O(1). Nunca `len(root-list)` nem travessia.

### Cuidados específicos Python
- `consolidate` deve iterar sobre **cópia** da `root-list` (a lista é mutada durante `link`).
- Grau máximo: cota de Fibonacci `D(n) ≤ log_φ n ≈ 1.44 log2 n`; array com `~64` posições cobre qualquer `n` prático em 64-bit; preferir dimensionamento por `n.bit_length()*2` para segurança.
- Comparação de `float`/`int` misto: só `<`/`>` diretos; não usar tolerância epsilon (enunciado: pesos reais finitos; aumento de `1e-12` continua sendo aumento → `ValueError`).
- `mark` de filho recém-`link`ado deve ser `False` (esquecer isso quebra o amortizado e pode causar cortes espúrios).

## 4. Complexidades por método (para guiar `respostas.json` — Parte 3)

> Convenção do enunciado Parte 3: pior caso para binário e binomial; amortizado para Fibonacci. A tabela abaixo já separa as duas leituras para não confundir implementação com análise.

| Heap | `push` | `decrease_key` | `pop_min` | `__len__` |
|---|---|---|---|---|
| Binary (pior caso) | O(log n) | O(log n) | O(log n) | O(1) |
| Binomial (pior caso) | O(log n) | O(log n) | O(log n) | O(1) |
| Fibonacci (amortizado) | O(1) | O(1) | O(log n) | O(1) |
| Fibonacci (pior caso, referência) | O(1) | O(n)¹ | O(n)² | O(1) |

¹ `decrease_key` Fibonacci pior caso O(n) se cascata percorre cadeia longa (amortizado O(1) pelo método do potencial — créditos nos `mark`).
² `pop_min` Fibonacci pior caso O(n) se `root-list` degenera (amortizado O(log n) após `consolidate`).

Consequência para Dijkstra (lista de adjacência + `decrease_key`, grafo não necessariamente conexo — antecipação para Parte 3, sem implementar aqui):
- Binary/Binomial: O((n + m) log n).
- Fibonacci (amortizado): O(m + n log n).
- Detalhe: sem supor conexidade, o termo `n` de inicialização/`push` não é absorvido por `m`; manter forma `n + m` explícita.

## 5. Política de handles inválidos (decisão — aplicar igual nas 3 classes)

### O que é o handle
- Objeto opaco retornado por `push`. O chamador nunca constrói/inspeciona; só repassa a `decrease_key`.
- Binary: objeto com `index` mutável + referência ao heap dono + flag `_alive`.
- Binomial/Fibonacci: o próprio `Node` (ou wrapper com `.node`), mais referência ao heap dono + flag `_alive`.
- Cada `push` gera um handle distinto, mesmo para o mesmo `vertex` (entradas duplicadas são independentes).

### Transições de validade
- `push` → handle válido (`_alive=True`, `owner=heap`).
- `pop_min` → handle da entrada removida passa a `_alive=False` (invalidação imediata). Demais handles continuam válidos (no binário, com `index` atualizado pelos `swap`/`move`).
- Nunca reutilizar handle removido para nova entrada.

### Casos e comportamento decidido
| Caso | Comportamento |
|---|---|
| `decrease_key(handle, new)` com `new > old` (qualquer handle válido) | `ValueError` (exigência do enunciado) |
| `decrease_key` com handle já removido por `pop_min` (`_alive=False`) | `ValueError` (handle inválido; não é aumento, é uso após remoção — `ValueError` mantém categoria "argumento inválido" e evita colisão com `IndexError` reservado a `pop_min` em heap vazio) |
| `decrease_key` com handle estranho (`None`, tipo errado, de outro heap, ou forjado) | `ValueError` |
| `decrease_key` com `new == old` em handle válido | no-op permitido (não é aumento) |
| `decrease_key` com `NaN`/`inf` como `new_priority` | tratar como aumento se `new > old` → `ValueError`; `NaN` nunca satisfaz `<`/`>` — rejeitar explicitamente com `ValueError` (prioridades devem ser reais finitos no contexto do trabalho) |
| `pop_min` em heap vazio | `IndexError` (exigência do enunciado) |
| `push` com prioridade `NaN`/`inf` | rejeitar com `ValueError` (coerente com "pesos reais finitos"; evita envenenar comparações) — documentar no relatório se o corretor testar `inf` como prioridade inicial de Dijkstra (nesse caso, rever: Dijkstra usa `inf` como distância inicial; se `push(v, inf)` for necessário, aceitar `inf` no `push` mas rejeitar `NaN`. **Decisão pendente de verificação contra `dijkstra.py`**: se Dijkstra fizer `push` com `inf`, a regra de `push` deve aceitar `inf`. Registrar como ponto aberto para F2.) |

> Nota sobre a última linha: o enunciado diz "pesos reais finitos", não "prioridades finitas". Dijkstra canônico inicializa `dist=inf`. A implementação de Dijkstra (F2) pode fazer `push(v, inf)` ou `push(source, 0)` + `decrease`. A política de `push(inf)` será congelada em F2 após leitura do modelo `dijkstra.py`. Por ora: `NaN` sempre `ValueError`; `inf` em `decrease_key` como aumento segue a regra geral.

### Como detectar handle inválido (sem vazar detalhes)
- Cada handle carrega `_owner` (referência ao heap) e `_alive`.
- `decrease_key` verifica nesta ordem: (1) tipo/estrutura do handle, (2) `owner is self`, (3) `_alive`, (4) comparação de prioridades. Qualquer falha em (1)–(3) → `ValueError` com mensagem clara (`"invalid handle"`, `"handle from another heap"`, `"handle already removed"`).
- No binário, checagem extra opcional: `0 <= handle.index < len(a)` e `a[handle.index]` é a entrada dona do handle (protege contra dessincronização; falha interna → `ValueError`).
- Mensagens devem distinguir "aumento" de "handle inválido" para depuração, mantendo o tipo `ValueError` nos dois casos.

## 6. Armadilhas previstas (e como evitá-las na implementação)

1. **Esquecer de atualizar `handle.index` em `swap` (binário).** Toda troca no array deve atualizar os dois handles. Teste direcionado: `push` n itens, `decrease` aleatórios, `pop` tudo e conferir ordem + índices.
2. **Handle como `int`.** Congela e não invalida. Usar objeto mutável.
3. **`decrease_key` que aceita aumento silencioso.** Comparar `new > old` antes de qualquer mutação; `NaN` à parte (toda comparação com `NaN` é `False` — checar com `math.isnan`/`!= new` ou `priority != priority`).
4. **`pop_min` binário com 1 elemento.** Caso especial: remover sem `sift_down`; ainda assim invalidar handle e decrementar.
5. **`__len__` por travessia (binomial/Fibonacci).** Vira O(n) e corrompe a análise de Dijkstra. Usar contador incrementado em `push` e decrementado em `pop_min`.
6. **Binomial: esquecer reversão dos filhos em `pop_min`.** Sem reversão, graus ficam decrescentes e o `union` seguinte viola o invariante (duplicatas de grau). Reverter sempre.
7. **Binomial: trocar ponteiros em vez de conteúdo no `bubble-up` sem re-mapear.** O handle do chamador passa a apontar para outro lugar lógico. Trocar conteúdo (`vertex, priority`) preserva identidade.
8. **Fibonacci: `mark` inicial de nó não-raiz.** Nó que vira filho via `link` deve ter `mark=False`; só vira `True` ao perder o primeiro filho (sendo não-raiz).
9. **`cut` que não limpa `parent`/`mark` nem decrementa `degree`.** Os três juntos; faltando um, `consolidate` conta grau errado.
10. **Cascata recursiva.** Usar `while` para evitar `RecursionError` em cadeias longas.
11. **Mutar `root-list` durante `consolidate`.** Iterar sobre cópia (`list(self._roots)`).
12. **Array de `consolidate` subdimensionado.** Se `degree` exceder `len(A)`, estender dinamicamente em vez de `IndexError`.
13. **`_min` obsoleto após `decrease_key`/`cut`.** Sempre comparar `new_priority < _min.priority` e atualizar.
14. **Igualdade de prioridades.** `link`/`sift`/`bubble` devem usar `<` estrito para "menor" (empate = qualquer lado, mas consistente). Não usar `<=` que cause trocas infinitas.
15. **Alias de `vertex` mutável.** `vertex` é `int` (imutável) no contrato — sem risco, mas não usar `vertex` como identidade do handle.
16. **Exceções trocadas.** `pop` vazio é `IndexError`; aumento/inválido é `ValueError`. Trocar quebra o corretor automático (8,0 pts automáticos).

## 7. Decisões congeladas para a implementação (resumo executável)

- [ ] Binary: array + `sift_up`/`sift_down` iterativos; handle-objeto com `index`; contador `__len__` O(1); `swap` sempre atualiza índices; invalidação em `pop_min`.
- [ ] Binomial: floresta + `merge`/`union`/`link`; `push`=merge singleton; `decrease`=troca de conteúdo borbulhando; `pop_min`=remove mínimo + `union` com filhos reversos; handle=nó; contador O(1).
- [ ] Fibonacci: `root-list` lista Python + `min`/`mark`/`degree`; `push` O(1); `decrease` com `cut`+`cascading_cut` em `while`; `pop_min` com `consolidate` por array de graus + `link`; handle=nó; contador O(1).
- [ ] Política de handles §5 aplicada nas 3 classes; sem `heapq`; sem mudar assinaturas/nomes do modelo.
- [ ] Ponto aberto para F2: aceitar ou não `inf` em `push` (depende do desenho de `dijkstra.py`).

## 8. Fontes (sem código copiado — apenas padrões algorítmicos)

- Cormen, Leiserson, Rivest, Stein — *Introduction to Algorithms* (CLRS):
  - 3ª ed.: cap. 6 (*Heapsort* — binary heap, `sift`/`heapify`); cap. 19 (*Fibonacci Heaps* — §§ binomial heaps + estrutura/operações Fibonacci, análise amortizada por potencial).
  - 4ª ed.: cap. 6 (idem); cap. 19/20 conforme impressão (*Binomial Heaps* / *Fibonacci Heaps* — a numeração varia entre edições; o conteúdo de referência é o mesmo).
- Vuillemin, J. (1978). *A data structure for manipulating priority queues*. Communications of the ACM, 21(4), 309–315. — origem das árvores binomiais / floresta com `merge` por grau.
- Fredman, M. L., & Tarjan, R. E. (1987). *Fibonacci heaps and their uses in improved network optimization algorithms*. Journal of the ACM, 34(3), 596–615. — `root-list` + `min`, `decrease_key` O(1) amortizado com corte/cascata, `pop_min` O(log n) amortizado com `consolidate`, análise por potencial.
- Documentação Python relevante (só stdlib auxiliar, sem PQ): `list`, `dict`, `math.inf`/`math.isnan` — sem `heapq`.

## 9. Rastreabilidade do passo

- Comandos executados (apenas `.venv`):
  - `mkdir -p docs && ls -la` — criar/verificar diretório de entrega.
  - `/home/arthur/projects/papa_t2/.venv/bin/python --version` → `Python 3.12.3` (satisfaz ≥3.11).
- Arquivos criados/alterados: `docs/pesquisa_heaps_F11.md` (criado; único arquivo do passo).
- Arquivos propositalmente NÃO alterados: `materiais/Trabalho_Heap_Arquivos_Alunos/heaps.py` (modelo intacto), nenhum `aluno/*`.
- DoD: arquivo existe com os 3 heaps (§§1–3) + tabela de complexidades (§4) + referências (§8) + política de handles (§5).
