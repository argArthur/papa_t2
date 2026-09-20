# Workflow — Trabalho Prático: Heaps no Algoritmo de Dijkstra

> Fonte única de verdade: `materiais/Trabalho_Heap_Enunciado.md` (+ `.pdf`).
> Pasta modelo: `materiais/Trabalho_Heap_Arquivos_Alunos/` contendo os 6 arquivos de entrega:
> `autores.json`, `heaps.py`, `dijkstra.py`, `respostas.json`, `benchmark.py`, `relatorio.md`.
> Este workflow é sequencial e incremental. O agente deve executar fase por fase,
> pesquisar antes de implementar, testar após implementar e marcar o checklist ao final.

## Orquestrador — como rodar este workflow (leitura obrigatória antes de qualquer passo)

O workflow é executado por um **orquestrador** que nunca implementa diretamente: ele delega
cada passo a **subagentes com contexto limpo** e só avança quando as dependências e a revisão
estão satisfeitas.

### 1. Regras de execução
1. **Um subagente (ator) com contexto limpo por passo.** Cada item do checklist (exceto F0.1,
   que é referência contínua) roda em um subagente novo, sem histórico de outros passos.
2. **Gate de dependências.** Nunca inicie um passo cujas dependências não estejam `[x]`:
   `F1.1 → F1.2-bin → F1.2-binomial → F1.2-fib → F1.3 → F2.1 → F2.2 → F2.3 → F3.1 → F3.2 → F4.1 → F4.2 → F4.3 → F5.2 → F5.3`.
   Exceção: `F5.1` (dados dos autores) pode rodar em paralelo a qualquer momento, mas exige
   decisão humana (nome/RA) — ver item 4. `F0.2` já está `[x]`; não reexecutar sem motivo.
   (Os três heaps são sequenciais porque compartilham `heaps.py`; nunca paralelizar edições
   no mesmo arquivo.)
3. **Prompt do ator deve ser autocontido.** Todo prompt de ator contém, no mínimo:
   objetivo do passo + DoD, arquivos de entrada/saída (caminhos absolutos), contratos do
   enunciado pertinentes ao passo (copiados, não referenciados por "você sabe"), proibições
   (ex.: não usar `heapq`, não alterar assinaturas, rodar tudo no `.venv`), e formato de
   retorno (arquivos alterados + comandos executados + evidências). Nunca presuma que o
   subagente leu o enunciado — inclua o essencial no prompt.
4. **Ciclo ator → revisor obrigatório.** Após o ator concluir, e antes de marcar `[x]` ou
   iniciar o passo seguinte, o orquestrador dispara um **subagente revisor com contexto limpo**
   (sem histórico do ator), com prompt próprio contendo: trecho do enunciado, ID da revisão
   (`R0.2`…`R5.3` da seção Protocolo), artefatos a inspecionar e a ordem de veredito
   `REVISÃO [ID]: OK/FALHOU` com evidências (`arquivo:linha`/comando).
   - Se o revisor retornar **FALHOU**: o orquestrador reenvia as críticas ao **ator**
     (novo subagente de correção, contexto limpo, prompt com a lista de críticas + artefatos),
     e em seguida roda o revisor novamente. O ciclo repete-se **até o revisor declarar OK**
     (sem mais críticas). É proibido marcar `[x]`, pular a correção ou avançar de passo
     com revisão pendente.
   - Somente com `REVISÃO [ID]: OK` o orquestrador marca o item como `[x]` no checklist.
5. **Comunicação.** A cada passo o orquestrador anuncia ao humano: passo iniciado (ator +
   objetivo), resultado do ator, veredito do revisor (incluindo nº da iteração no ciclo),
   marcação do checklist e próximo passo. **Decisões que o humano deve saber** (interromper
   e perguntar, não arbitrar sozinho): dados de `autores.json` (nomes/RAs exatos);
   escolha `push` de todos os vértices vs. sob demanda no Dijkstra; famílias/tamanhos do
   benchmark (custo de execução); método de contagem de palavras do relatório; qualquer
   desvio do workflow ou troca de categoria em `respostas.json`.
6. **Revisão total ao final.** Após `F5.3` estar `[x]`, disparar um **revisor final com contexto
   limpo** (prompt no modelo abaixo) que audita o trabalho inteiro de ponta a ponta contra o
   enunciado + qualidade geral. Tratar suas críticas como um novo ciclo ator → revisor até
   `REVISÃO FINAL: OK`. Só então declarar o trabalho concluído.

