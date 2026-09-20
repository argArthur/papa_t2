# Relatório experimental — Dijkstra × 3 heaps

## 1. Ambiente e protocolo

Máquina única sem carga (de `versions_env.txt`): CPU Intel Core Ultra 7 256V, 8 núcleos/1 thread por núcleo, máx. 4800 MHz; caches L1d 320 KiB, L1i 512 KiB, L2 14 MiB, L3 12 MiB; 1 nó NUMA. RAM 15 Gi (10 Gi livres na coleta), swap 29 Gi. SO Ubuntu 24.04.5 LTS, kernel Linux 7.0.0-31-generic x86_64, glibc 2.39. Python 3.12.3 CPython (GCC 13.3.0), pytest 7.4.4, intérprete `.venv/bin/python` (sem `heapq` em `heaps.py`; só `.venv`, nunca sistema).

Geradores determinísticos com RNG local: `random.Random(SEED + fam_id*10000 + size_idx)`, `SEED=2027`, `fam_id` em {0:A, 1:B, 2:C}, `size_idx` em {0..3}; nunca `random.seed` global. Fonte fixa `s=0` e mesma instância por configuração entre os 3 heaps (comparação pareada). Grafo construído fora do cronômetro; mede-se só `dijkstra(g, s, Heap)`.

Medição via `medir(func, repeticoes=7)`: 7 repetições com `time.perf_counter`, retorna mediana e MAD (`statistics.median`) em segundos; tabelas mostram ms (s×1000) com MAD na mesma unidade. Aquecimento: 2 rodadas descartadas por (configuração, heap). Sanity: distâncias dos 3 heaps comparadas por configuração (iguais em todas).

## 2. Famílias de grafos

Plano fatorial 3 famílias × 4 tamanhos (`n=500, 1000, 2000, 4000`), 12 configurações × 3 heaps = 36 pontos (de `docs/desenho_experimental_F41.md`).

| Família | Gerador | n → m por ponto |
|---|---|---|
| A esparsa estrada | cada `u` com exatos `d=4` sucessores distintos, sem laço, pesos U{1..10} | 500→2000; 1000→4000; 2000→8000; 4000→16000 |
| B densa Erdős–Rényi `p=0,05` | cada par ordenado `u≠v` vira aresta com prob. 0,05, pesos U{1..100}; `m` efetivo medido | 500→12578; 1000→50232; 2000→200325; 4000→800553 |
| C corrente + atalhos | cadeia `i→i+1` peso 1 (`n−1` arestas) + 5 atalhos/vértice, pesos U{100..1000} | 500→2999; 1000→5999; 2000→11999; 4000→23999 |

A é homogênea `m/n=4`; B é quadrática `m/n≈25→200`; C é heterogênea `m/n≈6` em dois patamares com estrutura ordenada. Grafos direcionados; `m` exato em A/C, efetivo registrado em B.

## 3. Resultados

Mediana ± MAD em ms (7 reps; segundos com 6 casas em `resultados_benchmark.csv`/`.md`). Fonte `s=0` em todos os pontos.

Família A — `A_esparsa_d4`:

| n (m) | BinaryHeap | BinomialHeap | FibonacciHeap |
|---|---|---|---|
| 500 (2000) | 1,096±0,015 | 1,667±0,042 | 1,522±0,052 |
| 1000 (4000) | 2,460±0,031 | 3,586±0,041 | 3,023±0,054 |
| 2000 (8000) | 5,338±0,121 | 7,391±0,120 | 6,400±0,081 |
| 4000 (16000) | 11,877±0,382 | 15,249±0,264 | 13,009±0,217 |

Família B — `B_ER_p0.05`:

| n (m) | BinaryHeap | BinomialHeap | FibonacciHeap |
|---|---|---|---|
| 500 (12578) | 2,128±0,025 | 2,734±0,022 | 2,569±0,064 |
| 1000 (50232) | 6,645±0,103 | 7,618±0,057 | 7,189±0,110 |
| 2000 (200325) | 22,678±0,144 | 23,937±0,087 | 23,869±0,321 |
| 4000 (800553) | 79,808±0,130 | 80,632±0,077 | 81,299±0,777 |

