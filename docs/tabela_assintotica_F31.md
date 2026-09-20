# Tabela Assintótica Canônica — Passo F3.1 (pesquisa, sem preencher respostas)

> Natureza: pesquisa registrada para guiar o preenchimento futuro de `respostas.json` (Parte 3).
> Neste passo `respostas.json` NÃO foi editado (proibição do passo).
> Modelo: `materiais/Trabalho_Heap_Arquivos_Alunos/respostas.json` (lido, intacto).
> Enunciado: `materiais/Trabalho_Heap_Enunciado.md` Parte 3, linhas 52-54.

## 0. Contratos rígidos (copiados — não reinterpretar)

- Parte 3: preencher `aluno/respostas.json` **usando somente as categorias indicadas no modelo**.
- Convenção de análise: **pior caso** para heaps binário e binomial; **limites amortizados** para heap de Fibonacci, conforme a tabela comparativa usual.
- Além das operações individuais, informar a complexidade do Dijkstra **com listas de adjacência e `decrease_key`, sem supor que o grafo é conexo**.
- Modelo (`respostas.json`):
  - `categorias_permitidas = ["1", "log_n", "n", "m_mais_n_log_n", "m_mais_n_vezes_log_n"]`.
  - 12 campos `PREENCHER` = 3 heaps × 4 entradas (`inserir`, `diminuir_chave`, `extrair_minimo`, `dijkstra`):
    - `heap_binario`: `inserir`, `diminuir_chave`, `extrair_minimo`, `dijkstra`.
    - `heap_binomial`: `inserir`, `diminuir_chave`, `extrair_minimo`, `dijkstra`.
    - `heap_fibonacci`: `inserir`, `diminuir_chave`, `extrair_minimo`, `dijkstra`.
- Premissas herdadas: grafos direcionados em lista de adjacência, `n = |V|`, `m = |E|`, pesos reais finitos `>= 0`.
- Implementação de referência para a contagem (pesquisas F1.1/F2.1): Dijkstra variante (A)+(P1) — uma entrada por vértice via `push`, `decrease_key` por relaxamento que melhora, `n` × `pop_min`, sem lazy, sem conjunto visitado como correção.

## 1. Revisão das operações individuais (convenção do enunciado)

### 1.1 Heap binário — pior caso `O(log n)` nas três operações

- Referência: CLRS cap. 6 (3ª ed.; 4ª ed. cap. 6 — *Heapsort* / binary heap).
- `inserir` (`push`): append no fim + `sift_up` ao longo da altura `⌊log n⌋`. Pior caso `O(log n)`.
- `diminuir_chave` (`decrease_key`): atualização + `sift_up` a partir do índice do handle. Pior caso `O(log n)`.
- `extrair_minimo` (`pop_min`): remove raiz + move último + `sift_down` (`MIN-HEAPIFY`). Pior caso `O(log n)`.
- Leitura para o modelo: as três → `log_n`.

### 1.2 Heap binomial — pior caso `O(log n)` nas três operações

- Referência: Vuillemin (1978) para a árvore/floresta binomial; CLRS cap. 19 (3ª ed.; cap. correspondente em outras edições — *Binomial Heaps*: `merge`/`union`/`link`).
- Invariante: floresta com no máximo uma árvore por grau; nº de árvores `≤ ⌊log n⌋ + 1`; altura de cada árvore `≤ log n`.
- `inserir`: cria singleton de grau 0 + `union` (que inclui `merge` por grau + consolidação). Pior caso `O(log n)`.
- `diminuir_chave`: atualiza prioridade + borbulhamento (`bubble-up` trocando conteúdo) até a raiz, altura `≤ log n`. Pior caso `O(log n)`.
- `extrair_minimo`: varredura das raízes para achar o mínimo (`O(log n)` raízes) + `union` dos filhos revertidos com o resto. Pior caso `O(log n)`.
- Leitura para o modelo: as três → `log_n`.

### 1.3 Heap de Fibonacci — amortizado `O(1)` / `O(1)` / `O(log n)`

- Referência: Fredman–Tarjan (1987); CLRS cap. 19/20 conforme edição (3ª ed. cap. 19 — *Fibonacci Heaps*; 4ª ed. cap. 20 — numeração varia, conteúdo idêntico): análise pelo método do potencial.
- `inserir` (`push`): cria nó isolado, adiciona à `root-list`, atualiza `min`. Amortizado `O(1)` (nesta formulação também `O(1)` pior caso).
- `diminuir_chave`: atualiza prioridade + `cut` + `cascading-cut` (marcas `mark`). Pior caso isolado `O(n)` (cadeia de cortes), **amortizado `O(1)`** pelo potencial — é este o valor que o enunciado pede.
- `extrair_minimo` (`pop_min`): move filhos do `min` para `root-list` + `consolidate` por array de graus + reeleição do `min`. Pior caso isolado `O(n)` (lista de raízes degenerada), **amortizado `O(log n)`** (cota de Fibonacci: grau máximo `D(n) ≤ log_φ n`) — é este o valor que o enunciado pede.
- Leitura para o modelo (amortizado): `inserir → 1`, `diminuir_chave → 1`, `extrair_minimo → log_n`.
- Atenção deliberada: não confundir pior caso isolado (`O(n)` em diminuir/extrair) com o amortizado pedido. A tabela usa o amortizado.