### Modelos de prompt
- **Ator (adaptar por passo):** `Você é o ator do passo [ID: descrição]. Contexto: [contratos do enunciado pertinentes, caminhos absolutos]. Tarefa: [ações + DoD do passo]. Proibições: [ex.: sem heapq, sem mudar assinaturas, só .venv]. Retorne: [arquivos alterados, diff resumido, comandos + saídas]. Não marque checklists; apenas entregue o passo.`
- **Revisor (adaptar por passo):** `Você é o revisor independente do passo [ID]. Você NÃO participou da implementação. Base: [trecho do enunciado + ID da revisão Rxx deste workflow]. Inspecione por leitura direta: [artefatos]. Seja diligente e exigente (contratos + qualidade geral). Veredito obrigatório: 'REVISÃO [ID]: OK — <evidências>' ou 'REVISÃO [ID]: FALHOU — <lista numerada de problemas com evidência arquivo:linha/comando> — correção exigida'. Não corrija o código; apenas julgue.`
- **Revisor final:** `Você é o auditor final. Base: materiais/Trabalho_Heap_Enunciado.md integral + 6 arquivos de entrega + checklist. Verifique: (1) contratos dos 3 heaps e grep heapq limpo; (2) Dijkstra único/genérico + ValueError/inf-None; (3) respostas.json nas categorias permitidas e coerente; (4) benchmark 3 famílias×4 tamanhos pareado + relatório ≤1200 palavras com os 5 itens; (5) autores.json + zip com 6 arquivos na raiz. Veredito: 'REVISÃO FINAL: OK — <evidências>' ou 'REVISÃO FINAL: FALHOU — <críticas com evidência>'.`

---

## Fase 0 — Leitura integral + setup de ambiente (pré-requisito de todas as partes)

### 0.1 Ler todas as instruções
1. Ler `materiais/Trabalho_Heap_Enunciado.md` na íntegra (linhas 1–98).
2. Inspecionar os 6 arquivos modelo em `materiais/Trabalho_Heap_Arquivos_Alunos/` sem alterar assinaturas/nomes.
3. Extrair contratos rígidos (não negociáveis):
   - **Premissas:** Python ≥3.11; grafos direcionados em lista de adjacência `graph[u] = [(v,w), ...]`; vértices `0..n-1`; pesos reais finitos `>= 0`; `n=|V|`, `m=|E|`; peso negativo → `ValueError`; inalcançável → `dist=math.inf`, `pred=None`.
   - **Parte 1 (`heaps.py`):** classes `BinaryHeap`, `BinomialHeap`, `FibonacciHeap` com interface `push(vertex, priority)->handle`, `decrease_key(handle, new_priority)->None`, `pop_min()->tuple[vertex,priority]`, `__len__()->int`. `push` retorna handle opaco. Prioridades só diminuem — aumento → `ValueError`. `pop_min` em vazio → `IndexError`. Proibido `heapq` ou outra PQ pronta nas 3 classes; auxiliares comuns (`list`, `dict`) permitidos.
   - **Parte 2 (`dijkstra.py`):** `dijkstra(graph, source, heap_class) -> tuple[dist, pred]`; instanciar `heap_class` e usar **exclusivamente** interface pública; **não duplicar** o algoritmo por heap; empate → qualquer árvore de caminhos mínimos válida.
   - **Parte 3 (`respostas.json`):** usar **somente** categorias `["1", "log_n", "n", "m_mais_n_log_n", "m_mais_n_vezes_log_n"]`; pior caso para binário/binomial, amortizado para Fibonacci (tabela usual); informar complexidade do Dijkstra com adjacência + `decrease_key`, sem supor grafo conexo.
   - **Parte 4 (`benchmark.py` + `relatorio.md`):** comparar 3 heaps em ≥3 famílias × ≥4 tamanhos por família; mesmas instâncias e fontes; aquecimento + repetições + dispersão; relatório ≤1200 palavras cobrindo os 5 itens obrigatórios (máquina/Python/gerador/semente/protocolo; tabelas/gráficos com unidades e dispersão; operações dominantes por família; por que melhor assintótico ≠ menor tempo nos tamanhos testados; limitações/ameaças).
   - **Entrega:** 6 arquivos na raiz do `.zip`, sem pastas; nome `Trabalho_Heap_RA.zip` (RA do 1º autor); `autores.json` com 1–3 autores, nome+RA exatos, RA como string (preservar zeros à esquerda), sem RA repetido; código autoral + referências.
   - **Avaliação:** heaps 3,0 + Dijkstra 2,5 + assintótica 2,5 + experimento 2,0. Primeiros 8,0 via corretor automático.