Família C — `C_corrente_atl5`:

| n (m) | BinaryHeap | BinomialHeap | FibonacciHeap |
|---|---|---|---|
| 500 (2999) | 1,599±0,024 | 2,084±0,063 | 1,918±0,027 |
| 1000 (5999) | 3,675±0,081 | 4,670±0,088 | 4,146±0,141 |
| 2000 (11999) | 7,671±0,168 | 9,710±0,091 | 8,609±0,264 |
| 4000 (23999) | 16,774±0,107 | 20,845±0,276 | 18,113±0,207 |

Leitura: Binary vence os 12 pontos. MAD relativo 0,10–3,42% (mediana ≈1,5%), logo gaps >5% são robustos. Gap Binary×Binomial em A-4000 ≈28% e em C-4000 ≈24%; em B-4000 comprime para ≈1–2% (Binary 79,808±0,130 vs Binomial 80,632±0,077 vs Fib 81,299±0,777 ms). Fibonacci fica entre os dois em A e C e em B-500/1000/2000 — ex. B-2000 Binary 22,678±0,144 vs Fib 23,869±0,321 vs Binomial 23,937±0,087 ms — e só é o mais lento em B-4000. Escala aprox. linear em A/C ao dobrar `n` e superlinear em B, como esperado de `m≈0,05n²`.

## 4. Discussão

Operações dominantes (variante com push de todos: `n` pushes, `n` pops, até `m` decreases). A é pop-dominada: `m=4n` e pesos homogêneos geram poucos decreases bem-sucedidos; o custo é `pop` com heap de tamanho Θ(`n`). Binary vence por `sift` em vetor com localidade de cache; Fibonacci paga `consolidate` sem ter decreases que compensem; Binomial paga `union/merge` por push.

B é decrease-dominada: cada pop relaxa ≈`pn` vizinhos (até ~200 em n=4000), com alta taxa de sucesso no início — centenas de milhares de decreases por run. É o único regime onde o `decrease O(1)` amortizado do Fibonacci poderia aparecer, e de fato o gap comprime com `n`. Ainda assim Binary vence porque `n≤4000` não atinge o regime assintótico: constantes importam mais que a classe.

C força `pop/consolidate` com heap cheio: a corrente define o ótimo incremental enquanto milhares de atalhos caros nunca vencem cedo; decreases úteis são raros e cortes em cascata quase não disparam. É o pior caso relativo do Fibonacci (muito `consolidate`, pouco `decrease` útil).

Por que o melhor assintótico perde: implementação em Python puro troca ponteiros teóricos por objetos, listas e laços interpretados — constantes altas, sem localidade de array, pressão sobre alocador e GC. `Consolidate` varre root-lists longas com dicionários/listas; `decrease` O(1) economiza pouco quando o resto é caro. Com `n` moderado, o `O(log n)` do binário com fator constante mínimo vence (CLRS; Fredman–Tarjan).

## 5. Limitações e ameaças à validade

Interna: GC padrão sem controle manual; ruído do SO e possível migração de threads (sem `taskset`); apenas 7 repetições (MAD baixo, mas caudas mal estimadas); warmup de 2 rodadas pode não estabilizar o ponto B-4000; validação O(`n+m`) dentro do cronômetro (igual entre heaps, mas infla o absoluto).

Externa: uma máquina, uma seed (2027), tamanhos até 4000 e um `p` em B — sem generalizar para `n≫10⁴`, grafos reais ou pesos contínuos; fonte única `s=0`; pesos inteiros com empates; Python puro — resultados não se transferem para extensões em C. Reprodutibilidade limitada ao `.venv` e protocolo acima; qualquer `--quick` (3 reps, só A) não vale como evidência.

Método de contagem: `wc -w relatorio.md` direto ≤1200.

Referências: Cormen et al. (CLRS) — Dijkstra e heaps binário/binomial/Fibonacci; Fredman–Tarjan (1987) — Fibonacci heaps; Vuillemin (1978) — binomial queues; Dijkstra (1959); docs Python `time.perf_counter` e `statistics.median`.
