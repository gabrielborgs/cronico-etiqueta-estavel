"""
A etiqueta "crônico" é estável? Experimento com dados 100% sintéticos e verdade conhecida.

Cada célula tem um estado REAL fixo: nível médio = meta + m (m < 0: abaixo da meta, de fato crônica; m > 0: acima).
O indicador diário é o nível mais ruído autocorrelacionado (AR(1)). Nada muda no tempo: o estado real é o mesmo em todas as janelas.

Regra testada (a mesma lógica de uma classificação usual de cronicidade, janela de 60 dias):
    crônico = (>= 50% dos dias abaixo da meta)  OU  (>= 14 dias abaixo da meta em sequência)

Perguntas:
  1. Para a mesma célula, com o mesmo estado real, duas janelas seguidas de 60 dias recebem a mesma etiqueta?   (estabilidade)
  2. A etiqueta bate com o estado real?                                                                     (acerto)
  3. Onde estão os erros: no nível "m" (distância até a meta, em desvios do ruído)?
  4. Cada parte da regra (percentual, sequência, a combinação) erra de um jeito diferente?

Uso:  python cronico.py   (imprime as tabelas e grava resultados.csv)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

META = 95.0
SIGMA = 2.0            # desvio do ruído diário (p.p.)
PHI = 0.6              # autocorrelação do ruído de um dia para o outro
JANELA = 60
PCT_MIN = 0.50
SEQ_MIN = 14
N_CELULAS = 4000
SEEDS = range(10)


def simular(rng: np.random.Generator, m: np.ndarray, dias: int, phi: float = PHI) -> np.ndarray:
    """Matriz células x dias: nível real (meta + m) + ruído AR(1) estacionário de desvio SIGMA."""
    n = len(m)
    inov = SIGMA * np.sqrt(1 - phi ** 2)
    e = rng.normal(0, SIGMA, n)                      # começa já no regime estacionário
    saida = np.empty((n, dias))
    for t in range(dias):
        e = phi * e + rng.normal(0, inov, n)
        saida[:, t] = META + m + e
    return saida


def maior_sequencia(fora: np.ndarray) -> np.ndarray:
    """Maior sequência de True por linha."""
    n, d = fora.shape
    atual = np.zeros(n, dtype=int)
    melhor = np.zeros(n, dtype=int)
    for t in range(d):
        atual = np.where(fora[:, t], atual + 1, 0)
        melhor = np.maximum(melhor, atual)
    return melhor


def etiquetas(v: np.ndarray) -> dict:
    # (a janela é o número de colunas de v)
    fora = v < META
    pct = fora.mean(1) >= PCT_MIN
    seq = maior_sequencia(fora) >= SEQ_MIN
    return {"so_percentual": pct, "so_sequencia": seq, "regra_completa": pct | seq}


def rodar(seed: int, phi: float = PHI, janela: int = JANELA) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    m = rng.uniform(-6, 6, N_CELULAS)
    v = simular(rng, m, 2 * janela, phi)
    a, b = etiquetas(v[:, :janela]), etiquetas(v[:, janela:])
    real = m < 0
    linhas = {"seed": seed, "m": m, "m_sigma": m / SIGMA, "real_cronica": real}
    for k in a:
        linhas[f"{k}_A"], linhas[f"{k}_B"] = a[k], b[k]
    return pd.DataFrame(linhas)


def tabela_por_faixa(df: pd.DataFrame, regra: str) -> pd.DataFrame:
    faixas = [-3, -1.5, -0.75, -0.25, 0, 0.25, 0.75, 1.5, 3.01]
    rot = ["-3 a -1,5", "-1,5 a -0,75", "-0,75 a -0,25", "-0,25 a 0", "0 a 0,25", "0,25 a 0,75", "0,75 a 1,5", "1,5 a 3"]
    d = df.copy()
    d["faixa"] = pd.cut(d["m_sigma"], faixas, labels=rot, right=False)
    d["muda"] = d[f"{regra}_A"] != d[f"{regra}_B"]
    d["erra"] = (d[f"{regra}_A"] != d["real_cronica"]).astype(float)
    d["marcada"] = d[f"{regra}_A"].astype(float)
    g = d.groupby("faixa", observed=True).agg(celulas=("muda", "size"), marcada_cronica=("marcada", "mean"), erra_vs_real=("erra", "mean"), muda_de_etiqueta=("muda", "mean"))
    return g


if __name__ == "__main__":
    df = pd.concat([rodar(s) for s in SEEDS], ignore_index=True)
    df.to_csv("resultados.csv", index=False)
    print(f"{len(df)} células-simulação ({N_CELULAS} células x {len(list(SEEDS))} repetições)\n")
    pd.options.display.float_format = lambda x: f"{x:6.1%}"
    for regra in ("regra_completa", "so_percentual", "so_sequencia"):
        print(f"== {regra}: por distância até a meta (m em desvios do ruído; <0 = abaixo da meta) ==")
        print(tabela_por_faixa(df, regra).to_string(), "\n")
    print("== resumo geral ==")
    for regra in ("regra_completa", "so_percentual", "so_sequencia"):
        muda = (df[f"{regra}_A"] != df[f"{regra}_B"]).mean()
        erra = (df[f"{regra}_A"] != df["real_cronica"]).mean()
        print(f"{regra:16s} muda de etiqueta entre janelas: {muda:6.1%} | erra o estado real: {erra:6.1%}")