### 0.2 Criar venv e documentar versões
```bash
# na raiz do projeto (/home/arthur/projects/papa_t2)
python3 --version            # exigir >= 3.11
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip freeze > versions_pip.txt
python --version > versions_env.txt
python -c "import platform; print(platform.platform()); print(platform.processor())" >> versions_env.txt
```
1. Todo código e benchmark **devem** rodar dentro de `.venv`.
2. Documentar em `versions_env.txt`: versão Python, SO/CPU (para o relatório), `pip freeze`.
3. Registrar os mesmos dados no relatório (máquina + Python).
4. DoD Fase 0: `ls` mostra `.venv/`; `versions_env.txt` existe; agente confirma leitura dos 7 arquivos (enunciado + 6 modelos).

---

## Fase 1 — Parte 1: Filas de Prioridade (3,0 pts) — `heaps.py`

### 1.1 Pesquisa — melhores padrões e estado da arte (fazer ANTES de codar)
- **Binário:** CLRS cap. 6 (array-based, `sift-up`/`sift-down`, mapa handle→índice para `decrease_key` O(log n)). Padrão: handle = objeto mutável com índice (`list` de 1 slot ou classe `_Handle` com `index`), nunca o índice bruto. Pesquisar armadilhas: invalidação de handle após `pop_min`, `decrease_key` em handle já removido (definir política + teste).
- **Binomial:** CLRS cap. 19 / Vuillemin (1978). Padrão: floresta de árvores binomiais com `degree`, `parent/child/sibling` ou `children:list`; `merge` de raízes de mesmo grau; `push` = merge de singleton O(log n) pior caso; `decrease_key` = borbulhar até raiz O(log n); `pop_min` = remove raiz mínima e faz merge dos filhos reversos O(log n). Handle = ponteiro para nó.
- **Fibonacci:** Fredman–Tarjan (1987), CLRS cap. 20. Padrão: lista circular duplamente ligada de raízes + `min`, `mark`, `degree`; `push` O(1) amortizado; `decrease_key` O(1) amortizado com corte + corte em cascata; `pop_min` O(log n) amortizado com `consolidate` (array por grau + `link`). Handle = ponteiro para nó. Pesquisar simplificações seguras em Python: lista Python para root-list é aceitável se `consolidate` continuar correta; cuidado com recursão e com `__len__` O(1) via contador.
- Registrar referências (CLRS ed./cap., artigos) para citar no código/relatório — código deve ser autoral.

### 1.2 Implementação (contratos primeiro)
1. Implementar `BinaryHeap` → `BinomialHeap` → `FibonacciHeap`, nessa ordem (dificuldade crescente, permite reuso de testes).
2. Regras por método (todas as 3 classes): `push` retorna handle opaco; `decrease_key(handle, new)` valida handle e lança `ValueError` se `new > atual`; `pop_min` vazio → `IndexError`; `__len__` O(1) via contador interno; **nenhum `import heapq`** em `heaps.py` (verificar com `grep -rn heapq`).
3. Estilo: tipagem, docstrings com complexidade por método, sem alterar nomes/assinaturas do modelo.

### 1.3 Testes — Parte 1 (obrigatórios antes de avançar)
- Criar `tests/test_heaps_contract.py` (não entra no zip): para cada classe, testar `push/pop` ordenado, `decrease_key` válido, `ValueError` em aumento, `IndexError` em `pop_min` vazio, `len` correto, handles opacos reutilizáveis, `pop` até esvaziar.
- Teste aleatório/diferencial: N pushes aleatórios + decreases aleatórios válidos, comparar sequência de `pop_min` com `sorted` de referência.
- Teste de handles: `decrease_key` após `pop` deve falhar de forma definida (documentar escolha).
- Comando: `source .venv/bin/activate && python -m pytest tests/test_heaps_contract.py -v` (ou `unittest` se pytest indisponível — registrar no `versions_env.txt`).
- DoD Fase 1: 100% dos testes de contrato passam nas 3 classes; `grep heapq heaps.py` vazio.

