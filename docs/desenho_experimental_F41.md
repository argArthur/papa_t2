# Desenho Experimental — Passo F4.1 (estado da arte, sem implementar benchmark)

> Natureza: desenho para guiar a implementação futura de `benchmark.py` (F4.2) e o
> `relatorio.md` (F4.3). Neste passo **nada de `benchmark.py` foi implementado**:
> `medir()` e `SEED=2027` permanecem intactos e `main()` segue `NotImplementedError`.
> Modelo lido: `materiais/Trabalho_Heap_Arquivos_Alunos/benchmark.py` (linhas 1–31).
> Enunciado: `materiais/Trabalho_Heap_Enunciado.md` Parte 4 (linhas 56–66) + Observações (linhas 96–98).
> Ambiente real: `versions_env.txt` (ver §1). Tudo rodado/estimado via `.venv` (proibição do passo).

## 0. Contratos rígidos (copiados — não reinterpretar)

- Parte 4: comparar as **3 heaps** (`BinaryHeap`, `BinomialHeap`, `FibonacciHeap`) em
  **≥3 famílias × ≥4 tamanhos** por família; **mesmas instâncias e fontes** em cada
  comparação (pareado); **aquecimento + repetições + dispersão**; relatório ≤1200 palavras
  com os 5 itens (máquina/Python/gerador/semente/protocolo; tabelas com unidades+dispersão;
  operações dominantes; por que melhor assintótico pode perder; limitações/ameaças).
- Observações: mesma instância + mesma fonte entre heaps; registrar semente; aquecimento;
  repetir medições; apresentar dispersão; justificar decisões e limitações no relatório.
- Modelo `benchmark.py`: `SEED = 2027`; `medir(func, repeticoes=7)` retorna
  `(mediana, MAD)` em segundos via `time.perf_counter()` + `statistics.median`.
  **NÃO alterar `medir`/`SEED` neste passo; NÃO implementar `main` ainda** (matéria de F4.2).
- Padrões do workflow (F4.1): mesma seed + mesmas instâncias/fontes; warmup 1–2 rodadas
  descartadas; `time.perf_counter` via `medir()`; ≥7 repetições (mediana+MAD); unidades
  s/ms + dispersão; **separar construção do grafo da medição**; `random.Random(SEED)`
  **local**, nunca `random.seed` global; máquina única sem carga.

## 1. Ambiente fixo (de `versions_env.txt` — repetir no relatório)

- CPU: Intel Core Ultra 7 256V (8 núcleos, 1 thread/núcleo, máx. 4800 MHz); caches
  L1d 320 KiB / L1i 512 KiB / L2 14 MiB / L3 12 MiB; 1 nó NUMA.
- RAM: 15 Gi (10 Gi disponíveis no momento da coleta); Swap 29 Gi.
- SO: Ubuntu 24.04.5 LTS (noble), kernel `Linux-7.0.0-31-generic-x86_64`, glibc 2.39.
- Python: 3.12.3 (CPython, GCC 13.3.0) — atende premissa ≥3.11; `pytest 7.4.4`.
- Intérprete: `.venv/bin/python` (criado com `--without-pip --system-site-packages`;
  `sys.prefix` verificado). Todo o experimento roda nesse intérprete, máquina única,
  sem carga concorrente (fechar navegador/builds; sem `taskset` — documentar que o SO
  pode migrar threads, ameaça registrada em F4.3).

## 2. Plano fatorial 3 famílias × 4 tamanhos (n geométrico ×2)

`n = 500, 1000, 2000, 4000` em **todas** as famílias (escala geométrica ×2, mesma usada
no exemplo do workflow). `m` documentado por ponto — exato nas famílias A/C,
esperado + efetivo registrado nas tabelas em B (ER é aleatório por construção).

