"""
Sensibilidade: o quanto a "faixa de dúvida" em torno da meta depende da autocorrelação e da janela,
e se uma banda de indecisão resolve. Dados 100% sintéticos (ver cronico.py).

Faixa de dúvida = células cujo estado real está a menos de X desvios da meta e que mudam de etiqueta entre
janelas seguidas em mais de 10% dos casos. Reportamos a maior distância |m|/sigma com troca > 10%.

Uso:  python sensibilidade.py   (imprime as tabelas e grava sensibilidade.csv)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cronico as C

SEEDS = range(6)
BANDA = (0.35, 0.65)      # fração de dias fora: abaixo = "ok", acima = "crônico", no meio = "indeterminado"


def largura_da_duvida(df: pd.DataFrame, col: str = "so_percentual") -> float:
    """Maior |m|/sigma em que a etiqueta ainda muda entre janelas em mais de 10% dos casos (bins de 0,1)."""
    d = df.assign(muda=df[f"{col}_A"] != df[f"{col}_B"], dist=df["m_sigma"].abs())
    d["bin"] = (d["dist"] // 0.1) * 0.1
    g = d.groupby("bin")["muda"].mean()
    ruins = g[g > 0.10]
    return float(ruins.index.max() + 0.1) if len(ruins) else 0.0


def com_banda(seed: int, phi: float, janela: int):
    """Mesma simulação, mas com a regra de 3 estados sobre a fração de dias fora."""
    rng = np.random.default_rng(seed)
    m = rng.uniform(-6, 6, C.N_CELULAS)
    v = C.simular(rng, m, 2 * janela, phi)
    def cls(x):
        f = (x < C.META).mean(1)
        return np.where(f >= BANDA[1], "cronico", np.where(f <= BANDA[0], "ok", "indeterminado"))
    return m, cls(v[:, :janela]), cls(v[:, janela:])


if __name__ == "__main__":
    linhas = []
    for phi in (0.0, 0.6, 0.9):
        for janela in (30, 60, 120):
            df = pd.concat([C.rodar(s, phi, janela) for s in SEEDS], ignore_index=True)
            comp = (df["regra_completa_A"] != df["so_percentual_A"]).mean()
            larg = largura_da_duvida(df)
            # banda de indecisão
            ms, as_, bs = [], [], []
            for s in SEEDS:
                m, a, b = com_banda(s, phi, janela); ms.append(m); as_.append(a); bs.append(b)
            m, a, b = np.concatenate(ms), np.concatenate(as_), np.concatenate(bs)
            definido = (a != "indeterminado") & (b != "indeterminado")
            troca_def = (a[definido] != b[definido]).mean()
            erra_def = ((a[definido] == "cronico") != (m[definido] < 0)).mean()
            troca_bin = (df["so_percentual_A"] != df["so_percentual_B"]).mean()
            linhas.append(dict(phi=phi, janela=janela, largura_duvida_sigma=larg, completa_vs_percentual=comp,
                               troca_binaria=troca_bin, indeterminadas=(a == "indeterminado").mean(), troca_entre_definidas=troca_def, erra_entre_definidas=erra_def))
    r = pd.DataFrame(linhas)
    r.to_csv("sensibilidade.csv", index=False)
    pd.options.display.float_format = lambda x: f"{x:7.3f}"
    print(r.to_string(index=False))