---

## Fase 2 — Parte 2: Dijkstra (2,5 pts) — `dijkstra.py`

### 2.1 Pesquisa — melhores padrões e estado da arte
- Dijkstra (1959) + variante com `decrease_key` vs. variante lazy com entradas obsoletas (aqui **exigida** a com `decrease_key` + handles). Padrão: `dist=[inf]*n`, `pred=[None]*n`, `dist[source]=0`; `push` de todos os vértices (ou push sob demanda — decidir e justificar; push de todos simplifica e casa com análise `n` inserts); loop `pop_min` + relaxamento; `decrease_key` quando `nd < dist[v]`; marcar visitado/fechado para ignorar re-extrações se push sob demanda.
- Casos-limite: validar `source` fora de `[0,n-1]`, grafo vazio (`n=0`), fonte isolada, pesos zero, arestas paralelas, self-loops, peso negativo em qualquer aresta → `ValueError` **antes/durante** (varrer arestas no início é o mais simples e determinístico), `math.inf`/`None` para inalcançáveis, tipos `float/int`.
- Estado da arte da análise: com binary/binomial heap `O((m+n) log n)`; com Fibonacci `O(m + n log n)` — antecipa Fase 3.

### 2.2 Implementação
1. Função única `dijkstra(graph, source, heap_class)`, genérica em `heap_class` (sem `if heap_class == ...`, sem duplicar algoritmo).
2. Usar **somente** `push/decrease_key/pop_min/__len__`; não acessar internals do heap.
3. Validações: pesos negativos (incl. `-0.0`? não — `-0.0 == 0`, aceitar), vértice fonte inválido, estrutura `graph` como `Sequence`.
4. Retornar `(dist, pred)` como listas de tamanho `n`.

### 2.3 Testes — Parte 2
- Criar `tests/test_dijkstra.py`: para cada heap_class — grafo pequeno com resposta manual; grafo desconexo (`inf`/`None`); peso zero; empates (validar que é árvore de caminhos mínimos re-calculando custo, não igualdade exata de `pred`); fonte única/isolada; `ValueError` em peso negativo; `ValueError`/exceção em fonte inválida; invariante `len(heap)==0` ao fim.
- Diferencial aleatório: gerar ~200 grafos aleatórios (n≤12) e comparar as 3 heaps + referência ingênua O(n²) sem heap (implementada só no teste).
- Comando: `python -m pytest tests/test_dijkstra.py -v`.
- DoD Fase 2: todos os testes passam com as 3 heaps; corretor manual simulado (contratos) OK.

---

## Fase 3 — Parte 3: Análise Assintótica (2,5 pts) — `respostas.json`

### 3.1 Pesquisa — tabela comparativa canônica
- Revisar CLRS: binário — `inserir O(log n)`, `diminuir_chave O(log n)`, `extrair_minimo O(log n)` (pior caso); binomial — idem `O(log n)` pior caso; Fibonacci — `inserir O(1)`, `diminuir_chave O(1)`, `extrair_minimo O(log n)` (amortizados).
- Derivar Dijkstra com adjacência + `decrease_key`: `n` inserts + `n` extract-min + até `m` decrease-keys. Sem supor conexidade (vale para esparso e denso). Mapear para categorias permitidas **exatas**: `"1"`, `"log_n"`, `"n"`, `"m_mais_n_log_n"`, `"m_mais_n_vezes_log_n"`. Preencher os 3 campos `dijkstra` (um por heap) — binário/binomial → `(m+n) log n`; Fibonacci → `m + n log n`.

### 3.2 Preenchimento + validação
1. Editar só os valores `"PREENCHER"` em `respostas.json`; nunca renomear chaves nem `categorias_permitidas`.
2. Validar: `python -c "import json; d=json.load(open('materiais/Trabalho_Heap_Arquivos_Alunos/respostas.json')); assert set(d['categorias_permitidas'])=={'1','log_n','n','m_mais_n_log_n','m_mais_n_vezes_log_n'}; ..."` + checar que nenhum valor restante é `"PREENCHER"`.
3. DoD Fase 3: JSON válido, 12 campos preenchidos só com categorias permitidas, coerentes com a pesquisa.