## 2. Derivação explícita do Dijkstra (lista de adjacência + `decrease_key`)

Vale para a formulação (A)+(P1) documentada em `docs/pesquisa_dijkstra_F21.md` §§1–2, 4–5.

### 2.1 Contagem de operações de fila de prioridade

1. **Inicialização:** `n` × `push` (um por vértice, `source → 0`, demais → `inf`). Heap com no máximo `n` entradas simultâneas, logo todo `log(tamanho_heap) ≤ log n` — a majoração por `log n` é válida em cada operação.
2. **Loop principal:** `n` × `pop_min` (cada vértice extraído exatamente uma vez; sem `early-break`, sem entradas obsoletas, sem re-extração).
3. **Relaxamentos:** cada aresta direcionada `(u, v)` é examinada exatamente uma vez — quando sua origem `u` é extraída (essência da lista de adjacência: varredura total `Θ(n + m)`). Cada exame dispara **no máximo um** `decrease_key` (só sob `nd < dist[v]`). Logo: `≤ m` × `decrease_key`.
4. **Trabalho fora do heap:** validação prévia `O(n + m)` + inicialização `dist`/`pred`/`handles` `O(n)` + varredura das adjacências `O(n + m)`. Parcela aditiva que não altera a classe dominada pelo heap (ver §2.2–2.3).
5. **Espaço:** `O(n)` entradas no heap + `O(n)` vetores auxiliares; grafo de entrada `O(n + m)`.

### 2.2 Binário e binomial — `O((m + n) log n)`

- Custo: `n · O(log n)` (pushes) + `n · O(log n)` (pops) + `≤ m · O(log n)` (decreases) + `O(n + m)` (varredura/validação).
- Soma: `O((m + 2n) log n + n + m) = O((m + n) log n)`, pois `n + m ≤ (m + n) log n` para `n ≥ 2`.
- Mapeamento: `O((m+n) log n)` = categoria `m_mais_n_vezes_log_n` (o produto distribui sobre a soma: `(m+n)·log n`).

### 2.3 Fibonacci (amortizado) — `O(m + n log n)`

- Custo amortizado: `n · O(1)` (pushes) + `n · O(log n)` (pops) + `≤ m · O(1)` (decreases) + `O(n + m)` (varredura/validação).
- Soma: `O(n + n log n + m) = O(m + n log n)` (o termo `n` isolado é absorvido por `n log n` para `n ≥ 2`).
- Mapeamento: `O(m + n·log n)` = categoria `m_mais_n_log_n` (soma de `m` com `n·log n`, sem fatorar o logaritmo sobre `m`).

### 2.4 Por que a distinção entre as duas categorias Dijkstra importa

- `m_mais_n_vezes_log_n` ≡ `(m + n) log n = m·log n + n·log n` — o logaritmo multiplica **também** `m` (cada aresta pode custar um `decrease` logarítmico).
- `m_mais_n_log_n` ≡ `m + n·log n` — o logaritmo multiplica **só** `n` (arestas custam `O(1)` amortizado cada; o logaritmo vem só dos `n` pops).
- Trocar uma pela outra é erro de classe, não de notação: em grafo denso (`m = Θ(n²)`), binário dá `Θ(n² log n)` contra Fibonacci `Θ(n²)`.

## 3. Tabela canônica — 12 campos + mapeamento exato para as categorias

> Leitura: `O(1) → "1"`; `O(log n) → "log_n"`; `O(m + n log n) → "m_mais_n_log_n"`; `O((m+n) log n) → "m_mais_n_vezes_log_n"`.

| # | Campo do modelo | Limite canônico (convenção do enunciado) | Categoria exata |
|---|---|---|---|
| 1 | `heap_binario.inserir` | `O(log n)` pior caso | `log_n` |
| 2 | `heap_binario.diminuir_chave` | `O(log n)` pior caso | `log_n` |
| 3 | `heap_binario.extrair_minimo` | `O(log n)` pior caso | `log_n` |
| 4 | `heap_binario.dijkstra` | `O((m+n) log n)` pior caso | `m_mais_n_vezes_log_n` |
| 5 | `heap_binomial.inserir` | `O(log n)` pior caso | `log_n` |
| 6 | `heap_binomial.diminuir_chave` | `O(log n)` pior caso | `log_n` |
| 7 | `heap_binomial.extrair_minimo` | `O(log n)` pior caso | `log_n` |
| 8 | `heap_binomial.dijkstra` | `O((m+n) log n)` pior caso | `m_mais_n_vezes_log_n` |
| 9 | `heap_fibonacci.inserir` | `O(1)` amortizado | `1` |
| 10 | `heap_fibonacci.diminuir_chave` | `O(1)` amortizado | `1` |
| 11 | `heap_fibonacci.extrair_minimo` | `O(log n)` amortizado | `log_n` |
| 12 | `heap_fibonacci.dijkstra` | `O(m + n log n)` amortizado | `m_mais_n_log_n` |