| Família | Gerador (determinístico, ver §3) | n=500 (m) | n=1000 (m) | n=2000 (m) | n=4000 (m) |
|---|---|---|---|---|---|
| **A — Esparsa estrada** (out-degree fixo) | cada `u` recebe exatamente `d=4` sucessores distintos (`v≠u`, sem laço), pesos `U{1..10}` | 2 000 | 4 000 | 8 000 | 16 000 |
| **B — Densa Erdős–Rényi** `p=0,05` | cada par ordenado `u≠v` vira aresta com prob. `p`, pesos `U{1..100}`; `E[m]=n(n−1)p` | ≈12 475 | ≈49 950 | ≈199 900 | ≈799 800 |
| **C — Camadas/corrente hierárquica** | corrente `i→i+1` peso 1 (`n−1` arestas) + 5 atalhos/vértice (`v≠u`), pesos `U{100..1000}` | 2 999 | 5 999 | 11 999 | 23 999 |

- Total: **12 configurações × 3 heaps = 36 pontos** (cada ponto = 1 mediana + 1 MAD).
- Por que `p=0,05` em B e não maior: com `p=0,05`, o maior ponto tem `m≈800k`
  (50× o esparso de mesmo `n`), já suficiente para o regime `m≫n`; `p=0,10`
  dobraria geração/memória sem mudar a classe assintótica e arriscaria GC/ruído.
  Piloto (§5) mostra que `p=0,05/n=4000` já é o ponto mais caro e ainda viável (~80 ms/run).
- Por que `n` uniforme e não menor em B: simplifica a leitura geométrica e o pareamento
  narrativo do relatório; o custo continua <5 min no total (§5), logo não há motivo
  para encolher B.
- Pesos inteiros (não `float` contínuo): determinísticos via RNG local, evitam `NaN/inf`
  (que `dijkstra` rejeitaria) e mantêm empates possíveis — qualquer árvore de caminhos
  mínimos continua válida pelo enunciado.

## 3. Protocolo reproduzível (o que F4.2 deve implementar — especificação)

1. **Semente local, fonte fixa, instância pareada.**
   - `SEED = 2027` (do modelo, inalterado). Geradores **puros e determinísticos**:
     `rng = random.Random(SEED + fam_id*10_000 + size_idx)` com
     `fam_id ∈ {0:A, 1:B, 2:C}`, `size_idx ∈ {0..3}` — offsets fixos documentados no
     código de F4.2. **Proibido `random.seed()` global.**
   - Cada configuração `(família, tamanho)` gera **uma única instância `g`** (lista de
     adjacência `graph[u] = [(v,w), ...]`, direcionada) reutilizada pelos 3 heaps.
   - **Fonte fixa `s = 0`** em todas as configurações (alcança quase todos os vértices
     nas 3 famílias; mesma fonte entre heaps = comparação pareada). Registrar `s` na tabela.
2. **Construção separada da medição.**
   - Gerar `g` **fora** de `medir`. Medir **só** `dijkstra(g, s, Heap)`:
     `medir(lambda: dijkstra(g, s, HeapClass))`. A validação `O(n+m)` interna ao
     `dijkstra` fica dentro da medição — igual para os 3 heaps, portanto justa — mas a
     geração do grafo nunca entra no cronômetro.
3. **Aquecimento (warmup) descartado.**
   - Modo completo: **2 rodadas de warmup por (config, heap)**, descartadas
     (estabiliza caches, alocador e `statistics`; custo irrelevante — ver §5).
   - `--quick`: 1 rodada de warmup.
4. **Repetições via `medir` (mediana + MAD).**
   - Modo completo: `medir(..., repeticoes=7)` (default do modelo) → `(mediana_s, mad_s)`.
   - `--quick`: `repeticoes=3` (só fumaça; números do quick **não** entram no relatório).
   - `medir` usa `time.perf_counter()` internamente — não cronometrar por fora.
5. **Unidades e dispersão.**
   - Colunas por ponto: `familia, n, m_efetivo, fonte, heap, mediana_s, mad_s`
     (segundos, 6 casas) + colunas derivadas `mediana_ms, mad_ms` para leitura quando
     `mediana_s < 1`. Dispersão obrigatória: MAD na mesma unidade + razão `mad/mediana`
     opcional no relatório. Saída: CSV (`resultados.csv`) + tabela Markdown impressa.