---

## Fase 4 — Parte 4: Experimento e Discussão (2,0 pts) — `benchmark.py` + `relatorio.md`

### 4.1 Pesquisa — desenho experimental estado da arte
- Padrões: mesma seed (`SEED=2027` já dada) + mesmas instâncias/fontes entre heaps (pareado); aquecimento (warmup) antes de cronometrar; `time.perf_counter()`; repetições (usar `medir()` dada: mediana + MAD) com ≥7 repetições; reportar unidades (s/ms) e dispersão; separar construção do grafo da medição do Dijkstra.
- Famílias que exercitam operações dominantes distintas (escolher ≥3, ex.: (a) esparso tipo estrada/grade — poucos `decrease_key`; (b) denso Erdős–Rényi `p` alto — muitos `decrease_key`/relaxamentos; (c) pesos com forte hierarquia / grafos com muitos empates ou correntes que forçam `pop_min`/`consolidate`). ≥4 tamanhos por família em escala geométrica (ex.: n = 500, 1000, 2000, 4000) mantendo `m` documentado.
- Estado da arte da discussão: Fibonacci tem melhor amortizado mas constantes altas + overhead Python (objetos, listas, GC) → binário costuma vencer em n moderado; binomial raramente vence em Python puro; `consolidate` O(log n) com constantes altas; cache-localidade do array do binário.

### 4.2 Implementação do `benchmark.py`
1. Completar `main()`: gerar famílias (funções determinísticas com `random.Random(SEED)` local, não global), fixar fonte por instância, warmup (1–2 rodadas descartadas), laço `medir(lambda: dijkstra(g, s, Heap))` por heap, imprimir/salvar tabela (CSV/Markdown) com `n, m, heap, mediana_s, mad_s`.
2. Não invalidar `medir()`/`SEED`; permitir `--quick` para fumaça e modo completo para o relatório.
3. Rodar dentro do `.venv` em máquina única, sem carga concorrente; registrar tudo.

### 4.3 `relatorio.md` (≤1200 palavras, 5 seções obrigatórias)
1. Ambiente e protocolo (máquina, CPU/RAM/SO, `python --version`, gerador, semente, aquecimento, repetições, `medir` mediana+MAD).
2. Famílias de grafos (≥3 × ≥4 tamanhos, com `n`/`m` por ponto).
3. Resultados (tabelas/gráficos com unidades + dispersão).
4. Discussão (operações dominantes por família; por que assintótico melhor pode perder em n testado — constantes, Python puro, localidade).
5. Limitações e ameaças (validade interna/externa: GC, ruído, uma máquina, uma seed, tamanhos limitados).
- Contar palavras: `wc -w relatorio.md` (excluir marcação se necessário — documentar método de contagem).
- DoD Fase 4: `benchmark.py` roda de ponta a ponta; relatório ≤1200 palavras com os 5 itens verificáveis.

---

## Fase 5 — Entrega (0 pts diretos, elimina erros formais)

1. Preencher `autores.json` (nome exato + RA string com zeros à esquerda); validar: 1–3 autores, sem RA repetido/vazio.
2. Auditoria final: nomes/assinaturas intactos; sem `heapq` em `heaps.py`; `wc -w relatorio.md`; JSONs válidos; testes verdes.
3. Montar zip: copiar os 6 arquivos para staging plano e zipar sem pastas:
```bash
mkdir -p /tmp/staging && cp materiais/Trabalho_Heap_Arquivos_Alunos/{autores.json,heaps.py,dijkstra.py,respostas.json,benchmark.py,relatorio.md} /tmp/staging/
python -c "import zipfile,pathlib; [print(p.name) for p in pathlib.Path('/tmp/staging').iterdir()]"
# nome com RA do 1º autor:
RA=XXXXXXXX; python - <<PY
import zipfile, pathlib
ra="$RA"
files=["autores.json","heaps.py","dijkstra.py","respostas.json","benchmark.py","relatorio.md"]
with zipfile.ZipFile(f"Trabalho_Heap_{ra}.zip","w",zipfile.ZIP_DEFLATED) as z:
    for f in files: z.write(f"/tmp/staging/{f}", arcname=f)
PY
unzip -l Trabalho_Heap_$RA.zip
```
4. DoD Fase 5: `unzip -l` lista exatamente os 6 arquivos na raiz.