Notas de preenchimento (para o passo futuro que editará `respostas.json`, NÃO este):

- Preencher cada um dos 12 campos **somente** com o token da coluna "Categoria exata", sem prefixo `O(...)`, sem variação de caixa ou separador.
- A categoria `n` consta em `categorias_permitidas` mas **não é usada** em nenhum dos 12 campos canônicos (nenhuma das operações pedidas é `Θ(n)` na convenção adotada; `n` isolado aparece apenas como parcela absorvida na derivação do Dijkstra — ver §2). Registrado aqui para evitar preenchimento espúrio.
- Manter `categorias_permitidas` inalterada no arquivo final.

## 4. Sem supor conexidade — por que manter `n` explícito (vale esparso/denso/desconexo)

- O enunciado veda supor grafo conexo. Em grafo conexo (não-direcionado) valeria `m ≥ n − 1` e poder-se-ia simplificar `O((m+n) log n)` para `O(m log n)`; com a vedação, a forma com `n` explícito é obrigatória.
- Casos que a fórmula com `n` explícito cobre e a simplificada não:
  - **Desconexo / fonte isolada:** `m = 0`, `n` arbitrário. Dijkstra ainda faz `n` pushes + `n` pops: binário/binomial `Θ(n log n)`; Fibonacci `Θ(n log n)` (dominado pelos pops). Sem o termo `n`, a fórmula daria `0` — falso.
  - **Esparso:** `m = O(n)` (ex.: listas, grades, árvores direcionadas). Binário `O(n log n)`; Fibonacci `O(n log n)` — mesma classe, constantes decidem (ponto do benchmark F4).
  - **Denso:** `m = Θ(n²)` (ex.: completo direcionado sem laços). Binário/binomial `Θ(n² log n)`; Fibonacci `Θ(n²)` — a vantagem do Fibonacci (decreases `O(1)`) aparece aqui.
- Consequência prática: o relatório/benchmark (F4) deve incluir pelo menos uma família esparsa e uma densa para exercitar os dois regimes, mas isso é matéria de outro passo — aqui basta que a tabela valha nos três regimes.

## 5. Fontes (sem código copiado — apenas limites assintóticos)

- Cormen, Leiserson, Rivest, Stein — *Introduction to Algorithms* (CLRS):
  - 3ª ed.: cap. 6 (*Heapsort* — binário `O(log n)`); cap. 19 (*Fibonacci Heaps* — inclui binomial heaps + análise amortizada por potencial do Fibonacci); cap. 24 (*Single-Source Shortest Paths* — Dijkstra `O((m+n) log n)` binário / `O(m + n log n)` Fibonacci com adjacência + `decrease_key`).
  - 4ª ed.: cap. 6 (idem); caps. 19/20 (*Binomial* / *Fibonacci Heaps* — a numeração varia entre edições/impressões, o conteúdo de referência é o mesmo); cap. correspondente a *Single-Source Shortest Paths* (mesma análise do Dijkstra).
- Vuillemin, J. (1978). *A data structure for manipulating priority queues*. Communications of the ACM, 21(4), 309–315. — origem das árvores binomiais; base do binomial `O(log n)` por operação e `O((m+n) log n)` no Dijkstra.
- Fredman, M. L., & Tarjan, R. E. (1987). *Fibonacci heaps and their uses in improved network optimization algorithms*. Journal of the ACM, 34(3), 596–615. — `insert`/`decrease_key` `O(1)` amortizado, `extract-min` `O(log n)` amortizado, Dijkstra `O(m + n log n)` amortizado.
- Pesquisas anteriores do projeto (coerência interna): `docs/pesquisa_heaps_F11.md` §4 (tabela pior-caso vs amortizado + ressalva dos piores casos isolados do Fibonacci) e `docs/pesquisa_dijkstra_F21.md` §5 (contagem `n` pushes + `n` pops + `≤ m` decreases, sem conexidade).

## 6. Rastreabilidade do passo

- Comandos: apenas leitura (`materiais/Trabalho_Heap_Enunciado.md` linhas 52-54, `materiais/Trabalho_Heap_Arquivos_Alunos/respostas.json`, `docs/pesquisa_heaps_F11.md`, `docs/pesquisa_dijkstra_F21.md`); nenhuma execução (nada a rodar neste passo; se algo fosse rodado, seria só via `.venv`).
- Arquivo criado neste passo: `docs/tabela_assintotica_F31.md` (este arquivo).
- Arquivos propositalmente NÃO alterados: `materiais/Trabalho_Heap_Arquivos_Alunos/respostas.json` (modelo intacto, ainda com 12× `PREENCHER`), nenhum `aluno/*`, nenhum código.
- DoD: este arquivo existe com tabela de 12 campos (§3) + derivação explícita (§2) + mapeamento exato para as categorias (§§2–3) + fontes (§5), sem supor conexidade (§4).
