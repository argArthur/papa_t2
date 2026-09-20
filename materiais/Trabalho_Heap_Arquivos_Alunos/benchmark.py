"""Experimento reproduzível; complete e gere os dados do relatório."""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import sys
import time
from pathlib import Path

SEED = 2027


def medir(func, repeticoes: int = 7) -> tuple[float, float]:
    """Retorne mediana e desvio absoluto mediano, em segundos."""
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        func()
        tempos.append(time.perf_counter() - inicio)
    mediana = statistics.median(tempos)
    mad = statistics.median(abs(t - mediana) for t in tempos)
    return mediana, mad


# ---------------------------------------------------------------------------
# Geradores determinísticos (RNG local; nunca random.seed global).
# Offsets: fam_id em {0:A, 1:B, 2:C}, size_idx em {0..3} sobre NS ordenado.
# ---------------------------------------------------------------------------

NS = (500, 1000, 2000, 4000)
FAMILIAS = ("A_esparsa_d4", "B_ER_p0.05", "C_corrente_atl5")
SOURCE = 0  # fonte fixa s=0 em todas as configurações (pareado entre heaps)

HEAP_NAMES = ("BinaryHeap", "BinomialHeap", "FibonacciHeap")


def _rng(fam_id: int, size_idx: int) -> random.Random:
    return random.Random(SEED + fam_id * 10_000 + size_idx)


def gen_a(n: int, rng: random.Random) -> list[list[tuple[int, int]]]:
    """A — esparsa estrada: cada u recebe exatamente d=4 sucessores distintos.

    Sem laços (v != u), pesos U{1..10}. m exato = 4n. Direcionada.
    """
    d = 4
    g: list[list[tuple[int, int]]] = []
    for u in range(n):
        # Amostra d distintos de [0, n) \\ {u} via índice deslocado.
        sucs = set()
        while len(sucs) < d:
            v = rng.randrange(n - 1)
            if v >= u:
                v += 1
            sucs.add(v)
        g.append([(v, rng.randint(1, 10)) for v in sucs])
    return g


def gen_b(n: int, rng: random.Random, p: float = 0.05) -> list[list[tuple[int, int]]]:
    """B — densa Erdős–Rényi direcionada: cada par ordenado u!=v vira aresta.

    Com prob. p=0.05, pesos U{1..100}. E[m] = n(n-1)p (m efetivo varia).
    """
    g: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    rand = rng.random
    randint = rng.randint
    for u in range(n):
        gu = g[u]
        for v in range(n):
            if v != u and rand() < p:
                gu.append((v, randint(1, 100)))
    return g


def gen_c(n: int, rng: random.Random) -> list[list[tuple[int, int]]]:
    """C — corrente + atalhos: cadeia i->i+1 peso 1 (n-1 arestas).

    Mais 5 atalhos por vértice (v != u, distintos entre si), pesos
    U{100..1000}. m exato = (n-1) + 5n = 6n-1. Direcionada.
    """
    g: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u in range(n):
        if u + 1 < n:
            g[u].append((u + 1, 1))
        atalhos = set()
        while len(atalhos) < 5:
            v = rng.randrange(n - 1)
            if v >= u:
                v += 1
            atalhos.add(v)
        for v in atalhos:
            g[u].append((v, rng.randint(100, 1000)))
    return g


_GENERATORS = (gen_a, gen_b, gen_c)


def _import_heaps_dijkstra():
    """Importa heaps.py / dijkstra.py do mesmo diretório deste arquivo."""
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    from dijkstra import dijkstra  # noqa: E402

    from heaps import BinaryHeap, BinomialHeap, FibonacciHeap  # noqa: E402

    return dijkstra, (BinaryHeap, BinomialHeap, FibonacciHeap)


def _warmup(dijkstra, g, s: int, heap_cls, rodadas: int) -> None:
    for _ in range(rodadas):
        dijkstra(g, s, heap_cls)