---

## Protocolo de revisão diligente (obrigatório para todos os passos, exceto F0.1)

> Regra dura: nenhum item do checklist (exceto F0.1) pode ser marcado `[x]` sem antes
> executar a revisão correspondente abaixo. Seja diligente e exigente: releia o trecho
> do enunciado, reinspecione o artefato, confira qualidade geral. Havendo qualquer
> problema, NÃO marque `[x]` — retorne as críticas no formato:
> `REVISÃO [ID]: FALHOU — <lista numerada de problemas com evidência arquivo:linha/comando> — correção exigida antes de avançar`.
> Só marque `[x]` com `REVISÃO [ID]: OK — <evidências verificadas>`.

### R0.2 — Revisão do venv e versões
- Reում contra enunciado (Premissas: Python ≥3.11) e Fase 0.2: `.venv/` existe e `.venv/bin/python --version` ≥3.11?
- `versions_env.txt` contém Python, SO/CPU/RAM e `versions_pip.txt` existe? Todo o trabalho rodou no `.venv` (`sys.prefix` confere)?
- Qualidade: sem venv commitado no zip; adaptação `--without-pip` documentada se aplicável.
- Exigência: rode `ls -la`, `.venv/bin/python --version` e `cat versions_env.txt`; critique versão divergente, arquivo ausente ou uso do Python do sistema.

### R1.1 — Revisão da pesquisa de heaps
- Contra Parte 1 + §Entrega (código autoral + referências): há registro escrito das decisões (handle opaco, `sift-up/down`, merge binomial, corte/cascata + `consolidate` Fibonacci) com fontes (CLRS caps, Fredman–Tarjan, Vuillemin)?
- Qualidade: pesquisa distingue pior caso vs. amortizado? Prevê armadilhas (handle após `pop`, `decrease_key` inválido)? Sem copiar código externo?
- Critique: afirmação assintótica errada, fonte ausente, padrão que viola a interface exigida.

### R1.2-bin — Revisão BinaryHeap
- Contra Parte 1 (linhas 27–38): métodos exatos `push/decrease_key/pop_min/__len__`, handle opaco aceito por `decrease_key`, `ValueError` em aumento, `IndexError` em vazio, zero `heapq`/PQ pronta (`grep -rn heapq` limpo)?
- Qualidade: `decrease_key` O(log n) via mapa handle→índice (não busca linear); `__len__` O(1); handle inválido/removido tratado de forma definida e testada; tipagem + docstring com complexidade; nomes/assinaturas do modelo intactos.
- Critique qualquer desvio de contrato, O(n) escondido, handle = índice bruto, exceção errada ou `heapq` importado.

### R1.2-binomial — Revisão BinomialHeap
- Contra os mesmos contratos da Parte 1: interface, erros, sem `heapq`.
- Qualidade: invariante de floresta (graus únicos), `merge` correto, `push`/`decrease_key`/`pop_min` O(log n) pior caso, `__len__` O(1), sem vazamento de nós, sem recursão estourável.
- Critique: merge que quebra unicidade de graus, filhos não reversos no `pop_min`, `decrease_key` sem borbulhar até raiz, contador de tamanho incorreto.

### R1.2-fib — Revisão FibonacciHeap
- Contra os mesmos contratos da Parte 1.
- Qualidade: `push`/`decrease_key` O(1) amortizado com corte + cascata + `mark` corretos; `pop_min` com `consolidate` por grau; `min` mantido; `__len__` O(1); sem atalhos que quebrem amortização (ex.: `pop_min` O(n) sem consolidate).
- Critique: cascata ausente/errada, `mark` nunca limpo, `consolidate` com array subdimensionado, `min` obsoleto.

### R1.3 — Revisão dos testes de heaps
- Contra Parte 1 + Critérios (3,0 pts, corretor automático): `tests/test_heaps_contract.py` cobre para as 3 classes — ordem de `pop`, `decrease_key` válido, `ValueError`, `IndexError`, `len`, esvaziamento total, handles pós-`pop`, diferencial aleatório vs `sorted`?
- Qualidade: testes isolados, determinísticos (seed), comando `pytest` documentado e verde; teste falha de propósito se o contrato for quebrado (validar mutando código)?
- Critique: cobertura faltante, teste que só passa para 1 heap, aleatoriedade sem seed, teste verde por asserção fraca.

