"""Gráfico do post: quanto a etiqueta 'crônico' muda entre janelas seguidas, conforme a distância real até a meta.

    python grafico.py   ->  grafico_cronico.png  e  curva.csv
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cronico as C

SURF, INK, INK2, MUTED, LINHA = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8985", "#d9d8d3"
CORES = {0.0: "#9a9994", 0.6: "#2a78d6", 0.9: "#eb6834"}
BORDAS = np.arange(0, 1.76, 0.25)


def curva(phi: float, seeds=range(8)) -> pd.DataFrame:
    df = pd.concat([C.rodar(s, phi, 60) for s in seeds], ignore_index=True)
    df["dist"] = df["m_sigma"].abs()
    df["muda"] = df["regra_completa_A"] != df["regra_completa_B"]
    df["bin"] = pd.cut(df["dist"], BORDAS, right=False)
    g = df.groupby("bin", observed=True)["muda"].agg(["mean", "size"]).reset_index()
    g["centro"] = [b.left + 0.125 for b in g["bin"]]
    g["phi"] = phi
    return g


if __name__ == "__main__":
    dados = pd.concat([curva(p) for p in CORES], ignore_index=True)
    dados[["phi", "centro", "mean", "size"]].to_csv("curva.csv", index=False)
    fig, ax = plt.subplots(figsize=(10.8, 6.6), dpi=100, facecolor=SURF)
    ax.set_facecolor(SURF)
    nomes = {0.0: "φ = 0: dias independentes", 0.6: "φ = 0,6: autocorrelação moderada", 0.9: "φ = 0,9: autocorrelação alta"}
    for phi, cor in CORES.items():
        d = dados[dados.phi == phi]
        ax.plot(d["centro"], d["mean"] * 100, color=cor, lw=2.4, marker="o", ms=7, mec=SURF, mew=1.5, zorder=3)
    # rótulos diretos curtos, colados às linhas (a legenda completa fica acima do gráfico)
    for txt, x, y in (("φ = 0,9", 1.03, 13.8), ("φ = 0,6", 0.48, 16.8), ("φ = 0", 0.02, 20)):
        ax.text(x, y, txt, color=INK, fontsize=12.5, fontweight="bold", va="center")
    from matplotlib.lines import Line2D
    leg = [Line2D([0], [0], color=CORES[p], lw=3, marker="o", ms=7, mec=SURF, label=nomes[p]) for p in (0.0, 0.6, 0.9)]
    fig.legend(handles=leg, loc="upper left", bbox_to_anchor=(0.075, 0.855), ncol=3, frameon=False, fontsize=11.5, labelcolor=INK2, handlelength=1.6, columnspacing=1.6)
    ax.set_xlim(0, 1.75); ax.set_ylim(0, 50)
    ax.set_xlabel("Distância real até a meta (em desvios do ruído diário). 0 = exatamente na meta", color=INK2, fontsize=12.5, labelpad=12)
    ax.set_ylabel("Células que mudam de etiqueta\nentre duas janelas seguidas de 60 dias (%)", color=INK2, fontsize=12.5, labelpad=12)
    ax.set_yticks(range(0, 60, 10)); ax.set_xticks([0, 0.5, 1, 1.5]); ax.set_xticklabels(["0", "0,5", "1", "1,5"])
    ax.tick_params(colors=MUTED, labelsize=12, length=0)
    ax.grid(axis="y", color=LINHA, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(LINHA)
    fig.text(0.075, 0.985, "Perto da meta, a etiqueta “crônico” é cara ou coroa", fontsize=19, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.075, 0.905, "Estado real fixo, nada muda no tempo. 4.000 células × 8 repetições por curva. Dados sintéticos.", fontsize=12.5, color=INK2, ha="left", va="top")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.78, bottom=0.17)
    fig.savefig("grafico_cronico.png", dpi=100, facecolor=SURF)
    print(dados[["phi", "centro", "mean", "size"]].assign(mean=lambda x: (x["mean"] * 100).round(1)).to_string(index=False))