def run_experimento(quick: bool = False) -> list[dict]:
    """Executa o protocolo fatorial e retorna as linhas da tabela.

    quick=False: 3 famílias x 4 tamanhos, warmup 2, repeticoes 7.
    quick=True:  fumaça — só família A, n em {500, 1000}, warmup 1, reps 3.
    Construção do grafo sempre FORA de medir(); medição só cronometra
    dijkstra(g, s, Heap) via medir().
    """
    dijkstra, heap_classes = _import_heaps_dijkstra()
    repeticoes = 3 if quick else 7
    warmup = 1 if quick else 2
    fams = [(0, FAMILIAS[0])] if quick else list(enumerate(FAMILIAS))
    nss = ((0, 500), (1, 1000)) if quick else list(enumerate(NS))

    linhas: list[dict] = []
    for fam_id, fam_nome in fams:
        gen = _GENERATORS[fam_id]
        for size_idx, n in nss:
            rng = _rng(fam_id, size_idx)  # RNG local determinístico
            g = gen(n, rng)  # construção SEPARADA da medição
            m = sum(len(adj) for adj in g)
            dists: dict[str, list] = {}
            for heap_nome, heap_cls in zip(HEAP_NAMES, heap_classes):
                _warmup(dijkstra, g, SOURCE, heap_cls, warmup)  # descartado
                mediana_s, mad_s = medir(
                    lambda h=heap_cls: dijkstra(g, SOURCE, h),
                    repeticoes=repeticoes,
                )
                linhas.append(
                    {
                        "familia": fam_nome,
                        "n": n,
                        "m": m,
                        "fonte": SOURCE,
                        "heap": heap_nome,
                        "mediana_s": mediana_s,
                        "mad_s": mad_s,
                        "mediana_ms": mediana_s * 1000.0,
                        "mad_ms": mad_s * 1000.0,
                    }
                )
                # Sanity: guarda distâncias de 1 run extra p/ checar acordo.
                dist, _ = dijkstra(g, SOURCE, heap_cls)
                dists[heap_nome] = dist
            ref = dists[HEAP_NAMES[0]]
            for hn in HEAP_NAMES[1:]:
                if dists[hn] != ref:
                    raise AssertionError(
                        f"divergência de distâncias em {fam_nome} n={n}: "
                        f"{HEAP_NAMES[0]} vs {hn}"
                    )
    return linhas


def _tabela_markdown(linhas: list[dict]) -> str:
    cab = (
        "| familia | n | m | fonte | heap | mediana_s (s) | mad_s (s) | "
        "mediana_ms (ms) | mad_ms (ms) |"
    )
    sep = "|---|---|---|---|---|---|---|---|---|"
    out = [cab, sep]
    for r in linhas:
        out.append(
            f"| {r['familia']} | {r['n']} | {r['m']} | {r['fonte']} | "
            f"{r['heap']} | {r['mediana_s']:.6f} | {r['mad_s']:.6f} | "
            f"{r['mediana_ms']:.3f} | {r['mad_ms']:.3f} |"
        )
    return "\n".join(out) + "\n"


def salvar_csv(linhas: list[dict], caminho: Path) -> None:
    campos = [
        "familia",
        "n",
        "m",
        "fonte",
        "heap",
        "mediana_s",
        "mad_s",
        "mediana_ms",
        "mad_ms",
    ]
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in linhas:
            w.writerow(r)


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark reproduzível (SEED=2027).")
    ap.add_argument("--quick", action="store_true", help="fumaça: fam A, n=500/1000, 3 reps")
    ap.add_argument("--out", default=None, help="caminho do CSV de saída")
    args = ap.parse_args()

    linhas = run_experimento(quick=args.quick)

    base = Path(__file__).resolve().parent
    csv_path = Path(args.out) if args.out else base / "resultados_benchmark.csv"
    md_path = csv_path.with_suffix(".md")
    salvar_csv(linhas, csv_path)
    md_text = (
        "# Resultados benchmark (SEED=2027, fonte s=0)\n\n"
        "Tempos em segundos (mediana_s, 6 casas) e ms derivados; "
        "dispersão = MAD na mesma unidade.\n\n" + _tabela_markdown(linhas)
    )
    md_path.write_text(md_text, encoding="utf-8")

    print(md_text, end="")
    print(f"[benchmark] CSV: {csv_path} | Markdown: {md_path}", flush=True)


if __name__ == "__main__":
    main()