### R2.1 — Revisão da pesquisa de Dijkstra
- Contra Parte 2 (linhas 42–48) + Premissas: variante com `decrease_key` + handles (não lazy), decisão `push` de todos vs. sob demanda justificada, casos-limite mapeados (fonte inválida, `n=0`, isolada, peso zero, paralelas, self-loop, negativo→`ValueError`, `inf`/`None`)?
- Qualidade: análise antecipada O((m+n) log n) vs O(m + n log n) correta e sem supor conexidade.
- Critique: proposta lazy com duplicatas, validação de negativo ausente, fonte inválida sem erro definido.

### R2.2 — Revisão da implementação de Dijkstra
- Contra Parte 2: função única genérica em `heap_class`, sem `if heap_class == ...`, sem duplicação, usa **exclusivamente** a interface pública (auditar: nenhum acesso a atributo interno do heap)?
- Contra Premissas: varre todas as arestas e lança `ValueError` em peso negativo; `dist`/`pred` tamanho `n` com `inf`/`None` para inalcançáveis; empate aceita qualquer árvore válida (não força `pred` específico)?
- Qualidade: legível, tipado, sem O(n²) acidental, trata `-0.0` como 0, valida `source`.
- Critique linha a linha qualquer uso de internals, ramificação por heap, `ValueError` faltante ou retorno com tamanho errado.

### R2.3 — Revisão dos testes de Dijkstra
- Contra Parte 2 + Critérios (2,5 pts): `tests/test_dijkstra.py` testa nas 3 heaps — resposta manual, desconexo, peso zero, empates (valida custo, não `pred` exato), isolada, negativo→`ValueError`, fonte inválida, heap vazio ao fim + diferencial ~200 grafos vs referência O(n²)?
- Qualidade: testes determinísticos, mesma instância para as 3 heaps, falhas reais detectadas.
- Critique: teste que compara `pred` exato em empate, referência ausente, cobertura de erro faltante.

### R3.1 — Revisão da tabela assintótica (pesquisa)
- Contra Parte 3 (linhas 52–54): pior caso binário/binomial, amortizado Fibonacci, tabela usual, Dijkstra com adjacência + `decrease_key` sem supor conexidade?
- Qualidade: derivação `n` inserts + `n` extract-min + ≤`m` decreases explícita; mapeamento exato para as 5 categorias permitidas.
- Critique: confundir pior caso com amortizado, supor grafo conexo (`m ≥ n-1`), categoria inventada.

### R3.2 — Revisão do respostas.json
- Contra modelo: JSON válido, só valores das categorias permitidas, nenhum `"PREENCHER"` restante, chaves/`categorias_permitidas` intactas, 12 campos coerentes com R3.1?
- Qualidade: validação por comando (`json.load` + asserts) executada e verde.
- Critique: valor fora do vocabulário, chave renomeada, Dijkstra de Fibonacci igual ao binário sem justificativa.

### R4.1 — Revisão do desenho experimental
- Contra Parte 4 + Observações: ≥3 famílias × ≥4 tamanhos documentados com `n`/`m`, mesmas instâncias/fontes entre heaps, seed registrada (2027), warmup, repetições via `medir` (mediana+MAD), construção separada da medição, famílias que estressam operações dominantes distintas?
- Qualidade: tamanhos em escala que diferenciam heaps sem inviabilizar tempo; protocolo reproduzível por terceiros.
- Critique: famílias indistinguíveis, tamanhos insuficientes, comparação não pareada, seed/warmup/dispersão ausentes.

### R4.2 — Revisão do benchmark.py
- Contra Parte 4 e R4.1: `main()` implementado sem quebrar `medir`/`SEED`, geradores determinísticos (`Random(SEED)` local), fonte fixa, warmup descartado, tabela com unidades + dispersão, roda de ponta a ponta no `.venv` em máquina única?
- Qualidade: `--quick` para fumaça + modo completo; sem medir construção do grafo junto; sem carga concorrente; saída salva (CSV/Markdown) para o relatório.
- Critique: `random.seed` global em vez de local, warmup ausente, tempos sem unidade/MAD, `SEED` alterado, `medir` modificado.