6. **Ordem e higiene.**
   - Ordem fixa por configuração: Binary → Binomial → Fibonacci (ou intercalada por
     repetição em F4.2 — decisão de implementação, desde que idêntica entre repetições);
     máquina única, sem carga, `.venv`, sem `GC` manual (default; registrar como ameaça).
7. **CLI (especificação para F4.2, não implementada aqui).**
   - `python benchmark.py` = modo completo (12 configs × 7 reps).
   - `python benchmark.py --quick` = fumaça (família A, `n ∈ {500, 1000}`, 3 reps).
   - `--out` opcional para o CSV. `SEED`/`medir` intactos em ambos os modos.

## 4. Justificativa — operações dominantes por família (por que são distinguíveis)

Contagem comum (variante A+P1 de `dijkstra.py`: push de todos): `n` pushes + `n` pops +
`≤ m` decreases (um por aresta, só se `nd < dist[v]`). O que muda é **qual termo domina
e com que taxa de sucesso**, exercitando caminhos de código distintos em cada heap:

- **A — Esparsa (`m=4n`): regime `pop`-dominado, poucos `decrease_key` bem-sucedidos.**
  Out-degree baixo + pesos homogêneos (1..10) → cada vértice relaxa 4 vizinhos, mas a
  maioria dos relaxamentos falha após as distâncias estabilizarem. Esperado:
  `n` pops com heap de tamanho `Θ(n)` e `sift_down`/`union`/`consolidate` por pop como
  custo principal; `decrease` raro. **Diferencial esperado:** binário favorecido
  (array + localidade de cache, `sift` barato); Fibonacci paga `consolidate` sem ter
  `decrease O(1)` para compensar; binomial paga `merge/union` por push sem contrapartida.
- **B — Densa ER (`m≈0,05n²`): regime `decrease`-dominado, muitos relaxamentos.**
  Cada pop relaxa `≈pn` vizinhos (≈25/50/100/200 por pop nos 4 tamanhos); no início
  quase todo relaxamento melhora `dist` → taxa de `decrease_key` bem-sucedido alta
  (dezenas de milhares a centenas de milhares de decreases por run). É o único regime
  onde a vantagem assintótica do Fibonacci (`decrease O(1)` amortizado vs `O(log n)`)
  tem chance de aparecer — e onde o binomial sofre (borbulhar `O(log n)` com constantes
  de ponteiros). **Diferencial esperado:** gap binário×Fibonacci comprime com `n`
  (ou inverte se `n` fosse maior); binomial tende a último.
- **C — Corrente + atalhos hierárquicos (`m≈6n−1`, pesos 1 vs 100..1000): força
  `pop_min`/`consolidate` com heap cheio e prioridades em dois patamares.**
  A corrente garante o caminho ótimo incremental (distâncias `0,1,2,…,n−1`), enquanto os
  5 atalhos/vértice mantêm no heap milhares de entradas com prioridades altas que nunca
  vencem cedo → heap permanece grande durante quase todo o loop; cada pop remove o
  próximo da corrente e cada `consolidate`/`union`/varredura de raízes varre uma
  root-list longa. Decreases bem-sucedidos são raros (atalhos peso ≥100 quase nunca
  melhoram), mas **cortes em cascata e `mark`** do Fibonacci são exercitados quando um
  atalho eventualmente melhora um vértice distante. Pesos em dois patamares também
  criam empates parciais (corrente), testando estabilidade do `min`.
  **Diferencial esperado:** binário ainda vence pelo `pop` barato em array; Fibonacci
  mostra seu pior caso relativo (muito `consolidate`, pouco `decrease` útil) — ponto
  central da discussão "assintótico melhor ≠ mais rápido em `n` moderado".