### R4.3 — Revisão do relatorio.md
- Contra Parte 4 (5 itens obrigatórios + ≤1200 palavras): (1) máquina/Python/gerador/seed/protocolo, (2) tabelas/gráficos com unidades + dispersão, (3) operações dominantes por família, (4) por que melhor assintótico pode perder, (5) limitações/ameaças — todos presentes e verificáveis? `wc -w` ≤1200 (método de contagem documentado)?
- Qualidade: números do relatório batem com a saída real do benchmark; unidades consistentes; português claro; referências citadas; sem afirmação sem evidência.
- Critique: item faltante, palavra excedente, tabela sem dispersão/unidade, conclusão contradita pelos dados, número inventado.

### R5.1 — Revisão do autores.json
- Contra §Entrega: 1–3 autores, nome completo + RA exatos como no sistema, RA como string com zeros à esquerda, sem nome/RA vazio, sem RA repetido, sem 4º integrante?
- Qualidade: JSON válido, validado por comando.
- Critique qualquer RA numérico (perde zero), duplicata, campo renomeado.

### R5.2 — Revisão da auditoria final
- Contra tudo: assinaturas/nomes dos 6 arquivos intactos; `grep heapq` limpo em `heaps.py`; JSONs válidos; testes verdes; `wc -w relatorio.md` OK; código legível/autoral com referências?
- Qualidade: auditoria executada de verdade (colar comandos + saídas), não "de cabeça".
- Critique: qualquer verificação pulada ou com saída não inspecionada.

### R5.3 — Revisão do zip de entrega
- Contra §Entrega: `Trabalho_Heap_RA.zip` (RA do 1º autor), exatamente os 6 arquivos na raiz, sem pastas, nomes exatos (`unzip -l` confere)?
- Qualidade: zip remontado a partir de staging plano, testado por extração em diretório limpo + re-execução de um teste.
- Critique: pasta intermediária dentro do zip, arquivo faltante/extra, nome com RA errado, `tests/` ou `.venv` dentro do zip.

---

## Referências a registrar no código/relatório
- Cormen et al. (CLRS) — heaps binário/binomial/Fibonacci + Dijkstra.
- Fredman & Tarjan (1987) — Fibonacci heaps.
- Vuillemin (1978) — binomial queues.
- Dijkstra (1959).
- Documentação Python (`time.perf_counter`, `statistics.median`).

---

## Checklist incremental (marcar `[x]` somente após `REVISÃO [ID]: OK`; F0.1 é o único item sem revisão — manter desmarcado até releitura final)

```text
[x] F0.1 Li enunciado integral + 6 arquivos modelo e anotei contratos rígidos
[x] F0.2 .venv criado (Python >=3.11) e versions_env.txt/versions_pip.txt gerados
[x] F1.1 Pesquisa heaps (binário/binomial/Fibonacci + handles) registrada
[x] F1.2 BinaryHeap implementado (push/decrease_key/pop_min/len + erros)
[x] F1.2 BinomialHeap implementado (idem)
[x] F1.2 FibonacciHeap implementado (idem, sem heapq — grep limpo)
[x] F1.3 tests/test_heaps_contract.py verde nas 3 classes
[x] F2.1 Pesquisa Dijkstra (decrease_key vs lazy + casos-limite) registrada
[x] F2.2 dijkstra() único e genérico, só interface pública, validações OK
[x] F2.3 tests/test_dijkstra.py verde (manual + desconexo + negativo + diferencial aleatório)
[x] F3.1 Tabela assintótica canônica revisada (pior caso vs amortizado)
[x] F3.2 respostas.json válido, 12 campos só com categorias permitidas
[x] F4.1 Desenho experimental definido (3 famílias x 4 tamanhos, pareado, warmup, medir mediana+MAD)
[x] F4.2 benchmark.py completo e executado no .venv (tabela com unidades+dispersão)
[x] F4.3 relatorio.md ≤1200 palavras com os 5 itens obrigatórios
[x] F5.1 autores.json válido (1-3 autores, RA string, sem duplicata)
[x] F5.2 Auditoria final OK (assinaturas, sem heapq, JSONs válidos, testes verdes, wc -w)
[x] F5.3 Trabalho_Heap_RA.zip com exatamente os 6 arquivos na raiz (unzip -l)
```