As três famílias são **mutuamente distinguíveis** por construção: (A) `m/n=4` homogêneo,
(B) `m/n≈12→200` crescente quadraticamente, (C) `m/n≈6` heterogêneo em dois patamares
com estrutura ordenada. Nenhuma é redundante.

## 5. Custos e tempos estimados (piloto no `.venv`, mesma máquina/CPU)

Piloto ad-hoc (não é o `benchmark.py`; comandos e saídas arquivados na revisão):
geradores equivalentes + 1 run de `dijkstra` por heap, `.venv/bin/python`, sem carga.

| Configuração piloto | m | Binary | Binomial | Fibonacci |
|---|---|---|---|---|
| A n=2000 | 8 000 | 0,0056 s | 0,0074 s | 0,0063 s |
| A n=4000 | 16 000 | 0,011 s | 0,015 s | 0,014 s |
| B p=0,02 n=2000 | 79 844 | 0,012 s | 0,015 s | 0,014 s |
| B p=0,10 n=1000 | 100 577 | 0,011 s | 0,011 s | 0,012 s |
| B p=0,05 n=2000 | 199 210 | 0,023 s | 0,024 s | 0,026 s |
| B p=0,05 n=4000 | 799 347 | 0,079 s | 0,089 s | 0,081 s |
| C n=2000 | 11 993 | 0,0077 s | 0,0093 s | 0,0093 s |
| C n=4000 | 23 992 | 0,017 s | 0,020 s | 0,020 s |
| Geração B p=0,05 n=4000 | — | 0,76 s (uma vez por config) | — | — |

Estimativa modo **completo** (12 configs × 3 heaps × (2 warmup + 7 reps) = 324 runs):
pior config (B/n=4000) ≈ 3 heaps × 9 × 0,085 s ≈ 2,3 s + 0,8 s geração ≈ 3 s;
demais configs ≤0,5 s cada. **Total estimado <60 s** (folga ×3 para ruído/GC: <3 min).
Memória pico: grafo B/n=4000 (~800k tuplas) ≈ dezenas de MB — folgado nos 15 Gi.
Conclusão: os tamanhos **diferenciam os heaps (gaps de 10–35% já visíveis no piloto)
sem inviabilizar tempo** — sem motivo para encolher `n` ou `p`.

## 6. Decisão `--quick` vs completo

- **`--quick` (fumaça, <10 s):** família A, `n ∈ {500, 1000}`, `repeticoes=3`, warmup 1.
  Uso: validar que `main()` roda de ponta a ponta, CSV/Markdown são gerados e os 3 heaps
  concordam (sanity das distâncias em 1 instância). **Números do quick não entram no
  relatório.**
- **Completo (relatório, <3 min):** as 12 configurações do §2, `repeticoes=7`, warmup 2.
  Uso: única fonte dos números/tabelas do relatório F4.3.
- Ambos no `.venv`, mesma máquina, sem carga; queda automática para `--quick` em CI
  sem justificativa adicional.

## 7. Rastreabilidade do passo (DoD F4.1)

- [x] Doc existe com **3 famílias × 4 tamanhos** e `n/m` por ponto (§2).
- [x] **Pareado**: mesma instância + fonte `s=0` entre heaps (§3.1).
- [x] **Seed/warmup/medir documentados**: `SEED=2027` local com offsets (§3.1),
  warmup 2 (1 no quick) (§3.3), `medir` 7 reps mediana+MAD via `perf_counter` (§3.4).
- [x] **Famílias distinguíveis** por operação dominante (§4).
- [x] Construção separada da medição (§3.2); unidades+dispersão (§3.5); custos (§5);
  decisão quick/completo (§6).
- Propositalmente **não** alterados: `materiais/.../benchmark.py`
  (`SEED`/`medir`/`main` intactos), nenhum código de `heaps.py`/`dijkstra.py`.
- Comandos: só leitura + piloto de calibração via `.venv/bin/python`
  (nenhum `python3` do sistema; nenhum `pip install`).
